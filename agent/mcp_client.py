from typing import Optional, Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult, TextContent, Resource, Prompt


class MCPClient:
    """Handles MCP server connection and tool execution via stdio"""

    def __init__(self, docker_image: str) -> None:
        self.docker_image = docker_image
        self.session: Optional[ClientSession] = None
        self._stdio_context = None
        self._session_context = None
        self._process = None

    async def __aenter__(self):
        # 1. Create StdioServerParameters with:
        #       - command="docker"
        #       - args=["run", "--rm", "-i", self.docker_image]
        server_params = StdioServerParameters(
            command="docker",
            args=["run", "--rm", "-i", self.docker_image]
        )
        
        # 2. Init `_stdio_context` with `stdio_client(server_params)`
        self._stdio_context = stdio_client(server_params)
        
        # 3. Create `read_stream, write_stream` with `await self._stdio_context.__aenter__()`
        read_stream, write_stream = await self._stdio_context.__aenter__()
        
        # 4. Create ClientSession with `read_stream, write_stream` and assign to the `_session_context`
        self._session_context = ClientSession(read_stream, write_stream)
        
        # 5. Init `session` with `await self._session_context.__aenter__()`
        self.session = await self._session_context.__aenter__()
        
        # 6. Call `self.session.initialize()`, and print its result (to check capabilities of MCP server later)
        print("Initializing MCP session...")
        init_result = await self.session.initialize()
        print(f"Capabilities: {init_result.model_dump_json(indent=2)}")

        # 7. return self
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # This is shutdown method.
        # If session is present and session context is present as well then shutdown the session context (__aexit__ method with params)
        if self.session and self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        
        # If stdio context is present then shutdown the stdio context (__aexit__ method with params)
        if self._stdio_context:
            await self._stdio_context.__aexit__(exc_type, exc_val, exc_tb)

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        # 1. Call `await self.session.list_tools()` and assign to `tools`
        tools = await self.session.list_tools()
        
        # 2. Return list with dicts:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in tools.tools
        ]

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        print(f"    🔧 Calling `{tool_name}` with {tool_args}")
        
        # 1. Call `await self.session.call_tool(tool_name, tool_args)` and assign to `tool_result: CallToolResult` variable
        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)
        
        # 2. Get `content` with index `0` from `tool_result` and assign to `content` variable
        content = tool_result.content[0]
        
        # 3. print(f"    ⚙️: {content}\n")
        print(f"    ⚙️: {content}\n")
        
        # 4. If `isinstance(content, TextContent)` -> return content.text
        #    else -> return content
        if isinstance(content, TextContent):
            return content.text
        else:
            return content

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        try:
            resources = await self.session.list_resources()
            return resources.resources
        except Exception as e:
            print(f"Error getting resources: {e}")
            return []

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        try:
            prompts = await self.session.list_prompts()
            return prompts.prompts
        except Exception as e:
            print(f"Error getting prompts: {e}")
            return []

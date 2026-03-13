import asyncio
import json
import os

from agent.mcp_client import MCPClient
from agent.dial_client import DialClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT

async def main():
    # 1. Create MCP client with `docker_image="mcp/duckduckgo:latest"` as `mcp_client`
    async with MCPClient(docker_image="mcp/duckduckgo:latest") as mcp_client:
        # 2. Get Available MCP Tools, assign to `tools` variable, print tool as well
        tools = await mcp_client.get_tools()
        print(f"\n📚 Available MCP Tools:\n")
        for tool in tools:
            print(f"  - {tool['function']['name']}: {tool['function']['description']}")
        
        # 3. Create DialClient:
        #       - api_key=os.getenv("DIAL_API_KEY")
        #       - endpoint="https://ai-proxy.lab.epam.com"
        #       - tools=tools
        #       - mcp_client=mcp_client
        dial_client = DialClient(
            api_key=os.getenv("DIAL_API_KEY"),
            endpoint="https://ai-proxy.lab.epam.com",
            tools=tools,
            mcp_client=mcp_client
        )
        
        # 4. Create list with messages and add there SYSTEM_PROMPT with instructions to LLM
        messages = [Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)]
        
        # 5. Create console chat (infinite loop + ability to exit from chat + preserve message history after the call to dial client)
        print("\n💬 Chat started. Type 'exit' to quit.\n")
        while True:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Add user message to history
            messages.append(Message(role=Role.USER, content=user_input))
            
            # Get completion from DialClient
            ai_message = await dial_client.get_completion(messages)
            
            # Add AI response to history
            messages.append(ai_message)


if __name__ == "__main__":
    asyncio.run(main())
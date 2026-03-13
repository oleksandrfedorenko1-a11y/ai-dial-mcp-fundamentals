import asyncio
import json
import os

from mcp import Resource
from mcp.types import Prompt

from agent.mcp_client import MCPClient
from agent.dial_client import DialClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT


# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts

async def main():
    async with MCPClient(mcp_server_url="http://localhost:8005/mcp") as mcp_client:
        # Get and print available resources
        resources = await mcp_client.get_resources()
        print(f"📚 Available Resources:")
        for resource in resources:
            print(f"  - {resource.uri}: {resource.description}")
        print()

        # Get and print available tools
        tools = await mcp_client.get_tools()
        print(f"🔧 Available Tools:")
        for tool in tools:
            print(f"  - {tool['function']['name']}: {tool['function']['description']}")
        print()

        # Create DIAL client
        dial_client = DialClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            tools=tools,
            mcp_client=mcp_client
        )

        # Initialize messages with system prompt
        messages: list[Message] = [
            Message(role="system", content=SYSTEM_PROMPT)
        ]

        # Get and add prompts from MCP server as user messages
        prompts = await mcp_client.get_prompts()
        print(f"📝 Available Prompts:")
        for prompt in prompts:
            print(f"  - {prompt.name}: {prompt.description}")
        print()

        # Add prompt content to messages
        for prompt in prompts:
            prompt_content = await mcp_client.get_prompt(prompt.name)
            messages.append(Message(role="user", content=f"📌 Prompt - {prompt.name}:\n{prompt_content}"))

        # Console chat loop
        print("💬 Starting conversation with User Management Agent. Type 'exit' to quit.\n")
        while True:
            user_input = input("👤 You: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            # Add user message
            messages.append(Message(role="user", content=user_input))

            try:
                # Get AI response
                ai_response = await dial_client.get_completion(messages)
                messages.append(ai_response)
            except Exception as e:
                print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

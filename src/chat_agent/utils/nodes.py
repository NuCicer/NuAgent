import os
import json
from langchain_core.messages import ToolMessage
from langgraph.graph import END
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv

from .state import State

load_dotenv()

_async_components = {"llm": None, "tools": None, "initialized": False}


async def get_async_components():
    if _async_components["initialized"]:
        return _async_components["llm"], _async_components["tools"]

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
        temperature=0,
        base_url=os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
    )

    client = MultiServerMCPClient(
        {
            "weather": {
                "url": os.getenv("MCP_SERVER_URL"),
                "transport": "streamable_http",
            }
        }
    )

    tools = await client.get_tools()
    llm = llm.bind_tools(tools)
    _async_components["llm"] = llm
    _async_components["tools"] = tools
    _async_components["initialized"] = True

    return llm, tools


class ChatNode:
    def __init__(self) -> None:
        self.llm = None

    async def __call__(self, inputs: dict):
        if self.llm is None:
            self.llm, _ = await get_async_components()
        if messages := inputs.get("messages", []):
            response = await self.llm.ainvoke(messages)
            return {"messages": [response]}
        else:
            raise ValueError("No messages found in input")


class ToolNode:
    def __init__(self) -> None:
        self.tools = None
        self.tools_by_name = None

    async def __call__(self, inputs: dict):
        if self.tools is None:
            _, self.tools = await get_async_components()
            self.tools_by_name = {tool.name: tool for tool in self.tools}
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No messages found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = await self.tools_by_name[tool_call["name"]].ainvoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}


def route_tools(state: State):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

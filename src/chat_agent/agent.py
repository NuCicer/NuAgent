import os
import asyncio
from dotenv import load_dotenv
import uuid
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from src.chat_agent.utils import ToolNode, State, ChatNode, route_tools

load_dotenv()


def create_graph(langgraph_server: bool = False):
    graph_builder = StateGraph(State)

    chat_node = ChatNode()
    tool_node = ToolNode()

    graph_builder.add_node("chatbot", chat_node)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges("chatbot", route_tools)
    graph_builder.add_edge("tools", "chatbot")

    if not langgraph_server:
        memory = MemorySaver()
        return graph_builder.compile(checkpointer=memory)

    return graph_builder.compile()


graph = create_graph(langgraph_server=os.getenv("SERVER_TYPE", "local") == "langgraph")


async def main():
    """Main function for local testing."""

    random_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": random_id}}

    async def stream_graph_updates(user_input: str):
        events = graph.astream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
            stream_mode="updates",
        )
        async for event in events:
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            await stream_graph_updates(user_input)
        except:
            user_input = "What is the weather at (40.714, -74.006) now?"
            print("User: ", user_input)
            await stream_graph_updates(user_input)
            break


if __name__ == "__main__":
    asyncio.run(main())

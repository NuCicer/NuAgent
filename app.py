import uuid
import gradio as gr
from src.chat_agent import graph

thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}


def reset_memory():
    global thread_id
    graph.checkpointer.delete_thread(thread_id)


async def bot(history):
    user_input = history[-1]["content"]
    events = graph.astream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="updates",
    )
    results = []
    responses = []
    async for event in events:
        results.append(event)
        for role, value in event.items():
            print(f"{role}: {value["messages"][-1].content}\n")
            responses.append(value["messages"][-1].content)
            if role == "tools":
                response = "Tool call response:\n" + value["messages"][-1].content
            else:
                response = value["messages"][-1].content
            history.append({"role": "assistant", "content": response})
            yield history


def user(message, history: list):
    return "", history + [{"role": "user", "content": message}]


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages", allow_tags=True)
    msg = gr.Textbox()
    clear = gr.Button("Clear")
    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(reset_memory, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()

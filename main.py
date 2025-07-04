import os
import streamlit as st
import asyncio
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
from utils.strip_leading_json import strip_leading_json

# --- Load environment variables ---
load_dotenv()

# --- Web Search Tool ---
@function_tool
def web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo and return the top results.
    Always pass the user's original question as the query argument.
    """
    print(f"web_search tool called with: {query}")
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(r.get("body", ""))
        if not results:
            return "No relevant results found."
        return "\n---\n".join(results)
    except Exception as e:
        return f"Web search failed due to: {e}"

# --- OpenAI Model Setup ---
token = os.getenv('OPENAI_API_KEY')
endpoint = 'https://api.openai.com/v1'
model = 'gpt-4o'

set_tracing_disabled(True)

client = AsyncOpenAI(
    base_url=endpoint,
    api_key=token
)

model_instance = OpenAIChatCompletionsModel(
    model=model,
    openai_client=client
)

agent = Agent(
    name="Assistant",
    instructions="""
You are a helpful assistant.

Use the `web_search` tool for any of the following:
- If the question involves current events, weather, news, or real-time information.
- If the question asks for lates, most recent, or most up to date information.
- If you are uncertain about the answer.
- If the user directly asks you to use the tool or says "search".

When using the `web_search` tool, always pass the user's original question as the query argument, without rephrasing or summarizing.

Otherwise, answer directly using your own knowledge.
""",
    model=model_instance,
    model_settings=ModelSettings(temperature=0.1),
    tools=[web_search]
)

# --- Streamlit App UI ---
st.title("🔎 Web Search Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("agent"):
        message_placeholder = st.empty()
        with st.spinner("Agent is thinking..."):
            # Async streaming logic
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            async def stream_response():
                full_response = ""
                first_chunk = True
                # Prepare the input as a list of messages for the agent
                input_messages = st.session_state.messages[-10:]
                result = Runner.run_streamed(agent, input=input_messages)
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and hasattr(event.data, "delta") and event.data.delta:
                        delta = event.data.delta
                        if first_chunk:
                            delta = strip_leading_json(delta)
                            first_chunk = False
                        full_response += delta
                        message_placeholder.markdown(full_response + "▌")  # Typing indicator
                return full_response

            response = loop.run_until_complete(stream_response())
            response = strip_leading_json(response)
            message_placeholder.markdown(response)  # Final response

    st.session_state.messages.append({"role": "assistant", "content": response})


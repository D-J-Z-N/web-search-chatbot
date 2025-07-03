import os
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
from openai import AsyncOpenAI
from duckduckgo_search import DDGS
import streamlit as st
import asyncio

from dotenv import load_dotenv
load_dotenv()


@function_tool
def web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo and return the top results.

    Always use this tool for questions about current events, weather, news, or anything requiring up-to-date information.
    Always pass the user's original question as the query argument, without rephrasing or summarizing.
    """
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



# Settings
token = os.getenv('OPENAI_API_KEY')  
endpoint = 'https://api.openai.com/v1' 
model = 'gpt-3.5-turbo'

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
- If you are uncertain about the answer.
- If the user directly asks you to use the tool or says "search".

When using the `web_search` tool, always pass the user's original question as the query argument, without rephrasing or summarizing.

Otherwise, answer directly using your own knowledge.""",
    model=model_instance,
    model_settings=ModelSettings(
        temperature=0.1
    ),
    tools=[web_search]
)

# --- Main Streamlit App ---

st.title("Web Search Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat messages from history
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display agent response in chat message container
    with st.chat_message("agent"):
        message_placeholder = st.empty()
        with st.spinner("Agent is thinking..."):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            response = loop.run_until_complete(Runner.run(agent, prompt))
            message_placeholder.markdown(response.final_output)

    # Add agent response to chat history
    st.session_state.messages.append({"role": "agent", "content": response.final_output})


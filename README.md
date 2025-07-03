# Web Search Chatbot

A minimal Streamlit chatbot app that uses OpenAI's GPT models and a DuckDuckGo web search tool for real-time information.

## Setup
1. **Clone the repository**
2. **Install dependencies** (using uv, pip, or your preferred tool):
   ```sh
   uv pip install -r requirements.txt
   # or
   pip install -r requirements.txt
   ```
3. **Set your OpenAI API key**
   - Create a `.env` file in the project root:
     ```
     OPENAI_API_KEY=sk-...
     ```

## Usage
Run the Streamlit app:
```sh
streamlit run main.py
```

## How it works
- The chatbot uses OpenAI's API for conversation.
- For real-time or current questions, the agent can use a DuckDuckGo search tool.

## Notes
- You need an OpenAI API key with access to the model you specify in `main.py` (e.g., `gpt-4o`).
- The DuckDuckGo tool is used when the agent decides it needs up-to-date information.

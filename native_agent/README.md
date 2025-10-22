# Native Agent

An AI agent framework to rewrite user messages into native, natural English while preserving meaning and intent.

## Features
- Provider-agnostic LLM abstraction (OpenAI, Anthropic, local vLLMs)
- Style profiles (casual, professional, concise, friendly)
- Safety and privacy filters
- Deterministic evaluation tests
- REST API and CLI

## Quickstart
1. Copy `.env.example` to `.env` and fill in your provider keys
2. Install dependencies: `pip install -r requirements.txt`
3. (Optional) Run API: `uvicorn native_agent.server.api:app --reload`
4. Run from the CLI:
   ```bash
   # Rewrite text
   python -m native_agent.cli rewrite "I wanna build up an AI agent" --style professional

   # Analyse live ETH market data (requires `OPENAI_API_KEY` in your environment)
   python -m native_agent.cli analyze-eth
   ```
5. Test the HTTP API with cURL:
   ```bash
   curl -X POST http://localhost:8000/rewrite -H 'Content-Type: application/json' -d '{"text":"I wanna build up an AI agent", "style":"professional"}'
   ```

## Structure
- `providers/`: LLM provider adapters
- `pipeline/`: orchestration, prompts, rules
- `server/`: FastAPI app
- `prompts/`: base and style prompts
- `style_guides/`: examples and tests for tones
- `tests/`: unit and eval tests


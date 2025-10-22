# Native Agent

An AI agent framework to rewrite user messages into native, natural English while preserving meaning and intent.

## Features
- Provider-agnostic LLM abstraction (OpenAI, Anthropic, local vLLMs)
- Style profiles (casual, professional, concise, friendly)
- Safety and privacy filters
- Deterministic evaluation tests
- REST API and CLI

## Quickstart

The instructions below assume you are starting with no coding background. Follow the
steps in order and copy the commands exactly as they appear.

### 1. Install Python (only once)
- Download Python 3.10 or newer from [python.org/downloads](https://www.python.org/downloads/).
- During installation make sure **“Add Python to PATH”** is ticked (Windows) or follow the
  default prompts (macOS/Linux).

### 2. Open a terminal window
- **Windows:** search for “Command Prompt” (or “PowerShell”).
- **macOS:** open “Terminal” from Launchpad.
- **Linux:** open your preferred terminal emulator.

### 3. Move into the project folder
Run this command in the terminal (update the path if you saved the project elsewhere):

```bash
cd path/to/AI-ConversBot/native_agent
```

### 4. Create and activate a virtual environment
This keeps dependencies isolated from the rest of your computer.

```bash
python -m venv .venv
```

Activate it with one of the following commands:

| Platform | Command |
| --- | --- |
| Windows (Command Prompt) | `.venv\Scripts\activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| macOS/Linux | `source .venv/bin/activate` |

You will know it worked when you see `(.venv)` appear at the start of the terminal line.

### 5. Install the project dependencies

```bash
pip install -r requirements.txt
```

### 6. Add your OpenAI key
1. Copy the template environment file:
   ```bash
   cp .env.example .env
   ```
2. Open the new `.env` file in any text editor.
3. Replace `your-openai-key` with the secret key from
   [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

Your `.env` file should end up looking like this:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # optional: change if you prefer another model
```

> ✅ Tip: keep this file private—do not share your API key publicly.

### 7. Run the ETH price analyst agent

```bash
python -m native_agent.cli analyze-eth
```

The command fetches the latest Ethereum (ETH) market data, computes hourly and daily
changes, and prints a natural-language explanation. Example output:

```
Current price: $3,482.11
1h change: +0.82%
24h change: -1.43%
24h high: $3,589.90
24h low: $3,441.05
Analysis:
- ...summary written by the AI...
```

Run the command again whenever you want an updated analysis—the data is live.

### 8. (Optional) Rewrite text with the same CLI

```bash
python -m native_agent.cli rewrite "I wanna build up an AI agent" --style professional
```

You can swap out the quoted sentence or choose another style such as `casual`, `friendly`,
or `concise`.

### 9. (Optional) Run the HTTP API locally

```bash
uvicorn native_agent.server.api:app --reload
```

Then send a request with cURL:

```bash
curl -X POST http://localhost:8000/rewrite \
  -H 'Content-Type: application/json' \
  -d '{"text":"I wanna build up an AI agent", "style":"professional"}'
```

### 10. Need help?

- Show available commands: `python -m native_agent.cli --help`
- Show options for a specific command: `python -m native_agent.cli analyze-eth --help`
- If you see “command not found”, double-check that the virtual environment is activated.
- If Python complains about missing packages, re-run `pip install -r requirements.txt` while
  the virtual environment is active.

## Structure
- `providers/`: LLM provider adapters
- `pipeline/`: orchestration, prompts, rules
- `server/`: FastAPI app
- `prompts/`: base and style prompts
- `style_guides/`: examples and tests for tones
- `tests/`: unit and eval tests


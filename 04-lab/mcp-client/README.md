# Weather Agent - Ollama + MCP Server

AI agent using **Ollama (minimax-m3:cloud)** with tools from a local **MCP server** via Streamable HTTP transport.

## Architecture

```
┌─────────────────┐   Streamable HTTP    ┌─────────────────┐      REST       ┌─────────────────┐
│  Ollama Agent   │ ──────────────────── │   MCP Server    │ ─────────────── │  WeatherAPI.com  │
│  (mcp-client)   │   localhost:8085/mcp │  (mcp-server)   │                 │                 │
└─────────────────┘                      └─────────────────┘                 └─────────────────┘
```

## Features

- **Function Calling** via Ollama (OpenAI-compatible API)
- **MCP Tools**: `get_current_weather`, `get_forecast`, `health_check`
- **Web UI** at http://localhost:8000
- **CLI mode** for quick queries

## Quick Start

### 1. Start the MCP Server

```bash
cd ../mcp-server
python weather.py   # runs on port 8085
```

### 2. Install Dependencies

```bash
cd mcp-client
pip install -r requirements.txt
```

### 3. Run the Agent

```bash
# Web UI
python main.py

# CLI mode
python main.py --cli

# Single question
python main.py --ask "What's the weather in Hanoi?"
```

## Project Structure

```
mcp-client/
├── weather_agent/
│   ├── agent.py           # WeatherAgent class (MCP + Ollama)
│   └── __init__.py
├── main.py                # CLI + Web UI entry point
├── requirements.txt
├── verify_setup.py        # Setup verification
└── README.md
```

## Configuration

| Variable | Where | Description |
|----------|-------|-------------|
| `WEATHERAPI_KEY` | mcp-server | API key from weatherapi.com (optional) |
| `PORT` | mcp-server (env) | Override server port (default: 8085) |

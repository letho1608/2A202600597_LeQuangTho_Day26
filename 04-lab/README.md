# Lab 04 — Weather Agent with MCP + Ollama

A weather agent using **Ollama (minimax-m3:cloud)** for LLM + Function Calling,
connected to an **MCP server** via Streamable HTTP transport.

## Architecture

```
┌─────────────────┐   Streamable HTTP    ┌─────────────────┐      REST       ┌─────────────────┐
│  Ollama Agent   │ ──────────────────── │   MCP Server    │ ─────────────── │  WeatherAPI.com  │
│  (mcp-client)   │   localhost:8085/mcp │  (mcp-server)   │                 │                 │
└─────────────────┘                      └─────────────────┘                 └─────────────────┘
```

Thay vì dùng Google ADK + Gemini (cần API key không bị IP restriction),
lab này dùng **Ollama** với model **minimax-m3:cloud** qua OpenAI-compatible API.

## Tools

| Tool | Description |
|------|-------------|
| `get_current_weather(city)` | Get current weather conditions for a city |
| `get_forecast(city, days)` | Get weather forecast (1–3 days) |
| `health_check()` | Verify server is running |

## Requirements

- Python >= 3.10
- [Ollama](https://ollama.com) installed with `minimax-m3:cloud`:
  ```bash
  ollama pull minimax-m3:cloud
  ```
- WeatherAPI key (optional, get at https://weatherapi.com)

## Setup

### 1. MCP Server

```bash
cd mcp-server
pip install -r <(uv export --frozen --format requirements.txt)   # hoặc dùng pip với fastmcp httpx

export WEATHERAPI_KEY="your_weatherapi_key"  # optional
python weather.py
# Server at http://localhost:8085/mcp
```

### 2. Weather Agent (Client)

```bash
cd mcp-client
pip install -r requirements.txt

# Run verification
python verify_setup.py

# Web UI
python main.py
# Open http://localhost:8000

# Or CLI mode
python main.py --cli

# Or single question
python main.py --ask "Thời tiết Hanoi thế nào?"
```

## ADK so với Ollama

| | Google ADK (original) | Ollama (this fix) |
|---|---|---|
| **LLM** | Gemini 2.5 Flash | minimax-m3:cloud (local) |
| **API key** | Cần Gemini API key | Không cần (chạy local) |
| **Function Calling** | ADK tự xử lý | OpenAI-compatible API |
| **Web UI** | ADK web (built-in) | FastAPI (main.py) |
| **Python version** | >=3.12 | >=3.10 |

Luồng hoạt động giống hệt:
```
User hỏi → LLM (Function Calling) quyết định tool → MCP Client gọi MCP Server
→ kết quả → LLM tổng hợp câu trả lời
```

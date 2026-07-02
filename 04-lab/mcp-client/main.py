"""Weather Agent - CLI and Web UI entry point.

Usage:
    python main.py                    # Start web UI at http://localhost:8000
    python main.py --cli              # Interactive CLI mode
    python main.py --ask "Hanoi weather?"  # Single question
"""

from __future__ import annotations
import asyncio
import sys
import argparse
import logging

from weather_agent import WeatherAgent

logging.basicConfig(level=logging.WARNING)


async def ask_single(question: str) -> str:
    agent = WeatherAgent()
    await agent.connect()
    try:
        return await agent.ask(question)
    finally:
        await agent.disconnect()


async def cli_loop():
    agent = WeatherAgent()
    await agent.connect()
    try:
        tools = ", ".join(agent.tool_names)
        print(f"Weather Agent (Ollama + MCP) | Tools: {tools}")
        print("Type 'quit' to exit.\n")
        while True:
            try:
                q = input("You: ")
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in ("quit", "exit", "q"):
                break
            if not q.strip():
                continue
            print("Agent: ", end="", flush=True)
            ans = await agent.ask(q)
            print(ans)
            print()
    finally:
        await agent.disconnect()


async def run_web():
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import HTMLResponse
        import uvicorn

        app = FastAPI(title="Weather Agent")

        @app.on_event("startup")
        async def startup():
            app.state.agent = WeatherAgent()
            await app.state.agent.connect()
            print(f"✅ Connected to MCP server. Tools: {app.state.agent.tool_names}")

        @app.on_event("shutdown")
        async def shutdown():
            await app.state.agent.disconnect()

        @app.get("/", response_class=HTMLResponse)
        async def index():
            return """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>Weather Agent</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;background:#f5f5f5}
    h1{color:#333;margin-bottom:8px}
    p.sub{color:#666;margin-bottom:24px}
    #chat{background:#fff;border-radius:12px;padding:16px;height:400px;overflow-y:auto;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
    .msg{margin-bottom:12px}
    .msg.user{text-align:right}
    .msg.user .bubble{background:#007aff;color:#fff;display:inline-block;padding:8px 14px;border-radius:16px 4px 16px 16px;max-width:80%;text-align:left}
    .msg.agent .bubble{background:#e9e9eb;color:#333;display:inline-block;padding:8px 14px;border-radius:4px 16px 16px 16px;max-width:80%;white-space:pre-wrap}
    .loading{color:#999;font-style:italic}
    #form{display:flex;gap:8px}
    #input{flex:1;padding:10px 14px;border:1px solid #ddd;border-radius:20px;font-size:15px;outline:none}
    #input:focus{border-color:#007aff}
    #form button{padding:10px 20px;background:#007aff;color:#fff;border:none;border-radius:20px;cursor:pointer;font-size:15px}
    #form button:hover{background:#0056d6}
    #tools{color:#888;font-size:13px;margin-bottom:16px}
  </style>
</head>
<body>
  <h1>☀️ Weather Agent</h1>
  <p class="sub">Ollama (minimax-m3:cloud) + MCP Server</p>
  <div id="tools">Loading...</div>
  <div id="chat"></div>
  <form id="form" onsubmit="return send()">
    <input id="input" placeholder="Ask about weather..." autofocus>
    <button type="submit">Send</button>
  </form>
  <script>
    const chat=document.getElementById('chat'),input=document.getElementById('input'),td=document.getElementById('tools')
    fetch('/tools').then(r=>r.json()).then(d=>{td.textContent='Tools: '+d.tools.join(', ')})
    function addMsg(role,text){const d=document.createElement('div');d.className='msg '+role;d.innerHTML='<div class="bubble">'+text.replace(/\\n/g,'<br>')+'</div>';chat.appendChild(d);chat.scrollTop=chat.scrollHeight}
    async function send(){const q=input.value.trim();if(!q)return false;addMsg('user',q);input.value=''
    const ld=document.createElement('div');ld.className='loading';ld.textContent='Thinking...';chat.appendChild(ld)
    try{const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});ld.remove();addMsg('agent',(await r.json()).answer)}
    catch(e){ld.remove();addMsg('agent','Error: '+e.message)}return false}
  </script>
</body>
</html>"""

        @app.get("/tools")
        async def list_tools():
            return {"tools": app.state.agent.tool_names}

        @app.post("/ask")
        async def ask(req: Request):
            body = await req.json()
            agent = app.state.agent
            answer = await agent.ask(body["question"])
            return {"answer": answer}

        print(f"🌐 Web UI: http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError as e:
        print(f"❌ Web UI requires FastAPI: pip install fastapi uvicorn")
        print(f"   Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Weather Agent")
    parser.add_argument("--cli", action="store_true", help="Interactive CLI mode")
    parser.add_argument("--ask", type=str, help="Single question")
    args = parser.parse_args()

    if args.ask:
        print(asyncio.run(ask_single(args.ask)))
    elif args.cli:
        asyncio.run(cli_loop())
    else:
        asyncio.run(run_web())


if __name__ == "__main__":
    main()

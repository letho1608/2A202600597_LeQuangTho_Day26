"""Weather Agent with Ollama + MCP Server."""
from __future__ import annotations
import asyncio
import json
import logging
from typing import Any

import httpx
from openai import OpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_SERVER_URL = "http://localhost:8085/mcp"
OLLAMA_BASE = "http://localhost:11434/v1"
MODEL = "minimax-m3:cloud"

openai_client = OpenAI(base_url=OLLAMA_BASE, api_key="ollama")


class WeatherAgent:
    def __init__(self, mcp_url: str = MCP_SERVER_URL):
        self.mcp_url = mcp_url
        self.tools: list[dict] = []
        self.tool_names: list[str] = []
        self._connected = False

    async def connect(self):
        self._http_client = httpx.AsyncClient(
            headers={"Accept": "application/json, text/event-stream"}
        )
        self._stream_ctx = streamable_http_client(
            self.mcp_url, http_client=self._http_client
        )
        self._read, self._write, self._sid = await self._stream_ctx.__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.__aenter__()
        await self._session.initialize()

        tools_result = await self._session.list_tools()
        for t in tools_result.tools:
            schema = {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema if hasattr(t, 'inputSchema') else {"type": "object", "properties": {}},
                },
            }
            self.tools.append(schema)
            self.tool_names.append(t.name)
        self._connected = True

    async def disconnect(self):
        if not self._connected:
            return
        await self._session.__aexit__(None, None, None)
        await self._stream_ctx.__aexit__(None, None, None)
        await self._http_client.aclose()
        self._connected = False

    async def call_tool(self, name: str, arguments: dict) -> str:
        result = await self._session.call_tool(name, arguments)
        return result.content[0].text

    async def ask(self, user_input: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Bạn là trợ lý thời tiết thân thiện. Dùng emoji phù hợp. "
                "Trả lời ngắn gọn, tự nhiên bằng tiếng Việt.",
            },
            {"role": "user", "content": user_input},
        ]

        resp = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=self.tools,
            stream=False,
        )

        msg = resp.choices[0].message

        while msg.tool_calls:
            msg_dict = {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            }
            messages.append(msg_dict)

            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                logger.info(f"Calling tool: {tc.function.name}({args})")
                result = await self.call_tool(tc.function.name, args)
                logger.info(f"Result: {result[:100]}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            resp = openai_client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=self.tools,
                stream=False,
            )
            msg = resp.choices[0].message

        return msg.content or ""

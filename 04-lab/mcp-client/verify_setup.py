#!/usr/bin/env python3
"""Verification script for Weather Agent (Ollama + MCP) setup."""
import os
import sys
from pathlib import Path

def check_ollama():
    """Check if Ollama is running and model is available"""
    print("🔍 Checking Ollama server...")
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        models = [m["name"] for m in r.json().get("models", [])]
        if "minimax-m3:cloud" in models:
            print(f"✅ Ollama running - minimax-m3:cloud available")
            return True
        else:
            print(f"⚠️  Ollama running but minimax-m3:cloud not found")
            print(f"   Run: ollama pull minimax-m3:cloud")
            return False
    except Exception as e:
        print(f"❌ Ollama not reachable: {e}")
        print(f"   Make sure Ollama is installed and running")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking dependencies...")

    required_packages = [
        ("openai", "OpenAI"),
        ("mcp", "MCP"),
        ("fastmcp", "FastMCP"),
        ("httpx", "httpx"),
    ]

    all_installed = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} not installed")
            all_installed = False

    if not all_installed:
        print("\n   Install with: pip install -r requirements.txt")

    return all_installed

def check_agent_structure():
    """Check if agent directory structure is correct"""
    print("\n🔍 Checking agent structure...")

    required_files = [
        "weather_agent/agent.py",
        "weather_agent/__init__.py",
        "main.py",
    ]

    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            all_exist = False

    return all_exist

def check_mcp_server():
    """Check if MCP server is accessible"""
    print("\n🔍 Checking MCP server connectivity...")

    server_url = "http://localhost:8085/mcp"

    try:
        import httpx
        import asyncio
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        async def test_connection():
            http_client = httpx.AsyncClient(
                headers={"Accept": "application/json, text/event-stream"}
            )
            async with http_client:
                async with streamable_http_client(server_url, http_client=http_client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = await session.list_tools()
                        return len(tools.tools) > 0

        success = asyncio.run(test_connection())

        if success:
            print(f"✅ MCP server reachable at {server_url}")
            return True
        else:
            print(f"⚠️  MCP server returned no tools")
            return False

    except Exception as e:
        print(f"❌ Cannot reach MCP server: {e}")
        return False

def check_agent_import():
    """Try to import the WeatherAgent class"""
    print("\n🔍 Checking agent import...")

    try:
        import warnings
        warnings.filterwarnings("ignore")
        import logging
        logging.disable(logging.CRITICAL)

        from weather_agent import WeatherAgent
        print(f"✅ WeatherAgent class imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import agent: {e}")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Weather Agent Setup Verification (Ollama + MCP)")
    print("=" * 60)
    print()

    checks = [
        check_ollama(),
        check_dependencies(),
        check_agent_structure(),
        check_mcp_server(),
        check_agent_import(),
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed!")
        print("\n🚀 Ready to start!")
        print("   1. Start MCP server:   python ../mcp-server/weather.py")
        print("   2. Start web UI:       python main.py")
        print("   3. CLI mode:           python main.py --cli")
        print("\n📍 Web UI: http://localhost:8000")
        return 0
    else:
        print("❌ Some checks failed")
        print("\n⚠️  Fix the issues above and run this script again")
        return 1

if __name__ == "__main__":
    sys.exit(main())

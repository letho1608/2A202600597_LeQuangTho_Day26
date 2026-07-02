"""Function Calling với Ollama + minimax-m3:cloud.
Thay thế Google Gemini SDK bằng OpenAI-compatible endpoint của Ollama."""

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

MODEL = "minimax-m3:cloud"

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế "
    "(ví dụ: mang ô, mặc áo mỏng, ...)."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy thời tiết hiện tại của một thành phố",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Tên thành phố",
                    }
                },
                "required": ["city"],
            },
        },
    }
]


def get_weather(city: str) -> str:
    """Trả về thời tiết (mock) của *city*."""
    mock_data = {
        "Hà Nội": {"nhiệt_độ": "29°C", "thời_tiết": "trời mưa nhẹ", "độ_ẩm": "82%", "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"}},
        "Hồ Chí Minh": {"nhiệt_độ": "33°C", "thời_tiết": "mưa rào", "độ_ẩm": "75%", "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"}},
        "Đà Nẵng": {"nhiệt_độ": "30°C", "thời_tiết": "nhiều mây", "độ_ẩm": "78%", "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"}},
    }
    import json
    default = {"nhiệt_độ": "28°C", "thời_tiết": "không có dữ liệu chi tiết"}
    return json.dumps({"city": city, **mock_data.get(city, default)}, ensure_ascii=False)


def run(prompt: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt},
    ]

    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        stream=False,
    )

    msg = resp.choices[0].message

    while msg.tool_calls:
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            import json
            args = json.loads(tc.function.arguments)
            print(f"  [model yêu cầu] {tc.function.name}({args})")
            result = get_weather(**args)
            print(f"  [app thực thi]  -> {result}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            stream=False,
        )
        msg = resp.choices[0].message

    return msg.content or ""


if __name__ == "__main__":
    question = "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))

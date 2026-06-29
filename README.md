# Phân biệt MCP và Function Calling

Đây là hai khái niệm hay bị nhầm lẫn nhưng thực ra ở **hai tầng khác nhau**, và **bổ sung cho nhau** chứ không thay thế.

## Định nghĩa ngắn gọn

**Function Calling** là một *khả năng của model* (capability). Model được huấn luyện để khi bạn đưa cho nó danh sách các "công cụ" (kèm schema mô tả tham số), nó có thể tự quyết định gọi công cụ nào và sinh ra JSON tham số phù hợp. Bản thân model **không chạy** function — nó chỉ nói "hãy gọi `get_weather(city='Hanoi')`". Code của bạn mới là người thực thi.

**MCP (Model Context Protocol)** là một *giao thức chuẩn* (protocol) — giống như USB-C hay HTTP cho thế giới AI. Nó định nghĩa cách một **MCP Client** (như Claude Code, Claude Desktop) kết nối tới các **MCP Server** để khám phá và sử dụng tools, resources, prompts một cách thống nhất.

## So sánh trực tiếp

| Tiêu chí | Function Calling | MCP |
|---|---|---|
| **Bản chất** | Khả năng của LLM | Giao thức giao tiếp client–server |
| **Tầng** | Tầng model | Tầng hạ tầng/tích hợp |
| **Ai định nghĩa tool?** | Bạn hard-code trong từng app | Server tự công bố (self-describe) tool |
| **Tái sử dụng** | Phải viết lại cho mỗi app/model | Viết 1 lần, mọi MCP client dùng được |
| **Thực thi** | App của bạn tự chạy | MCP Server chạy, client điều phối |
| **Tính chuẩn hóa** | Mỗi nhà cung cấp 1 kiểu (OpenAI, Anthropic khác nhau) | Một chuẩn chung do Anthropic đề xuất |
| **Phạm vi** | Chỉ "gọi hàm" | Tools + Resources + Prompts |

## Quan hệ giữa chúng

Điểm quan trọng nhất: **MCP dùng Function Calling bên dưới**. Chúng không loại trừ nhau.

```
User hỏi
   │
   ▼
LLM (dùng Function Calling để quyết định gọi tool nào)
   │
   ▼
MCP Client  ──[giao thức MCP]──►  MCP Server (thực thi tool thật)
   │                                   │
   ◄───────────── kết quả ─────────────┘
   ▼
LLM tổng hợp câu trả lời
```

## Ví dụ minh họa

**Chỉ Function Calling (cách cũ):** Bạn viết app, định nghĩa tool `get_weather` ngay trong code, tự gọi API thời tiết, tự xử lý. Nếu muốn dùng tool này ở app khác → copy/viết lại.

**Với MCP:** Bạn viết một **weather MCP server** một lần. Sau đó Claude Desktop, Claude Code, Cursor... đều cắm vào dùng được mà không cần sửa code. Server tự "khai báo" nó có tool gì.

## Khi nào dùng cái nào?

- **Function Calling thuần**: app đơn giản, tool gắn chặt với 1 ứng dụng, không cần chia sẻ.
- **MCP**: muốn tool/tích hợp dùng lại được trên nhiều AI client, muốn tách biệt logic tool khỏi app, hoặc xây hệ sinh thái tích hợp (DB, file, API nội bộ...).

## Minh hoạ bằng mã nguồn

Cùng một tool `get_weather`, dưới đây là hai cách triển khai để thấy rõ sự khác biệt.

### Cách 1 — Function Calling thuần (Google Gemini SDK)

Tool được **định nghĩa và thực thi ngay trong app**. Model chỉ quyết định gọi tool nào, app tự chạy và đưa kết quả trở lại.

```python
# pip install google-genai
from google import genai
from google.genai import types

client = genai.Client()

# 1. App tự định nghĩa schema của tool
get_weather_declaration = types.FunctionDeclaration(
    name="get_weather",
    description="Lấy thời tiết hiện tại của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(
                type=types.Type.STRING, description="Tên thành phố"
            )
        },
        required=["city"],
    ),
)
tools = [types.Tool(function_declarations=[get_weather_declaration])]

# 2. App tự thực thi tool
def get_weather(city: str) -> str:
    # Ở đây thường gọi API thời tiết thật; demo trả về cứng
    return f"{city}: 29°C, trời mưa"

contents = [
    types.Content(role="user", parts=[types.Part.from_text(text="Thời tiết Hanoi thế nào?")])
]

# 3. Gọi model — model QUYẾT ĐỊNH gọi tool nào, KHÔNG tự chạy
resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(tools=tools),
)

# 4. App đọc yêu cầu gọi tool và TỰ THỰC THI
if resp.function_calls:
    contents.append(resp.candidates[0].content)

    function_responses = []
    for fc in resp.function_calls:
        result = get_weather(**fc.args)  # <-- app chạy, không phải model
        function_responses.append(
            types.Part.from_function_response(
                name=fc.name, response={"result": result}
            )
        )

    contents.append(types.Content(role="user", parts=function_responses))

    # 5. Gọi lại model để nó tổng hợp câu trả lời cuối
    final = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(tools=tools),
    )
    print(final.text)
```

> Nhược điểm: nếu muốn dùng `get_weather` ở một app khác, bạn phải copy lại cả schema lẫn hàm thực thi.

### Cách 2 — MCP (server tự công bố tool, mọi client dùng chung)

Tool được tách ra **một MCP server độc lập**. Server tự "khai báo" nó có tool gì; bất kỳ MCP client nào (Claude Code, Claude Desktop, Cursor...) cũng cắm vào dùng được mà không cần biết code bên trong.

**Server** — `weather_server.py`:

```python
# pip install "mcp[cli]"
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

_MOCK_DB = {
    "Hanoi": "29°C, trời mưa",
    "Haiphong": "33°C, mưa rào",
    "Danang": "30°C, nhiều mây",
}

# Chỉ cần decorator — schema được TỰ ĐỘNG sinh ra từ type hints + docstring
@mcp.tool()
def get_weather(city: str) -> str:
    """Lấy thời tiết hiện tại của một thành phố."""
    return f"{city}: {_MOCK_DB.get(city, '28°C, không có dữ liệu chi tiết')}"

if __name__ == "__main__":
    mcp.run()  # chạy server qua stdio
```

**Client** — kết nối tới server và để model gọi tool qua giao thức MCP:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command=sys.executable, args=["weather_server.py"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Client KHÁM PHÁ tool mà server công bố (không hard-code)
            tools = await session.list_tools()
            print("Tools server cung cấp:", [t.name for t in tools.tools])

            # 2. Client gọi tool — SERVER thực thi rồi trả kết quả về qua MCP
            for city in ["Hanoi", "Danang", "Haiphong"]:
                result = await session.call_tool("get_weather", {"city": city})
                print(f"Kết quả: {result.content[0].text}")

asyncio.run(main())
```

**Đăng ký server với Claude Code** (làm 1 lần, dùng mãi):

```bash
claude mcp add weather -- python /đường/dẫn/weather_server.py
```

Sau bước này, Claude tự `list_tools` để biết server có `get_weather`, rồi dùng **chính cơ chế Function Calling** để quyết định khi nào gọi — bạn không phải viết thêm dòng code tích hợp nào.

### Điểm khác biệt rút ra từ code

| | Function Calling thuần | MCP |
|---|---|---|
| Khai báo schema | Tự viết tay trong app | `@mcp.tool()` tự sinh từ type hints |
| Nơi thực thi tool | Trong app gọi model | Trong MCP server riêng |
| Khám phá tool | Hard-code danh sách `tools` | `session.list_tools()` tại runtime |
| Dùng lại ở app khác | Copy code | Cắm thêm client, không sửa server |
| Vai trò Function Calling | Là toàn bộ cơ chế | Là lớp model bên trong MCP |

---

**Tóm lại bằng một câu:** Function Calling là *cơ chế model gọi công cụ*; MCP là *chuẩn để kết nối model với các công cụ đó* — và MCP thực chất dùng Function Calling làm nền tảng để hoạt động.

import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()
BASE = Path(__file__).parent.resolve()

SYSTEM_PROMPT = """You are an Excel data analyst. Use ONLY the run_excel_code tool for all work.
Never call a tool named "python" or "browser"; they do not exist.
Default workbook: students.xlsx (in the working directory).

Rules:
- First inspect the workbook (sheet names, columns, head()) before assuming structure.
- Use pandas for analysis, openpyxl for edits. Save edits back to students.xlsx.
- For insights: compute real numbers (means, top/bottom, correlations, distributions)
  and print them, then explain them in plain language.
- For visualization: use matplotlib, save PNG to charts/<descriptive_name>.png
  (plt.tight_layout(); plt.savefig(...); plt.close()). Never use plt.show().
- If the tool returns an error, fix the code and retry.
- Keep the final answer short and clear."""


async def ask(question: str, history: list) -> str:
    client = MultiServerMCPClient({
        "excel_server": {
            "command": sys.executable,
            "args": [str(BASE / "task_server.py")],
            "transport": "stdio",
        }
    })
    tools = await client.get_tools()

    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, max_retries=4)
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

    # only plain user/assistant text from recent turns -> few tokens
    messages = history[-6:] + [("user", question)]
    for attempt in range(3):
        try:
            result = await agent.ainvoke({"messages": messages}, {"recursion_limit": 15})
            return result["messages"][-1].content
        except Exception as e:
            if "tool_use_failed" in str(e) and attempt < 2:
                messages = messages + [("user", "Use only the run_excel_code tool.")]
                continue
            raise
    return result["messages"][-1].content
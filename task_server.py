from mcp.server.fastmcp import FastMCP
import subprocess, sys, tempfile, os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
(BASE_DIR / "charts").mkdir(exist_ok=True)
MAX_OUTPUT = 3000  # keep tool output small to save tokens

PRELUDE = (
    "import matplotlib\nmatplotlib.use('Agg')\n"
    "import warnings\nwarnings.filterwarnings('ignore')\n"
)

mcp = FastMCP("Excel Python MCP")


@mcp.tool()
def run_excel_code(code: str) -> str:
    """Execute Python code (pandas, openpyxl, matplotlib available).
    Working directory contains students.xlsx. Save charts as PNG into
    the 'charts/' folder. Use print() to return results."""
    script_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(PRELUDE + code)
            script_path = f.name

        r = subprocess.run(
            [sys.executable, script_path],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=BASE_DIR,
        )
        out = ""
        if r.stdout:
            out += f"OUTPUT:\n{r.stdout}"
        if r.stderr:
            out += f"\nERROR:\n{r.stderr[-1500:]}"
        out = out or "Python executed successfully."
        return out[:MAX_OUTPUT]

    except subprocess.TimeoutExpired:
        return "ERROR: Python execution timed out."
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"
    finally:
        if script_path:
            try:
                os.remove(script_path)
            except OSError:
                pass


if __name__ == "__main__":
    mcp.run()
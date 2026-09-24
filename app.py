import asyncio, time
from pathlib import Path
import pandas as pd
import streamlit as st
from agent import ask

BASE = Path(__file__).parent
XLSX = BASE / "students.xlsx"
CHARTS = BASE / "charts"
CHARTS.mkdir(exist_ok=True)

st.set_page_config(page_title="Excel AI Analyst", layout="wide")
st.title("📊 Excel AI Analyst")

# ---- sidebar: upload + preview ----
with st.sidebar:
    up = st.file_uploader("Upload Excel file", type=["xlsx"])
    if up:
        XLSX.write_bytes(up.getbuffer())
        st.success("Saved as students.xlsx")
    if XLSX.exists():
        sheet = st.selectbox("Preview sheet", pd.ExcelFile(XLSX).sheet_names)
        st.dataframe(pd.read_excel(XLSX, sheet_name=sheet).head(20))
        st.download_button("Download workbook", XLSX.read_bytes(), "students.xlsx")
    st.caption("Try: 'Give me insights', 'Plot average grade by class', 'Add a Summary sheet'")

# ---- chat state ----
if "history" not in st.session_state:
    st.session_state.history = []   # [(role, text)]
    st.session_state.images = {}    # index -> [chart paths]

for i, (role, text) in enumerate(st.session_state.history):
    with st.chat_message(role):
        st.markdown(text)
        for img in st.session_state.images.get(i, []):
            st.image(img)

if q := st.chat_input("Ask about your Excel file..."):
    with st.chat_message("user"):
        st.markdown(q)

    start = time.time()
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                answer = asyncio.run(ask(q, st.session_state.history))
            except Exception as e:
                answer = f"⚠️ Error: `{type(e).__name__}: {e}`"
        st.markdown(answer)

        new_imgs = [str(p) for p in CHARTS.glob("*.png") if p.stat().st_mtime >= start]
        for img in new_imgs:
            st.image(img)

    st.session_state.history.append(("user", q))
    st.session_state.history.append(("assistant", answer))
    st.session_state.images[len(st.session_state.history) - 1] = new_imgs
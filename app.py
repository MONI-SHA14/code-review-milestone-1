"""Streamlit developer portal - AI Code Review & Security Analysis Agent."""
import json
import streamlit as st
from src import config
from src.llm import LLM
from src.rag import KnowledgeBase
from src.submission import build_submission, read_upload
from src.orchestrator import run_pipeline
from src.agents.assistant import Assistant
from src.report import build_pdf
from src.models import SEVERITIES

st.set_page_config(page_title="AI Code Review Agent", page_icon="🛡️", layout="wide")
ICON = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🔵", "Info": "⚪"}


@st.cache_resource
def get_kb():
    return KnowledgeBase()


@st.cache_resource
def get_llm():
    return LLM()


kb, llm = get_kb(), get_llm()
st.title("🛡️ AI Code Review & Security Analysis Agent")
st.caption(f"Mode: {'Claude-powered agents' if llm.available else 'Offline rule-based agents'} · "
           f"Knowledge base: {len(kb.chunks)} chunks indexed")

with st.sidebar:
    st.header("Samples")
    for p in sorted(config.SAMPLES_DIR.glob("*")):
        if p.suffix in (".py", ".java") and st.button(p.name, use_container_width=True):
            st.session_state["sample"] = (p.name, p.read_text())
    st.markdown("---")
    st.markdown("**Pipeline**: Code Analysis ∥ Security → Remediation → PR Summary → RAG Assistant")

tab_submit, tab_find, tab_chat, tab_report = st.tabs(["1 · Submit", "2 · Findings", "3 · Assistant", "4 · Report"])

with tab_submit:
    name, sample_code = st.session_state.get("sample", (None, ""))
    mode = st.radio("Input", ["Paste code", "Upload file"], horizontal=True)
    sub = None
    if mode == "Paste code":
        lang = st.selectbox("Language", ["auto-detect", "python", "java"])
        code = st.text_area("Source code", value=sample_code, height=320)
        if st.button("Analyze", type="primary"):
            sub = build_submission(code, name, None if lang == "auto-detect" else lang)
    else:
        up = st.file_uploader("Python or Java file", type=["py", "java"])
        if up and st.button("Analyze", type="primary"):
            sub = read_upload(up.read(), up.name)
    if sub is not None:
        if not sub.valid:
            st.error("Validation failed:\n\n" + "\n".join(f"- {e}" for e in sub.errors))
        else:
            with st.spinner("Running agents..."):
                rv = run_pipeline(sub, kb, llm)
                st.session_state["review"] = rv
                st.session_state["pdf"] = build_pdf(rv)       # final report, built once per analysis
                st.session_state["chat"] = []
            st.success("Analysis complete - open the Findings tab.")

review = st.session_state.get("review")

with tab_find:
    if not review:
        st.info("Submit code first.")
    else:
        s = review.summary
        base = review.submission.filename.rsplit(".", 1)[0]
        d1, d2, d3 = st.columns(3)
        d1.download_button("📄 Download Final Report (PDF)", st.session_state["pdf"],
                           f"{base}_code_review_report.pdf", "application/pdf",
                           type="primary", use_container_width=True)
        d2.download_button("📝 PR Summary (Markdown)", s["markdown"], f"{base}_pr_summary.md",
                           "text/markdown", use_container_width=True)
        d3.download_button("🧾 Findings (JSON)", json.dumps([f.to_dict() for f in review.findings], indent=2),
                           f"{base}_findings.json", "application/json", use_container_width=True)
        st.divider()
        c = st.columns(6)
        c[0].metric("Health score", f"{review.health_score}/100", review.grade)
        for col, sev in zip(c[1:], SEVERITIES):
            col.metric(f"{ICON[sev]} {sev}", s["counts"][sev])
        st.markdown(s["markdown"])
        pick = st.multiselect("Filter severity", SEVERITIES, default=SEVERITIES)
        for f in review.findings:
            if f.severity in pick:
                with st.expander(f"{ICON[f.severity]} {f.id} · {f.title} · line {f.line}"):
                    st.caption(f"{f.agent} · {f.cwe} · {f.owasp}")
                    st.code(f.snippet, language=review.submission.language)
                    st.write(f.description)
                    st.markdown(f"**Remediation:** {f.remediation}")
                    if f.fixed_code:
                        st.code(f.fixed_code, language=review.submission.language)
                    if f.references:
                        st.caption("Sources: " + ", ".join(f.references))

with tab_chat:
    if not review:
        st.info("Submit code first.")
    else:
        bot = Assistant(kb, llm)
        st.session_state.setdefault("chat", [])
        for role, text in st.session_state["chat"]:
            st.chat_message(role).markdown(text)
        q = st.chat_input("Ask e.g. 'explain line 12' or 'how do I prevent XSS?'")
        if q:
            st.chat_message("user").markdown(q)
            res = bot.ask(q, review.findings, st.session_state["chat"])
            ans = res["answer"] + (f"\n\n*Sources: {', '.join(res['sources'])}*" if res["sources"] else "")
            st.chat_message("assistant").markdown(ans)
            st.session_state["chat"] += [("user", q), ("assistant", ans)]

with tab_report:
    if not review:
        st.info("Submit code first.")
    else:
        st.download_button("⬇️ Download Final Report (PDF)", st.session_state["pdf"],
                           "code_review_report.pdf", "application/pdf", type="primary")
        st.download_button("⬇️ Download findings (JSON)",
                           json.dumps([f.to_dict() for f in review.findings], indent=2), "findings.json")
        st.json({k: round(v, 3) for k, v in review.timings.items()})

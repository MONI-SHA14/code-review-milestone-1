# AI Code Review & Security Analysis Agent

Multi-agent platform that reviews pasted/uploaded **Python** and **Java** code for quality issues and
OWASP-style vulnerabilities, proposes fixes, and answers follow-up questions via a RAG assistant.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
pytest -q                                              # end-to-end tests
```
Optional: `export ANTHROPIC_API_KEY=...` (see `.env.example`) to switch the Remediation, PR Summary and
Assistant agents to Claude. Without a key everything runs offline with rule-based agents + RAG.

## Architecture
```
Submission (paste/upload + syntax validation)
        |
  +-----+------------------+   (parallel, ThreadPoolExecutor)
  | Code Analysis Agent    |   Security Vulnerability Agent
  +-----+------------------+
        v  merged + severity-sorted findings (shared Finding schema, IDs F-001...)
  Remediation Agent  <---- RAG (TF-IDF vector index over kb/*.md)
        v
  PR Summary Agent -> health score, verdict, prioritized fixes
        v
  Streamlit portal: Findings | RAG Assistant | PDF/JSON export
```

## Milestone map
| Milestone | Where |
|---|---|
| 1 Submission module, KB + RAG | `src/submission.py`, `src/rag.py`, `kb/` |
| 2 Code Analysis, Security agents, parallel orchestration, accuracy validation | `src/agents/code_analysis.py`, `src/agents/security.py`, `src/orchestrator.py`, `tests/` |
| 3 Remediation, PR Summary, Findings portal, Assistant | `src/agents/remediation.py`, `pr_summary.py`, `assistant.py`, `app.py` |
| 4 PDF report, E2E tests, tuning, demo | `src/report.py`, `tests/test_pipeline.py`, `samples/` |

## Demo samples (3+ complexity levels)
- `samples/simple_utils.py` - clean, low complexity (expect grade A)
- `samples/flask_app_vulnerable.py` - medium, many OWASP issues
- `samples/order_processor.py` - high-complexity code smells
- `samples/UserService.java` - Java with security + quality problems

## Extending
- Add a security rule: append a dict to `RULES` in `src/agents/security.py` and a fix template in `remediation.py`.
- Add knowledge: drop a `.md` file (with `# Title` and `## Section` headings) into `kb/`; the index rebuilds automatically.
- Swap TF-IDF for neural embeddings by changing `KnowledgeBase.build/search` in `src/rag.py`.

## Limitations
Rule-based detection is pattern/AST driven (no full taint analysis) so it can miss data-flow bugs or flag false
positives; with an API key, Claude refines remediation text but detection remains deterministic for reproducibility.

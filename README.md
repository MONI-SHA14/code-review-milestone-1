# AI Code Review & Security Analysis Agent

Complete implementation for Milestones 1–3 from `codeanaylsismilestone4.docx`.

## Included requirements

- **Milestone 1:** Python/Java submission, syntax validation, secure-coding knowledge base, chunking, local TF–IDF vector retrieval, agent/data-model design.
- **Milestone 2:** Code Analysis Agent, Security Vulnerability Agent, severity scoring, location-specific findings, parallel multi-agent orchestration, sample validation.
- **Milestone 3:** Remediation Agent, PR Summary Agent, findings display/severity dashboard, RAG-powered Conversational Code Assistant.
- **Milestone 4:** JSON/Markdown/PDF code-review reports, end-to-end tests, optimization plan, technical documentation, and final demonstration workflow.

The implementation is intentionally deterministic and local-first. It does not send source code to an external provider. The architecture is ready for an LLM provider to be added later behind the agent interfaces.

## Run

```bash
cd code_review_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000.

## API

- `GET /api/health`
- `POST /api/analyze` JSON: `{ "language": "python|java", "filename": "...", "code": "..." }`
- `POST /api/analyze/upload` multipart field `file`
- `POST /api/chat` JSON: `{ "question": "...", "review_id": "optional" }`
- `GET /api/reviews/{review_id}`
- `GET /api/reviews/{review_id}/export?format=json|markdown|pdf`

## Exact demo workflow

1. Paste or upload `samples/vulnerable.py`.
2. Click **Analyze code**.
3. The expected review contains security findings for SQL injection, hardcoded secret, XSS, and missing CSRF protection, plus code-quality findings such as broad exception handling and high complexity.
4. Each finding has an ID, category, OWASP mapping where applicable, severity, confidence, line range, explanation, remediation, corrected-code example, and knowledge-base sources.
5. Ask the assistant: `How do I fix the SQL injection?` or `Why is this critical?`.

## Project structure

```text
app/
  main.py             FastAPI routes and static-file serving
  models.py           Pydantic request/response/data models
  analyzers.py        Python and Java syntax + deterministic rule analyzers
  rag.py              Secure-coding corpus, chunking, TF-IDF retrieval
  agents.py           Code Analysis, Security, Remediation, PR Summary, Assistant
  orchestration.py    Parallel pipeline and in-memory review store
  reports.py          JSON/Markdown export
static/
  index.html          Developer portal
  app.js              Portal behavior
  styles.css          Portal styling
samples/               Vulnerable Python and Java demo files
tests/                 Automated pipeline tests
```

## Requirement traceability

| Requirement | Implementation |
|---|---|
| Paste/file upload for Python/Java | `app/main.py`, `static/index.html` |
| Syntax validation | `app/analyzers.py` |
| OWASP-style security scanning | `SecurityVulnerabilityAgent` rules in `app/agents.py` |
| Code smells/design/complexity | `CodeAnalysisAgent` rules in `app/agents.py` |
| Severity scoring/location | `Finding` model and `severity_score()` |
| Parallel orchestration | `run_in_parallel()` in `app/orchestration.py` |
| Corrected code and explanations | `RemediationAgent` |
| Pull-request style summary | `PRSummaryAgent` |
| Findings display and health score | `static/app.js`, `Summary` model |
| RAG Q&A grounded in secure coding | `KnowledgeBase`, `ConversationalCodeAssistant` |

## Milestone 4 deliverables

- `TECHNICAL_DOCUMENTATION.md` — architecture, security notes, validation, optimization, and demo script.
- `demo.py` — prints the exact structured output for the included Python and Java samples.
- `tests/test_pipeline.py` — end-to-end regression suite.
- PDF export endpoint — produces an exportable review report with severity breakdown, findings, corrected examples, PR summary, and remediation roadmap.

## Test

```bash
pytest -q
```

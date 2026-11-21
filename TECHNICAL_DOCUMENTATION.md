# Technical Documentation — Milestones 1–4

## Architecture

The request enters `POST /api/analyze`, is validated for Python or Java syntax, and is submitted to two independent agents in a `ThreadPoolExecutor`. Their findings are normalized into one `Finding` model, enriched by the Remediation Agent using the local secure-coding knowledge base, scored, and compiled by the PR Summary Agent. Reviews are stored in-memory for this prototype.

The Conversational Code Assistant retrieves top matching knowledge chunks with TF–IDF and prioritizes findings from the active review when answering a question. Every answer returns source names so grounding is visible.

## Security design

The prototype does not execute submitted code. It uses parsing and bounded regular-expression rules. It does not persist uploaded source to disk, and it does not expose secret values intentionally. For production, add authentication, encrypted persistence, sandboxed AST analysis, rate limiting, secret redaction, audit logging, and a real vector database.

## Milestone 4 validation

The test suite covers:

- Python and Java syntax validation.
- Required OWASP-style detections across known vulnerable samples.
- Severity scoring and health-score calculation.
- Parallel pipeline output and remediation enrichment.
- RAG retrieval and grounded assistant response.
- JSON, Markdown, and PDF report exports.
- API-level submission and invalid-source errors.

Run:

```bash
pytest -q
```

## Accuracy and optimization plan

1. Add AST/Java-parser rules where regex is insufficient.
2. Add rule fixtures for true positives and false positives and calculate precision/recall per rule.
3. Calibrate severity penalties against reviewer labels instead of fixed prototype weights.
4. Replace TF–IDF with an embedding model/vector store for semantic retrieval while keeping source citations.
5. Add retrieval metrics: hit@k, MRR, and grounded-answer citation rate.
6. Version agent prompts/rules and keep regression fixtures for every vulnerability.

## Final demonstration

1. Start the API with `uvicorn app.main:app --reload --port 8000`.
2. Open the portal and run the preloaded Python sample.
3. Show the score, severity chips, line locations, remediation code, and PR summary.
4. Ask the assistant about SQL injection and show the cited OWASP source.
5. Download the Markdown and PDF report.
6. Upload `samples/VulnerableController.java` and repeat to demonstrate language coverage.
7. Run `pytest -q` and show the green end-to-end suite.

# Milestone 1 Foundation Study

## OWASP-aligned vulnerability scope

The later Security Vulnerability Agent should prioritize injection (especially SQL injection), cross-site scripting, cross-site request forgery, hardcoded secrets, broken access control, and insecure authentication. Findings should carry a severity, confidence, CWE/OWASP reference, source location, explanation, and remediation.

## Secure coding rules

- Parameterize database queries; never concatenate untrusted input into SQL.
- Encode output for its target context (HTML, JavaScript, URL, shell).
- Keep secrets in a managed secret store or environment configuration, not source code.
- Authenticate consistently and authorize every protected object/action server-side.
- Use strong password hashing, secure session cookies, CSRF protections, and safe defaults.
- Validate input with allowlists where practical, limit resource use, and log security events without leaking secrets.

## Code smell patterns

Long methods, duplicated logic, deeply nested conditionals, broad exception handling, dead code, mutable global state, unclear names, magic values, missing resource cleanup, and excessive coupling are candidates for the Code Analysis Agent. A smell is a review signal, not automatically a defect; the eventual agent should include evidence and confidence.

## RAG architecture study

Documents are normalized to text, split into overlapping chunks, embedded into a vector representation, and persisted with source metadata. A user question is embedded using the same function, ranked by cosine similarity, and the top chunks are passed to a conversational layer as grounded context. This prototype uses deterministic normalized term-frequency vectors so the pipeline works offline. A production version can replace `embed()` with a hosted embedding model while retaining the chunk and retrieval contracts.

## Milestone 1 acceptance checklist

- [x] Foundation notes recorded.
- [x] System architecture, responsibilities, flow, and data models documented.
- [x] Paste and `.py`/`.java` file submission supported.
- [x] Python syntax and Java structural validation return line-aware issues.
- [x] Knowledge documents are chunked, embedded, indexed, and retrievable.

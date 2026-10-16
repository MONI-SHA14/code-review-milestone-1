# AI Code Review & Security Analysis Agent

A simple, runnable Milestone 1 project with a basic developer website, Python/Java submission validation API, and secure-coding knowledge-base retrieval.

## What is included

The `index.html`, `styles.css`, and `app.js` files provide a simple code input website with a language dropdown, code box, Submit Code button, and results section. The `server.py` file serves the frontend and exposes `POST /api/review`. The `backend/src/code_review_agent` package contains the tested Python AST validator, Java structural validator, data models, and dependency-free RAG retrieval pipeline. The `knowledge_base` directory contains secure-coding guidance; `samples`, `tests`, `docs`, and `outputs` contain examples, tests, architecture notes, and demo artifacts.

## Run on Windows

Install Python 3.10 or newer, open PowerShell in this folder, and run:

```powershell
py server.py
```

Then open `http://localhost:3000` in a browser. The website is served by the same Python process as the API.

## Run on Linux/macOS

```bash
python3 server.py
```

Open `http://localhost:3000`.

## Run tests

Windows:

```powershell
py -m unittest discover -s tests -v
```

Linux/macOS:

```bash
python3 -m unittest discover -s tests -v
```

## API example

```powershell
$body = @{language="python"; source="print('hello')"} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:3000/api/review -Method Post -ContentType 'application/json' -Body $body
```

The API never executes submitted code. It validates Python using `ast.parse`, checks Java structure safely, scans a small set of security signals, and retrieves related secure-coding chunks.

## Milestone 1 scope

This project completes the Milestone 1 deliverables: foundation study, architecture and data-model design, Python/Java paste and file validation, and a chunked/embedded/vector-indexed secure-coding knowledge base. Full remediation generation, PR summaries, and conversational agent behavior are planned for later milestones.

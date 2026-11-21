from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .models import AnalysisResponse, ChatRequest, ChatResponse, CodeSubmission, Language
from .orchestration import REVIEWS, analyze, assistant_answer
from .reports import as_json, as_markdown, as_pdf

app = FastAPI(title="AI Code Review & Security Analysis Agent", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", encoding="utf-8") as handle:
        return handle.read()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ai-code-review-agent", "milestones": [1, 2, 3, 4]}


def run_analysis(submission: CodeSubmission):
    review, validation = analyze(submission)
    if not validation.valid:
        raise HTTPException(status_code=422, detail={"message": "Source validation failed", "errors": validation.errors, "line_count": validation.line_count})
    return AnalysisResponse(review=review, validation=validation.__dict__)


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_code(submission: CodeSubmission):
    return run_analysis(submission)


@app.post("/api/analyze/upload", response_model=AnalysisResponse)
async def analyze_upload(file: UploadFile = File(...)):
    name = file.filename or "source"
    extension = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    if extension not in {"py", "java"}:
        raise HTTPException(status_code=400, detail="Only .py and .java files are supported")
    code = (await file.read()).decode("utf-8", errors="replace")
    return run_analysis(CodeSubmission(language=Language.python if extension == "py" else Language.java, filename=name, code=code))


@app.get("/api/reviews/{review_id}")
def get_review(review_id: str):
    review = REVIEWS.get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@app.get("/api/reviews/{review_id}/export")
def export_review(review_id: str, format: str = "json"):
    review = REVIEWS.get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if format == "json":
        return Response(as_json(review), media_type="application/json", headers={"Content-Disposition": f"attachment; filename={review.submission.filename}.review.json"})
    if format == "markdown":
        return Response(as_markdown(review), media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename={review.submission.filename}.review.md"})
    if format == "pdf":
        return Response(as_pdf(review), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={review.submission.filename}.review.pdf"})
    raise HTTPException(status_code=400, detail="format must be json, markdown, or pdf")


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    answer, sources, matched = assistant_answer(request.question, request.review_id)
    return ChatResponse(answer=answer, sources=sources, matched_findings=matched)

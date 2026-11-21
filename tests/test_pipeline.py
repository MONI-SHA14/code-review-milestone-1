from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models import CodeSubmission, Language
from app.orchestration import analyze
from app.rag import KnowledgeBase

client = TestClient(app)
PY_SAMPLE = Path("samples/vulnerable.py").read_text()
JAVA_SAMPLE = Path("samples/VulnerableController.java").read_text()


def test_python_pipeline_detects_required_risks():
    review, validation = analyze(CodeSubmission(language=Language.python, filename="vulnerable.py", code=PY_SAMPLE))
    assert validation.valid
    titles = {f.title for f in review.findings}
    assert {"SQL injection", "Hardcoded secret", "Cross-site scripting (XSS)", "Missing CSRF protection"} <= titles
    assert review.summary.health_score < 100
    assert review.summary.severity_breakdown["high"] >= 2


def test_java_pipeline_detects_required_risks():
    review, validation = analyze(CodeSubmission(language=Language.java, filename="VulnerableController.java", code=JAVA_SAMPLE))
    assert validation.valid
    titles = {f.title for f in review.findings}
    assert {"SQL injection", "Hardcoded secret", "Cross-site scripting (XSS)"} <= titles


def test_rag_retrieves_grounded_sql_guidance():
    sources = [chunk.source for chunk in KnowledgeBase().retrieve("How do I prevent SQL injection with parameters?")]
    assert sources
    assert any("SQL" in source for source in sources)


def test_api_analysis_and_exports():
    response = client.post("/api/analyze", json={"language": "python", "filename": "demo.py", "code": "x = 1\nprint(x)"})
    assert response.status_code == 200
    review_id = response.json()["review"]["id"]
    assert client.get(f"/api/reviews/{review_id}/export?format=json").status_code == 200
    assert client.get(f"/api/reviews/{review_id}/export?format=markdown").status_code == 200
    assert client.get(f"/api/reviews/{review_id}/export?format=pdf").headers["content-type"].startswith("application/pdf")


def test_invalid_python_returns_validation_error():
    response = client.post("/api/analyze", json={"language": "python", "filename": "bad.py", "code": "def broken("})
    assert response.status_code == 422


def test_chat_is_grounded_and_matches_review_finding():
    response = client.post("/api/analyze", json={"language": "python", "filename": "demo.py", "code": "db.execute(f\"SELECT * FROM t WHERE id={user_id}\")"})
    review_id = response.json()["review"]["id"]
    chat = client.post("/api/chat", json={"question": "How do I fix the SQL injection?", "review_id": review_id})
    assert chat.status_code == 200
    assert "parameter" in chat.json()["answer"].lower()
    assert chat.json()["sources"]

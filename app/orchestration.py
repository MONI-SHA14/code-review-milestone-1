from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from .agents import CodeAnalysisAgent, ConversationalCodeAssistant, PRSummaryAgent, RemediationAgent, SecurityVulnerabilityAgent
from .analyzers import validate_source
from .models import CodeSubmission, Review, Severity, Summary
from .rag import KnowledgeBase

REVIEWS: dict[str, Review] = {}
LOCK = Lock()
KB = KnowledgeBase()


def run_in_parallel(submission: CodeSubmission):
    agents = [CodeAnalysisAgent(), SecurityVulnerabilityAgent()]
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="review-agent") as pool:
        futures = [pool.submit(agent.run, submission) for agent in agents]
        findings = [finding for future in futures for finding in future.result()]
    return findings


def build_summary(findings):
    breakdown = {severity.value: 0 for severity in Severity}
    for f in findings:
        breakdown[f.severity.value] += 1
    penalty = sum({Severity.critical: 30, Severity.high: 18, Severity.medium: 9, Severity.low: 3, Severity.info: 0}[f.severity] for f in findings)
    score = max(0, min(100, 100 - penalty))
    risk = "critical" if breakdown["critical"] else "high" if breakdown["high"] else "medium" if breakdown["medium"] else "low"
    return Summary(total_findings=len(findings), counts={"security": sum(f.category == "security" for f in findings), "code_quality": sum(f.category != "security" for f in findings)}, severity_breakdown=breakdown, health_score=score, risk_level=risk, top_risks=[f.title for f in sorted(findings, key=lambda f: -f.score)[:3]])


def analyze(submission: CodeSubmission):
    validation = validate_source(submission.language, submission.code)
    if not validation.valid:
        return None, validation
    findings = run_in_parallel(submission)
    findings = RemediationAgent().enrich(findings, KB)
    summary = build_summary(findings)
    pr_summary, roadmap = PRSummaryAgent().build(submission, findings, summary.health_score)
    review = Review(submission=submission, findings=findings, summary=summary, pr_summary=pr_summary, roadmap=roadmap)
    with LOCK:
        REVIEWS[review.id] = review
    return review, validation


def assistant_answer(question: str, review_id: str | None):
    review = REVIEWS.get(review_id) if review_id else None
    return ConversationalCodeAssistant(KB).answer(question, review.findings if review else [])

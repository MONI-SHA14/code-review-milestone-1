from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Language(str, Enum):
    python = "python"
    java = "java"


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class CodeSubmission(BaseModel):
    language: Language
    filename: str = "source"
    code: str = Field(min_length=1, max_length=200_000)


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: f"F-{uuid4().hex[:8].upper()}")
    agent: str
    category: str
    title: str
    description: str
    severity: Severity
    score: int = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    language: Language
    line_start: int = 1
    line_end: int = 1
    code_excerpt: str = ""
    owasp: str | None = None
    remediation: str = ""
    corrected_code: str = ""
    references: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Summary(BaseModel):
    total_findings: int
    counts: dict[str, int]
    severity_breakdown: dict[str, int]
    health_score: int = Field(ge=0, le=100)
    risk_level: str
    top_risks: list[str]


class Review(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    submission: CodeSubmission
    findings: list[Finding]
    summary: Summary
    pr_summary: str
    roadmap: list[str]


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    review_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    matched_findings: list[str]


class AnalysisResponse(BaseModel):
    review: Review
    validation: dict[str, Any]

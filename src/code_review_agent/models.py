from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class ValidationIssue:
    code: str
    message: str
    line: int | None = None
    column: int | None = None
    severity: str = "error"

@dataclass
class SubmissionResult:
    submission_id: str
    language: str
    source_name: str
    source_length: int
    valid: bool
    issues: list[ValidationIssue]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["issues"] = [asdict(i) for i in self.issues]
        return data

@dataclass
class KnowledgeChunk:
    chunk_id: str
    source: str
    title: str
    text: str
    terms: dict[str, float]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class RetrievalResult:
    chunk_id: str
    source: str
    title: str
    score: float
    text: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

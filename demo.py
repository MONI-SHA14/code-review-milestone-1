from pathlib import Path

from app.models import CodeSubmission, Language
from app.orchestration import analyze
from app.reports import as_markdown

for filename, language in [("samples/vulnerable.py", Language.python), ("samples/VulnerableController.java", Language.java)]:
    code = Path(filename).read_text()
    review, validation = analyze(CodeSubmission(language=language, filename=Path(filename).name, code=code))
    print(f"\n=== {filename} ===")
    print(f"valid={validation.valid} findings={review.summary.total_findings} health={review.summary.health_score}/100 risk={review.summary.risk_level}")
    for finding in sorted(review.findings, key=lambda item: (-item.score, item.line_start)):
        print(f"{finding.id} | {finding.severity.value.upper():8} | line {finding.line_start:>3} | {finding.title}")
    print("\n" + as_markdown(review)[:1000])

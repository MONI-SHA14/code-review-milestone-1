from __future__ import annotations

import io
import json
from textwrap import wrap

from .models import Review


def as_json(review: Review) -> str:
    return review.model_dump_json(indent=2)


def as_markdown(review: Review) -> str:
    lines = [f"# Code Review Report — {review.submission.filename}", "", f"- Review ID: `{review.id}`", f"- Language: `{review.submission.language.value}`", f"- Health score: **{review.summary.health_score}/100**", f"- Risk level: **{review.summary.risk_level}**", "", "## Severity breakdown", ""]
    lines += [f"- {key}: {value}" for key, value in review.summary.severity_breakdown.items()]
    lines += ["", "## Findings", ""]
    for f in review.findings:
        lines += [f"### {f.id}: {f.title}", f"- Severity: **{f.severity.value}** | Score: **{f.score}/10** | Lines: {f.line_start}-{f.line_end}", f"- OWASP: {f.owasp or 'N/A'}", f"- Description: {f.description}", f"- Remediation: {f.remediation}", "", "```", f.corrected_code, "```", ""]
    lines += ["## PR summary", "", review.pr_summary, "", "## Remediation roadmap", ""]
    lines += [f"1. {item}" for item in review.roadmap]
    return "\n".join(lines)


def as_pdf(review: Review) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from xml.sax.saxutils import escape
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("AI Code Review & Security Analysis Report", styles["Title"]), Paragraph(escape(review.submission.filename), styles["Heading2"]), Paragraph(f"Health score: {review.summary.health_score}/100 | Risk: {review.summary.risk_level}", styles["Normal"]), Spacer(1, 8)]
    story.append(Paragraph("Findings", styles["Heading2"]))
    for f in sorted(review.findings, key=lambda x: -x.score):
        text = f"<b>{escape(f.severity.value.upper())} — {escape(f.title)}</b> (line {f.line_start})<br/>{escape(f.description)}<br/><b>Remediation:</b> {escape(f.remediation)}"
        story += [Paragraph(text, styles["BodyText"]), Spacer(1, 6)]
    story.append(Paragraph("Remediation roadmap", styles["Heading2"]))
    for item in review.roadmap:
        story.append(Paragraph("• " + escape(item), styles["BodyText"]))
    doc.build(story)
    return buffer.getvalue()

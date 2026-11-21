from __future__ import annotations

import re
from typing import Iterable

from .analyzers import excerpt, line_of
from .models import CodeSubmission, Finding, Language, Severity
from .rag import KnowledgeBase


OWASP = "https://owasp.org/www-project-top-ten/"


def make_finding(submission: CodeSubmission, agent: str, category: str, title: str, description: str, severity: Severity, score: int, position: int, remediation: str, corrected_code: str, owasp: str | None = None, confidence: float = .95, references: list[str] | None = None) -> Finding:
    start = line_of(submission.code, position)
    return Finding(agent=agent, category=category, title=title, description=description, severity=severity, score=score, confidence=confidence, language=submission.language, line_start=start, line_end=start, code_excerpt=excerpt(submission.code, start), owasp=owasp, remediation=remediation, corrected_code=corrected_code, references=references or [OWASP] if owasp else references or [])


class CodeAnalysisAgent:
    name = "Code Analysis Agent"

    def run(self, submission: CodeSubmission) -> list[Finding]:
        code = submission.code
        findings: list[Finding] = []
        patterns = []
        if submission.language == Language.python:
            patterns = [
                (r"except\s*:\s*", "Bare exception handler", "Catching every exception hides programming errors and makes recovery unpredictable.", Severity.medium, 5, "Catch specific exception types and log safely.", "except ValueError as exc:\n    logger.warning(\"Invalid input: %s\", exc)"),
                (r"except\s+Exception\s*:", "Broad exception handler", "Catching Exception broadly can hide security and availability failures.", Severity.medium, 5, "Catch only expected exceptions and preserve useful diagnostics.", "except (ValueError, TypeError) as exc:\n    logger.warning(\"Bad request: %s\", exc)"),
                (r"\beval\s*\(", "Dynamic code execution", "eval makes code behavior difficult to reason about and is dangerous with untrusted input.", Severity.high, 8, "Replace eval with an explicit parser or allow-listed operation.", "operation = ALLOWED_OPERATIONS[user_value]"),
            ]
        else:
            patterns = [
                (r"catch\s*\(\s*Exception\s+\w+\s*\)", "Broad exception handler", "Catching Exception broadly can hide security and availability failures.", Severity.medium, 5, "Catch specific checked exceptions and handle each expected failure.", "catch (SQLException ex) { logger.error(\"Database failure\", ex); }"),
                (r"System\.out\.print", "Direct console logging", "Production code should use structured logging with appropriate redaction.", Severity.low, 2, "Use a structured logger and avoid sensitive values.", "logger.info(\"Request completed\");"),
            ]
        for pattern, title, desc, sev, score, fix, corrected in patterns:
            match = re.search(pattern, code, re.IGNORECASE | re.MULTILINE)
            if match:
                findings.append(make_finding(submission, self.name, "code_quality", title, desc, sev, score, match.start(), fix, corrected, confidence=.91))
        line_count = len(code.splitlines())
        branch_count = len(re.findall(r"\b(if|for|while|case|catch|except)\b", code))
        if branch_count >= 8 or line_count >= 80:
            position = re.search(r"\b(def|public|private|protected)\b", code)
            findings.append(make_finding(submission, self.name, "complexity", "High cyclomatic complexity", f"The submitted unit has approximately {branch_count + 1} decision points across {line_count} lines.", Severity.medium, 5, position.start() if position else 0, "Split the unit into small functions, reduce nesting, and test each branch independently.", "# Refactor into focused functions with one responsibility each.", confidence=.78))
        return findings


class SecurityVulnerabilityAgent:
    name = "Security Vulnerability Agent"

    def run(self, submission: CodeSubmission) -> list[Finding]:
        c = submission.code
        out: list[Finding] = []
        def add(pattern, title, desc, sev, score, fix, corrected, owasp, confidence=.95):
            match = re.search(pattern, c, re.IGNORECASE | re.MULTILINE)
            if match:
                out.append(make_finding(submission, self.name, "security", title, desc, sev, score, match.start(), fix, corrected, owasp, confidence))
        if submission.language == Language.python:
            add(r"(?:execute|executemany)\s*\(\s*f?[\"'].*(?:%|\{|\+)|f[\"'].*\bSELECT\b", "SQL injection", "User-controlled data is interpolated into a SQL statement, allowing an attacker to alter query semantics.", Severity.critical, 10, "Use a parameterized query and pass values separately.", "cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))", "A03:2021-Injection")
            add(r"(?:password|passwd|secret|api[_-]?key|token)\s*=\s*[\"'][^\"']+[\"']", "Hardcoded secret", "A credential-like value is embedded in source and can be exposed through source control or logs.", Severity.high, 8, "Read the value from a secret manager or environment and rotate the exposed secret.", "api_key = os.environ[\"API_KEY\"]", "A07:2021-Identification and Authentication Failures")
            add(r"(?:render_template_string|Markup|\.html\s*=|return\s+f?[\"'].*<.*\{)", "Cross-site scripting (XSS)", "Untrusted data is inserted into HTML without an obvious context-safe encoding step.", Severity.high, 8, "Use auto-escaped templates or textContent; never concatenate untrusted HTML.", "return render_template(\"profile.html\", name=name)", "A03:2021-Injection")
            add(r"(?:app\.route|@.*route).*methods\s*=\s*\[[^]]*(?:POST|PUT|PATCH|DELETE)", "Missing CSRF protection", "A state-changing browser endpoint is declared without a visible CSRF control.", Severity.high, 7, "Require a server-validated CSRF token for cookie-authenticated state changes.", "@csrf_protect\n@app.post(\"/transfer\")", "A01:2021-Broken Access Control", .88)
            add(r"\beval\s*\(|\bexec\s*\(", "Unsafe dynamic execution", "Dynamic execution can turn attacker-controlled input into executable code.", Severity.critical, 10, "Remove dynamic execution and use a strict parser or allow-list.", "value = json.loads(user_input)", "A03:2021-Injection")
        else:
            add(r"(?:Statement|createStatement)\b.*(?:executeQuery|executeUpdate)\s*\(.*\+", "SQL injection", "SQL is assembled with string concatenation, allowing input to change query semantics.", Severity.critical, 10, "Use PreparedStatement parameters.", "PreparedStatement ps = conn.prepareStatement(\"SELECT * FROM users WHERE id = ?\");\nps.setString(1, userId);", "A03:2021-Injection")
            add(r"Runtime\.getRuntime\(\)\.exec\s*\(.*\+", "OS command injection", "Untrusted input is concatenated into an operating-system command.", Severity.critical, 10, "Use a fixed command and an argument list with strict allow-list validation.", "new ProcessBuilder(\"/usr/bin/file\", safePath).start();", "A03:2021-Injection")
            add(r"(?:password|secret|apiKey|token)\s*=\s*\"[^\"]+\"", "Hardcoded secret", "A credential-like value is embedded in source.", Severity.high, 8, "Use a secret manager or protected environment variable and rotate the value.", "String apiKey = System.getenv(\"API_KEY\");", "A07:2021-Identification and Authentication Failures")
            add(r"response\.getWriter\(\)\.print\s*\(.*\+", "Cross-site scripting (XSS)", "Untrusted data is written directly into an HTTP response without context-aware encoding.", Severity.high, 8, "HTML-encode untrusted output or use a templating engine with auto-escaping.", "response.getWriter().print(HtmlUtils.htmlEscape(name));", "A03:2021-Injection")
            add(r"@(?:PostMapping|RequestMapping)\b", "CSRF review required", "A state-changing endpoint was found; cookie-authenticated applications must enforce CSRF protection.", Severity.medium, 6, "Enable framework CSRF protection and require a validated token.", "http.csrf(csrf -> csrf.csrfTokenRepository(repository));", "A01:2021-Broken Access Control", .74)
        return out


class RemediationAgent:
    name = "Remediation Agent"

    def enrich(self, findings: Iterable[Finding], kb: KnowledgeBase) -> list[Finding]:
        result = []
        for finding in findings:
            context = kb.retrieve(f"{finding.title} {finding.description}", top_k=3)
            finding.references = list(dict.fromkeys(finding.references + [c.source for c in context]))
            result.append(finding)
        return result


class PRSummaryAgent:
    def build(self, submission: CodeSubmission, findings: list[Finding], health_score: int) -> tuple[str, list[str]]:
        ordered = sorted(findings, key=lambda f: (-f.score, f.line_start))
        if not ordered:
            return "## Automated Code Review\n\nNo findings were detected by the configured rules. Continue with tests and manual review.", []
        lines = ["## Automated Code Review", "", f"**Language:** `{submission.language.value}`  ", f"**Health score:** `{health_score}/100`", "", "### Findings"]
        for f in ordered:
            lines.append(f"- **{f.severity.value.upper()} — {f.title}** (`{f.id}`, line {f.line_start}) — {f.remediation}")
        roadmap = [f"Fix {f.title} at line {f.line_start}; verify with a regression test." for f in ordered]
        lines += ["", "### Review decision", "Request changes until critical/high findings are fixed." if any(f.severity in {Severity.critical, Severity.high} for f in findings) else "Approve with suggested improvements."]
        return "\n".join(lines), roadmap


class ConversationalCodeAssistant:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def answer(self, question: str, findings: list[Finding] | None = None) -> tuple[str, list[str], list[str]]:
        findings = findings or []
        matched = [f for f in findings if any(term in (question.lower() + " " + f.title.lower()) for term in ["sql", "xss", "csrf", "secret", "access", "complex", "exception", "injection"])]
        chunks = self.kb.retrieve(question, top_k=3)
        if matched:
            f = matched[0]
            answer = f"**{f.title} ({f.severity.value})** at line {f.line_start}: {f.description}\n\n**Fix:** {f.remediation}\n\n**Example:**\n```{f.language.value}\n{f.corrected_code}\n```"
        elif chunks:
            answer = "Based on the secure-coding knowledge base:\n\n" + "\n\n".join(c.text for c in chunks[:2])
        else:
            answer = "I could not ground that question in the indexed secure-coding guidance. Ask about a finding, SQL injection, XSS, CSRF, secrets, authentication, authorization, or complexity."
        return answer, [c.source for c in chunks], [f.id for f in matched]

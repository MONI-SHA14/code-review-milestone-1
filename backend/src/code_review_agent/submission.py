import ast
import hashlib
import re
from pathlib import Path
from .models import SubmissionResult, ValidationIssue

MAX_SOURCE_BYTES = 512 * 1024
EXTENSIONS = {"python": {".py"}, "java": {".java"}}

def _id(language: str, name: str, source: str) -> str:
    return hashlib.sha256(f"{language}:{name}:{source}".encode()).hexdigest()[:16]

def validate_python(source: str) -> list[ValidationIssue]:
    try:
        ast.parse(source)
        return []
    except SyntaxError as exc:
        return [ValidationIssue("PYTHON_SYNTAX", exc.msg, exc.lineno, exc.offset)]

def _java_scan(source: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not re.search(r"\b(class|interface|enum)\s+[A-Za-z_$][\w$]*", source):
        issues.append(ValidationIssue("JAVA_NO_TYPE", "No class, interface, or enum declaration found."))
    stack: list[tuple[str, int, int]] = []
    in_string = False; escaped = False; in_line_comment = False; in_block_comment = False
    line, col = 1, 0; i = 0
    pairs = {"}": "{", "]": "[", ")": "("}
    while i < len(source):
        ch = source[i]; col += 1
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if ch == "\n": line += 1; col = 0; in_line_comment = False; i += 1; continue
        if in_line_comment: i += 1; continue
        if in_block_comment:
            if ch == "*" and nxt == "/": in_block_comment = False; i += 2; col += 1
            else: i += 1
            continue
        if not in_string and ch == "/" and nxt == "/": in_line_comment = True; i += 2; col += 1; continue
        if not in_string and ch == "/" and nxt == "*": in_block_comment = True; i += 2; col += 1; continue
        if ch == '"' and not escaped: in_string = not in_string
        if not in_string:
            if ch in "{[(": stack.append((ch, line, col))
            elif ch in "}])":
                if not stack or stack[-1][0] != pairs[ch]:
                    issues.append(ValidationIssue("JAVA_UNBALANCED", f"Unexpected '{ch}'.", line, col))
                else: stack.pop()
        escaped = (ch == "\\" and not escaped) if in_string else False
        i += 1
    if in_string: issues.append(ValidationIssue("JAVA_STRING", "Unterminated string literal.", line, col))
    if in_block_comment: issues.append(ValidationIssue("JAVA_COMMENT", "Unterminated block comment.", line, col))
    for opening, l, c in reversed(stack): issues.append(ValidationIssue("JAVA_UNBALANCED", f"Unclosed '{opening}'.", l, c))
    return issues

def validate_java(source: str) -> list[ValidationIssue]:
    return _java_scan(source)

def submit_source(source: str, language: str, source_name: str = "pasted_code") -> SubmissionResult:
    language = language.lower()
    issues: list[ValidationIssue] = []
    if language not in EXTENSIONS:
        issues.append(ValidationIssue("UNSUPPORTED_LANGUAGE", f"Supported languages: {', '.join(EXTENSIONS)}."))
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        issues.append(ValidationIssue("SOURCE_TOO_LARGE", f"Source exceeds {MAX_SOURCE_BYTES} bytes."))
    if not source.strip(): issues.append(ValidationIssue("EMPTY_SOURCE", "Source code is empty."))
    if not issues:
        issues = validate_python(source) if language == "python" else validate_java(source)
    return SubmissionResult(_id(language, source_name, source), language, source_name, len(source), not issues, issues)

def submit_file(path: str) -> SubmissionResult:
    p = Path(path)
    language = {".py": "python", ".java": "java"}.get(p.suffix.lower())
    if not language:
        return SubmissionResult(_id("unknown", p.name, ""), "unknown", p.name, 0, False, [ValidationIssue("UNSUPPORTED_EXTENSION", f"Use .py or .java, not {p.suffix or '(none)'}.")])
    try: source = p.read_text(encoding="utf-8")
    except UnicodeDecodeError: return SubmissionResult(_id(language, p.name, ""), language, p.name, 0, False, [ValidationIssue("INVALID_ENCODING", "File must be valid UTF-8.")])
    except OSError as exc: return SubmissionResult(_id(language, p.name, ""), language, p.name, 0, False, [ValidationIssue("FILE_READ", str(exc))])
    return submit_source(source, language, p.name)

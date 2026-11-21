from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from .models import Language


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    line_count: int
    detected_language: str


def validate_source(language: Language, code: str) -> ValidationResult:
    errors: list[str] = []
    if language == Language.python:
        try:
            ast.parse(code)
        except SyntaxError as exc:
            errors.append(f"Python syntax error at line {exc.lineno}: {exc.msg}")
    else:
        if not re.search(r"\b(class|interface|enum)\s+[A-Za-z_$][\w$]*", code):
            errors.append("Java validation: no class, interface, or enum declaration was found")
        if code.count("{") != code.count("}"):
            errors.append("Java validation: braces are unbalanced")
        if re.search(r"\bpublic\s+class\s+\w+", code) and not re.search(r"\bpublic\s+static\s+void\s+main\s*\(", code):
            # A class without main is valid Java; this is deliberately not an error.
            pass
    return ValidationResult(not errors, errors, len(code.splitlines()), language.value)


def line_of(code: str, position: int) -> int:
    return code.count("\n", 0, max(0, position)) + 1


def excerpt(code: str, line_start: int, line_end: int | None = None) -> str:
    lines = code.splitlines()
    end = line_end or line_start
    return "\n".join(lines[max(0, line_start - 1):end])[:1000]

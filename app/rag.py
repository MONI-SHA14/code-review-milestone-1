from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    topic: str
    text: str


CORPUS = [
    KnowledgeChunk("OWASP SQL Injection Prevention Cheat Sheet", "SQL injection", "Use parameterized queries or prepared statements. Never concatenate untrusted input into SQL. Validate inputs as defense in depth and use the least-privileged database account."),
    KnowledgeChunk("OWASP Cross Site Scripting Prevention Cheat Sheet", "XSS", "Contextually encode untrusted output. Prefer framework auto-escaping and safe DOM APIs such as textContent. Do not render raw HTML from user input."),
    KnowledgeChunk("OWASP Cross-Site Request Forgery Prevention Cheat Sheet", "CSRF", "State-changing browser requests need CSRF tokens or a strong same-site request policy. Validate the token server-side and do not rely on a cookie alone."),
    KnowledgeChunk("OWASP Secrets Management Cheat Sheet", "hardcoded secrets", "Never commit passwords, API keys, or tokens in source code. Load secrets from a secret manager or protected environment and rotate exposed credentials."),
    KnowledgeChunk("OWASP Authentication Cheat Sheet", "authentication", "Use a well-tested framework, strong password hashing, secure session cookies, MFA where appropriate, rate limiting, and server-side authorization checks."),
    KnowledgeChunk("OWASP Authorization Cheat Sheet", "access control", "Deny by default, enforce authorization on every request, and check object ownership server-side. Do not trust client-controlled roles or IDs."),
    KnowledgeChunk("Python Secure Coding Guidelines", "python", "Catch specific exceptions, avoid eval and exec on untrusted input, use subprocess argument lists with shell=False, and keep complexity low through small focused functions."),
    KnowledgeChunk("Java Secure Coding Guidelines", "java", "Use PreparedStatement for database queries, encode output for its context, avoid Runtime.exec with concatenated input, and apply explicit access checks."),
    KnowledgeChunk("OWASP Logging Cheat Sheet", "logging", "Log security-relevant events without passwords, tokens, or personal data. Use structured logs and protect log integrity."),
]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_+#-]+", text.lower())


class KnowledgeBase:
    def __init__(self, chunks: list[KnowledgeChunk] | None = None):
        self.chunks = chunks or CORPUS
        self.documents = [Counter(_tokens(c.text + " " + c.topic)) for c in self.chunks]
        self.df = Counter()
        for doc in self.documents:
            for term in doc:
                self.df[term] += 1

    def retrieve(self, query: str, top_k: int = 4) -> list[KnowledgeChunk]:
        q = Counter(_tokens(query))
        if not q:
            return []
        n = len(self.documents)
        scores: list[tuple[float, int]] = []
        for index, doc in enumerate(self.documents):
            score = 0.0
            for term, count in q.items():
                if term in doc:
                    idf = math.log((1 + n) / (1 + self.df[term])) + 1
                    score += (1 + math.log(count)) * (1 + math.log(doc[term])) * idf
            if score:
                scores.append((score, index))
        scores.sort(reverse=True)
        return [self.chunks[i] for _, i in scores[:top_k]]

    def explain(self, query: str, top_k: int = 4) -> list[dict[str, str]]:
        return [{"source": c.source, "topic": c.topic, "text": c.text} for c in self.retrieve(query, top_k)]

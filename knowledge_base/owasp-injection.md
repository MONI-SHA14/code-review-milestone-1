# OWASP Injection Prevention

Injection occurs when untrusted data is interpreted as part of a command or query. SQL injection is prevented by parameterized queries or prepared statements. Bind values as parameters rather than concatenating strings. Validate types and ranges, use least-privilege database accounts, and avoid returning verbose database errors to users. For command injection, prefer safe library APIs over shell execution and use allowlists. Evidence should include the constructed query and the untrusted data flow, never the secret value.

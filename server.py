from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'backend'))
from src.code_review_agent.submission import submit_source
from src.code_review_agent.knowledge_base import KnowledgeBase

KB = KnowledgeBase(str(ROOT / 'knowledge_base'), str(ROOT / 'outputs' / 'vector_store.json'))
if not KB.index_path.exists():
    KB.build()
else:
    KB.load()

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_POST(self):
        if self.path != '/api/review':
            self.send_error(404, 'API route not found')
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 600_000:
                raise ValueError('Request body is too large.')
            body = json.loads(self.rfile.read(length).decode('utf-8'))
            language = str(body.get('language', '')).lower()
            source = str(body.get('source', ''))
            result = submit_source(source, language, 'pasted_code')
            security = []
            for line_no, line in enumerate(source.splitlines(), 1):
                if any(word in line.upper() for word in ('SELECT', 'INSERT', 'UPDATE', 'DELETE')) and ('+' in line or 'f"' in line or "f'" in line):
                    security.append({'line': line_no, 'code': 'SQL_INJECTION_SIGNAL', 'severity': 'high', 'message': 'Possible SQL injection: use parameterized queries instead of string concatenation.'})
                if any(word in line.lower() for word in ('password', 'api_key', 'apikey', 'secret', 'token')) and '=' in line and ('"' in line or "'" in line):
                    security.append({'line': line_no, 'code': 'HARDCODED_SECRET_SIGNAL', 'severity': 'high', 'message': 'Possible hardcoded secret: use a secret manager or protected environment configuration.'})
                if 'innerHTML' in line or 'document.write' in line:
                    security.append({'line': line_no, 'code': 'XSS_SIGNAL', 'severity': 'medium', 'message': 'Potential XSS sink: use safe DOM APIs or context-aware output encoding.'})
            hits = [hit.to_dict() for hit in KB.query(source or language, 3)]
            payload = {'submission': result.to_dict(), 'security_signals': security, 'knowledge': hits}
            self.send_json(200, payload)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {'error': str(exc)})
        except Exception as exc:
            self.send_json(500, {'error': 'Review failed', 'detail': str(exc)})

    def send_json(self, status, payload):
        raw = json.dumps(payload, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

if __name__ == '__main__':
    os.chdir(ROOT)
    port = int(os.environ.get('PORT', '3000'))
    print(f'Sentinel Review running at http://localhost:{port}')
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()

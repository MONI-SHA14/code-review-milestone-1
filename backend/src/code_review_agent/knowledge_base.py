import json, math, re
from pathlib import Path
from .models import KnowledgeChunk, RetrievalResult

TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{1,}")
STOP = {"the","and","for","with","that","this","from","into","are","use","should","must","when","then","not","your","you","can","by","of","to","in","a","an","is","on"}

def tokens(text: str) -> list[str]: return [t.lower() for t in TOKEN.findall(text) if t.lower() not in STOP]
def embed(text: str) -> dict[str, float]:
    counts: dict[str, float] = {}
    for t in tokens(text): counts[t] = counts.get(t, 0.0) + 1.0
    norm = math.sqrt(sum(v*v for v in counts.values())) or 1.0
    return {k: round(v/norm, 6) for k,v in counts.items()}
def cosine(a: dict[str,float], b: dict[str,float]) -> float: return sum(a.get(k,0.0)*v for k,v in b.items())

def chunk_markdown(path: Path, max_words: int = 120, overlap: int = 20) -> list[KnowledgeChunk]:
    text = path.read_text(encoding="utf-8"); title = path.stem.replace("-", " ").title(); words = text.split(); result=[]; start=0; idx=0
    while start < len(words):
        end = min(len(words), start + max_words); body = " ".join(words[start:end])
        cid = f"{path.name}:{idx}"
        result.append(KnowledgeChunk(cid, path.name, title, body, embed(body), {"word_start":start,"word_end":end}))
        if end == len(words): break
        start = max(end - overlap, start + 1); idx += 1
    return result

class KnowledgeBase:
    def __init__(self, directory: str, index_path: str): self.directory=Path(directory); self.index_path=Path(index_path); self.chunks=[]
    def build(self) -> dict:
        self.chunks = [c for p in sorted(self.directory.glob("*.md")) for c in chunk_markdown(p)]
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        payload={"version":1,"embedding":"normalized-term-frequency","chunks":[c.to_dict() for c in self.chunks]}
        self.index_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {"sources":len(list(self.directory.glob("*.md"))),"chunks":len(self.chunks),"index":str(self.index_path)}
    def load(self):
        payload=json.loads(self.index_path.read_text(encoding="utf-8")); self.chunks=[KnowledgeChunk(**c) for c in payload["chunks"]]; return self
    def query(self, question: str, top_k: int = 3) -> list[RetrievalResult]:
        q=embed(question); ranked=sorted(((cosine(q,c.terms),c) for c in self.chunks), key=lambda x:x[0], reverse=True)
        return [RetrievalResult(c.chunk_id,c.source,c.title,round(score,4),c.text,c.metadata) for score,c in ranked[:top_k] if score > 0]

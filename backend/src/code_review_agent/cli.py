import argparse, json
from pathlib import Path
from .submission import submit_file, submit_source
from .knowledge_base import KnowledgeBase

ROOT=Path(__file__).resolve().parents[2]; KB=ROOT/'knowledge_base'; OUT=ROOT/'outputs'; INDEX=OUT/'vector_store.json'
def dump(obj, path): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(obj,indent=2),encoding='utf-8'); print(json.dumps(obj,indent=2))
def main():
    ap=argparse.ArgumentParser(description='AI Code Review Agent — Milestone 1')
    sub=ap.add_subparsers(dest='cmd',required=True)
    v=sub.add_parser('validate'); v.add_argument('--file'); v.add_argument('--language',choices=['python','java']); v.add_argument('--code'); v.add_argument('--output')
    sub.add_parser('index-kb'); q=sub.add_parser('query'); q.add_argument('question'); q.add_argument('--top-k',type=int,default=3)
    sub.add_parser('demo'); args=ap.parse_args()
    if args.cmd=='validate':
        r=submit_file(args.file) if args.file else submit_source(args.code or '',args.language or 'python','pasted_code'); data=r.to_dict(); dump(data,Path(args.output) if args.output else OUT/(r.language+'_submission.json'))
    elif args.cmd=='index-kb': print(json.dumps(KnowledgeBase(str(KB),str(INDEX)).build(),indent=2))
    elif args.cmd=='query':
        kb=KnowledgeBase(str(KB),str(INDEX)); kb.load() if INDEX.exists() else kb.build(); data=[x.to_dict() for x in kb.query(args.question,args.top_k)]; dump(data,OUT/'knowledge_query.json')
    else:
        py=submit_file(str(ROOT/'samples/vulnerable.py')); ja=submit_file(str(ROOT/'samples/Hello.java')); kb=KnowledgeBase(str(KB),str(INDEX)); stats=kb.build(); hits=kb.query('How should SQL queries be parameterized and how are secrets protected?',3)
        dump(py.to_dict(),OUT/'python_submission.json'); dump(ja.to_dict(),OUT/'java_submission.json'); dump([h.to_dict() for h in hits],OUT/'knowledge_query.json')
        report=f'''# Milestone 1 Demo Report\n\n## Code submission\n\n- Python `{py.source_name}`: **{"valid" if py.valid else "invalid"}** ({len(py.issues)} issue(s))\n- Java `{ja.source_name}`: **{"valid" if ja.valid else "invalid"}** ({len(ja.issues)} issue(s))\n\n## Knowledge base\n\nIndexed **{stats["sources"]}** Markdown sources into **{stats["chunks"]}** chunks. Query returned **{len(hits)}** relevant chunks.\n\n## Reproducibility\n\nRun `python3 -m src.code_review_agent.cli demo` to regenerate these files. Submitted code is never executed.\n'''; (OUT/'demo_report.md').write_text(report,encoding='utf-8'); print(report)
if __name__=='__main__': main()

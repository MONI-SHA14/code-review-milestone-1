import json, tempfile, unittest
from pathlib import Path
from src.code_review_agent.submission import submit_source
from src.code_review_agent.knowledge_base import KnowledgeBase

class Milestone1Tests(unittest.TestCase):
    def test_python_syntax_error_is_line_aware(self):
        r=submit_source('def broken(:\n  pass\n','python','x.py')
        self.assertFalse(r.valid); self.assertEqual(r.issues[0].code,'PYTHON_SYNTAX'); self.assertIsNotNone(r.issues[0].line)
    def test_java_balanced_structure(self):
        self.assertTrue(submit_source('public class X {}','java','X.java').valid)
        self.assertFalse(submit_source('public class X {','java','X.java').valid)
    def test_kb_indexes_and_retrieves(self):
        with tempfile.TemporaryDirectory() as d:
            kbdir=Path(d)/'kb'; kbdir.mkdir(); (kbdir/'a.md').write_text('# SQL\nUse parameterized prepared statements for SQL queries.',encoding='utf8')
            index=Path(d)/'index.json'; kb=KnowledgeBase(str(kbdir),str(index)); stats=kb.build(); self.assertEqual(stats['chunks'],1)
            hits=kb.load().query('parameterized SQL query',1); self.assertEqual(len(hits),1); self.assertIn('prepared',hits[0].text)

if __name__=='__main__': unittest.main()

import unittest
from contextatlas.engine import analyze,tokenize,token_cost,bm25
class EngineTests(unittest.TestCase):
    def setUp(self):
        self.docs=[{"id":"one","text":"Aurora retrieval is evaluated using recall and citation coverage."},{"id":"two","text":"Cooking with lentils is easy."},{"id":"three","text":"Aurora citation coverage must exceed ninety percent."}]
    def test_tokenizer(self):self.assertIn("aurora",tokenize("The Aurora retrieval"))
    def test_token_count(self):self.assertEqual(token_cost("Hi, world!"),4)
    def test_bm25(self):self.assertGreater(bm25(["aurora"],[['aurora'],['lentils']])[0],0)
    def test_budget(self):
        r=analyze("Aurora citations",self.docs,budget=12)
        self.assertLessEqual(r['optimized_metrics']['tokens'],12)
    def test_no_oversize(self):self.assertEqual(analyze("Aurora",self.docs,budget=1)['selected'],[])
    def test_relevance(self):self.assertNotIn('two',[d['id'] for d in analyze('Aurora',self.docs,budget=40)['selected']])
    def test_determinism(self):self.assertEqual(analyze('Aurora',self.docs),analyze('Aurora',self.docs))
    def test_empty_query(self):
        with self.assertRaises(ValueError):analyze('',self.docs)
    def test_bad_budget(self):
        with self.assertRaises(ValueError):analyze('hello',self.docs,budget=0)
    def test_bad_diversity(self):
        with self.assertRaises(ValueError):analyze('hello',self.docs,diversity=1.1)
    def test_bad_doc(self):
        with self.assertRaises(ValueError):analyze('hello',[{'not_text':'x'}])
    def test_duplicate_ids_not_required(self):self.assertEqual(len(analyze('Aurora',['Aurora doc','Other'])['all_chunks']),2)
if __name__=='__main__':unittest.main()

import unittest

from nlp_engine import NLPEngine


class SpellingDictionaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = NLPEngine()

    def test_valid_boutique_is_known(self):
        self.assertTrue(self.engine.is_known("boutique"))

    def test_boutique_typo_gets_dictionary_candidate(self):
        self.assertIn("boutique", self.engine.get_corrections("boutiqe"))


if __name__ == "__main__":
    unittest.main()
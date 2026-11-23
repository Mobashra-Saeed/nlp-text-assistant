import unittest
from unittest.mock import patch

from nlp_engine import NLPEngine


class SpellingDictionaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = NLPEngine()

    def test_valid_boutique_is_known(self):
        self.assertTrue(self.engine.is_known("boutique"))

    def test_boutique_typo_gets_dictionary_candidate(self):
        self.assertIn("boutique", self.engine.get_corrections("boutiqe"))

    def test_engine_can_start_without_brown_corpus(self):
        with patch("nlp_engine.brown.words", side_effect=LookupError):
            with patch.dict("os.environ", {"NLTK_DOWNLOAD_BROWN": "0"}):
                engine = NLPEngine()

        self.assertEqual(engine.total_words, 0)
        self.assertTrue(engine.is_known("boutique"))
        self.assertIn("boutique", engine.get_corrections("boutiqe"))
        self.assertTrue(engine.autocomplete("bout"))


if __name__ == "__main__":
    unittest.main()
import unittest
from pathlib import Path
from unittest.mock import patch

from api_aggregator import APIAggregator
from context_rules import find_context_matches


class KnownWordStub:
    def is_known(self, word):
        return True


class ContextRuleTests(unittest.TestCase):
    def test_sore_in_shopping_context_suggests_store(self):
        text = "My friend and I are going to the sore for grocery."
        matches = find_context_matches(text)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["word"], "sore")
        self.assertEqual(matches[0]["suggestions"], ["store"])

    def test_boutique_without_article_suggests_article(self):
        text = "We can go together to boutique for shopping."
        matches = find_context_matches(text)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["word"], "boutique")
        self.assertEqual(matches[0]["suggestions"], ["a boutique"])

    def test_legitimate_sore_and_boutique_are_not_flagged(self):
        text = "She has a sore throat, and we went to the boutique for shopping."

        self.assertEqual(find_context_matches(text), [])

    def test_context_matches_are_returned_by_text_checker(self):
        aggregator = APIAggregator(KnownWordStub())
        with patch.object(aggregator, "_fetch_languagetool", return_value=[]):
            result = aggregator.process_text(
                "We can go together to boutique for shopping."
            )

        self.assertEqual(result["matches"][0]["suggestions"], ["a boutique"])

    def test_disabled_languagetool_does_not_make_network_request(self):
        aggregator = APIAggregator(KnownWordStub())
        with patch.dict("os.environ", {"DISABLE_LANGUAGETOOL": "1"}):
            with patch("api_aggregator.requests.post") as post_request:
                self.assertEqual(aggregator._fetch_languagetool("A sentence."), [])

        post_request.assert_not_called()

    def test_context_benchmark_passes_all_examples(self):
        benchmark_path = Path(__file__).resolve().parent.parent / "benchmark_context.csv"
        metrics = APIAggregator.evaluate_context_benchmark(benchmark_path)

        self.assertEqual(metrics["total_cases"], 4)
        self.assertEqual(metrics["true_positives"], 2)
        self.assertEqual(metrics["true_negatives"], 2)
        self.assertEqual(metrics["false_positives"], 0)
        self.assertEqual(metrics["false_negatives"], 0)


if __name__ == "__main__":
    unittest.main()
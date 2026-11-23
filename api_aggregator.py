import csv
import os
import re
import requests
from context_rules import find_context_matches
from nlp_engine import NLPEngine

class APIAggregator:
    def __init__(self, nlp_engine: NLPEngine):
        self.engine = nlp_engine
        self.lt_url = "https://api.languagetool.org/v2/check"

    def process_text(self, text):
        """
        Aggregates custom structural spellchecker with LanguageTool contextual API.
        """
        if not text.strip():
            return {"text": text, "matches": []}

        matches = []
        
        # 1. Fetch LanguageTool Context/Grammar matches
        lt_matches = self._fetch_languagetool(text)
        covered_spans = set()

        for match in lt_matches:
            offset = match['offset']
            length = match['length']
            for i in range(offset, offset + length):
                covered_spans.add(i)
            
            matches.append({
                "offset": offset,
                "length": length,
                "word": text[offset:offset + length],
                "type": "grammar" if match['rule']['category']['id'] != "TYPOS" else "spelling",
                "message": match['message'],
                "suggestions": [r['value'] for r in match['replacements'][:5]]
            })

        for match in find_context_matches(text):
            start = match['offset']
            end = start + match['length']
            if any(index in covered_spans for index in range(start, end)):
                continue
            matches.append(match)
            covered_spans.update(range(start, end))

        # 2. Extract words and check with custom NLP Engine (avoiding duplicate spans)
        word_iter = re.finditer(r'\b[a-zA-Z]+\b', text)
        for match_obj in word_iter:
            word = match_obj.group(0)
            start = match_obj.start()
            end = match_obj.end()

            # Skip if LanguageTool already flagged this span
            if any(idx in covered_spans for idx in range(start, end)):
                continue

            if not self.engine.is_known(word):
                suggestions = self.engine.get_corrections(word, top_n=5)
                matches.append({
                    "offset": start,
                    "length": len(word),
                    "word": word,
                    "type": "spelling",
                    "message": f"Possible spelling mistake: '{word}'",
                    "suggestions": suggestions
                })

        # Sort matches by character position
        matches.sort(key=lambda x: x['offset'])
        return {"text": text, "matches": matches}

    @staticmethod
    def evaluate_context_benchmark(csv_filepath):
        """Score the small local context-rule suite without calling external APIs."""
        required_columns = {"text", "expected_word", "expected_suggestion"}
        tp = fp = fn = tn = total_cases = 0

        with open(csv_filepath, mode='r', encoding='utf-8') as benchmark_file:
            reader = csv.DictReader(benchmark_file)
            if not required_columns.issubset(reader.fieldnames or []):
                raise ValueError(
                    "Context benchmark CSV must contain text, expected_word, and expected_suggestion columns"
                )

            for row in reader:
                text = (row.get('text') or '').strip()
                if not text:
                    raise ValueError(f"Context benchmark CSV has empty text on line {reader.line_num}")

                total_cases += 1
                expected_word = (row.get('expected_word') or '').strip().lower()
                expected_suggestion = (row.get('expected_suggestion') or '').strip().lower()
                matches = find_context_matches(text)

                if expected_word and expected_suggestion:
                    found = any(
                        match['word'].lower() == expected_word
                        and expected_suggestion in [item.lower() for item in match['suggestions']]
                        for match in matches
                    )
                    if found:
                        tp += 1
                    else:
                        fn += 1
                elif matches:
                    fp += 1
                else:
                    tn += 1

        accuracy = (tp + tn) / total_cases if total_cases else 0
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1_score = 2 * precision * recall / (precision + recall) if precision + recall else 0
        return {
            "total_cases": total_cases,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4),
        }

    def _fetch_languagetool(self, text):
        if os.environ.get('DISABLE_LANGUAGETOOL', '').lower() in {'1', 'true', 'yes'}:
            return []

        try:
            response = requests.post(
                self.lt_url,
                data={"text": text, "language": "en-US"},
                timeout=3.0
            )
            if response.status_code == 200:
                return response.json().get('matches', [])
        except requests.RequestException:
            pass
        return []
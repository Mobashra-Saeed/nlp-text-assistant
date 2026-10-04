import csv
import math
import os
import re
import time
from collections import defaultdict
import nltk
from nltk.corpus import brown
from spellchecker import SpellChecker

# Download required corpus silently on startup
try:
    nltk.data.find('corpora/brown')
except LookupError:
    nltk.download('brown', quiet=True)

class NLPEngine:
    def __init__(self):
        self.spell_checker = SpellChecker(language='en')
        self.dictionary_vocabulary = {
            word.lower() for word in self.spell_checker.word_frequency.words()
        }
        custom_words_path = os.path.join(os.path.dirname(__file__), 'custom_words.txt')
        if os.path.isfile(custom_words_path):
            with open(custom_words_path, encoding='utf-8') as custom_words_file:
                self.custom_vocabulary = {
                    word.strip().lower()
                    for word in custom_words_file
                    if word.strip() and not word.lstrip().startswith('#')
                }
        else:
            self.custom_vocabulary = set()
        self.vocabulary = set()
        self.word_counts = defaultdict(int)
        self.word_probs = {}
        self.length_to_words = defaultdict(set)
        self.total_words = 0
        self._build_corpus()

    def _build_corpus(self):
        """Builds vocabulary and unigram distribution from NLTK Brown Corpus."""
        raw_words = brown.words()
        for word in raw_words:
            clean_word = word.lower()
            if re.match(r'^[a-z]+$', clean_word):
                self.word_counts[clean_word] += 1
                self.total_words += 1

        self.vocabulary = set(self.word_counts.keys())
        
        for word, count in self.word_counts.items():
            self.word_probs[word] = count / self.total_words
            self.length_to_words[len(word)].add(word)

    @staticmethod
    def soundex(word):
        """Generates Soundex code for phonetic matching."""
        word = word.upper()
        if not word:
            return ""
        
        mapping = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6'
        }
        
        code = [word[0]]
        for char in word[1:]:
            digit = mapping.get(char, '0')
            if digit != '0' and digit != code[-1]:
                code.append(digit)
        
        soundex_str = "".join([c for c in code if c != '0'])
        return (soundex_str + "000")[:4]

    @staticmethod
    def get_bigrams(word):
        """Returns character bigrams for a word."""
        return set(word[i:i+2] for i in range(len(word)-1))

    def bigram_similarity(self, w1, w2):
        """Calculates Dice coefficient for character bigram similarity."""
        bg1, bg2 = self.get_bigrams(w1), self.get_bigrams(w2)
        if not bg1 or not bg2:
            return 0.0
        intersection = bg1.intersection(bg2)
        return (2.0 * len(intersection)) / (len(bg1) + len(bg2))

    def get_edits_one(self, word):
        """Generates all candidates 1 edit distance away."""
        letters = 'abcdefghijklmnopqrstuvwxyz'
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def get_edits_two(self, word):
        """Generates all candidates 2 edit distances away."""
        return set(e2 for e1 in self.get_edits_one(word) for e2 in self.get_edits_one(e1))

    def is_known(self, word):
        """Returns True if word is in Brown or the English spelling dictionary."""
        normalized = word.lower()
        return (
            normalized in self.vocabulary
            or normalized in self.dictionary_vocabulary
            or normalized in self.custom_vocabulary
        )

    def get_corrections(self, word, top_n=5):
        """
        Multi-model synthesis engine combining Levenshtein edits, 
        Soundex phonetics, and Bigram similarity weighted by Unigram probability.
        """
        word = word.lower()
        if self.is_known(word):
            return [word]

        candidates = set()
        
        # 1. Edit Distance 1 & 2 Filtered
        e1 = self.get_edits_one(word)
        e2 = self.get_edits_two(word)
        known_e1 = {w for w in e1 if w in self.dictionary_vocabulary or w in self.vocabulary}
        known_e2 = {w for w in e2 if w in self.dictionary_vocabulary or w in self.vocabulary}
        candidates.update(known_e1)
        candidates.update(known_e2)

        # 2. Phonetic Soundex Matching within length window ± 2
        target_soundex = self.soundex(word)
        length_window = range(max(1, len(word) - 2), len(word) + 3)
        
        for w_len in length_window:
            for w in self.length_to_words[w_len]:
                if self.soundex(w) == target_soundex:
                    candidates.add(w)

        if not candidates:
            return []

        # 3. Composite Scoring Model
        scored = []
        for candidate in candidates:
            bigram_score = self.bigram_similarity(word, candidate)
            probability = self.word_probs.get(candidate)
            if probability is None:
                word_frequency = self.spell_checker.word_frequency
                count = word_frequency.dictionary.get(candidate, 0)
                probability = count / word_frequency.total_words if word_frequency.total_words else 0
            prob_score = math.log(probability or 1e-7)
            edit_dist = 1 if candidate in known_e1 else (2 if candidate in known_e2 else 3)
            
            # Weighted rank formula
            score = (bigram_score * 4.0) + (prob_score * 0.2) - (edit_dist * 1.5)
            scored.append((candidate, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored[:top_n]]

    def autocomplete(self, prefix, top_n=5):
        """Returns top unigram completions for a given prefix."""
        prefix = prefix.lower()
        if not prefix:
            return []
        
        matches = [w for w in self.vocabulary if w.startswith(prefix)]
        matches.sort(key=lambda w: self.word_probs[w], reverse=True)
        return matches[:top_n]

    def evaluate_benchmark(self, csv_filepath):
        """
        Evaluate typo detection and correction against labeled word pairs.
        Classification metrics measure whether a word is changed; top-k hit
        rates measure whether the expected correction appears in suggestions.
        """
        start_time = time.time()
        tp, fp, fn, tn = 0, 0, 0, 0
        total_cases = 0
        correct_top1 = 0
        correct_top5 = 0
        required_columns = {"misspelled_word", "correct_target"}

        with open(csv_filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not required_columns.issubset(reader.fieldnames or []):
                raise ValueError(
                    "Benchmark CSV must contain misspelled_word and correct_target columns"
                )

            for row in reader:
                line_number = reader.line_num
                if not row.get("misspelled_word") or not row.get("correct_target"):
                    raise ValueError(f"Benchmark CSV has an empty value on line {line_number}")

                misspelled = row['misspelled_word'].strip().lower()
                correct_target = row['correct_target'].strip().lower()
                if not misspelled or not correct_target:
                    raise ValueError(f"Benchmark CSV has an empty value on line {line_number}")

                total_cases += 1

                suggestions = self.get_corrections(misspelled, top_n=5)
                predicted_word = suggestions[0] if suggestions else misspelled
                actual_typo = misspelled != correct_target
                predicted_typo = predicted_word != misspelled

                if correct_target == predicted_word:
                    correct_top1 += 1
                if correct_target in suggestions:
                    correct_top5 += 1

                if actual_typo and predicted_typo:
                    tp += 1
                elif predicted_typo:
                    fp += 1
                elif actual_typo:
                    fn += 1
                else:
                    tn += 1

        exec_time = round(time.time() - start_time, 3)
        accuracy = round((tp + tn) / total_cases, 4) if total_cases > 0 else 0
        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0
        f1_score = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0

        return {
            "total_words": total_cases,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "correct_top1": correct_top1,
            "correct_top5": correct_top5,
            "correction_accuracy_top1": round(correct_top1 / total_cases, 4) if total_cases > 0 else 0,
            "correction_accuracy_top5": round(correct_top5 / total_cases, 4) if total_cases > 0 else 0,
            "execution_time_seconds": exec_time
        }
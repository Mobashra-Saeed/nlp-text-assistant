# NLP Text Assistant

NLP Text Assistant is a small English-language web app for checking spelling and selected grammar or word-choice issues. Type in the editor to see findings, review suggestions, and apply corrections. The app also offers word autocomplete and a benchmark view. Checks are delayed briefly after typing pauses to avoid sending a request for every keystroke.

## What it does

Spelling suggestions come from an English dictionary and candidate ranking based on character edits, phonetic similarity, letter patterns, and word frequency. LanguageTool checks grammar and spelling through its public API. When enabled, the full text is sent to that external service. A few local rules cover specific context patterns, such as “to the sore for grocery.”

This is a lightweight rule-and-dictionary assistant, not a trained AI model or a general-purpose grammar checker. Suggestions can be wrong, so review them before applying.

## Run locally on Windows

From the repository root, open PowerShell and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r nlp-text-assistant\requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. On first startup, NLTK may download the Brown Corpus for word-frequency ranking. The app can still use its spelling dictionary if that corpus is unavailable.

To keep text from being sent to LanguageTool, disable the external check before starting the app:

```powershell
$env:DISABLE_LANGUAGETOOL = "1"
python app.py
```

Local spelling checks and the app’s narrow context rules will still run.

## Evaluation

The benchmark page evaluates spelling detection and correction against `benchmark_500.csv`, which contains 730 labeled word pairs despite its legacy filename. It reports accuracy, precision, recall, F1, and whether the expected correction appears in the top one or five suggestions. It also runs four small, hand-written checks for the local context rules. These datasets are useful for project-level checks, not a measure of performance on all writing.

Run the automated tests from the repository root with:

```powershell
python -m unittest discover -s tests
```

## Project layout

`app.py`, `nlp_engine.py`, `api_aggregator.py`, and `context_rules.py` contain the Flask backend and text-checking logic. `nlp-text-assistant` contains the browser interface, its launcher, and Python requirements. The benchmark CSV files and automated tests are at the repository root.

To allow names or specialist terms, add one accepted word per line to a root-level `custom_words.txt`. Restart the app after editing the file.

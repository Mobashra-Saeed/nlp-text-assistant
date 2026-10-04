# NLP Text Assistant

This folder contains the web interface and launcher. The Flask backend (`app.py`, `nlp_engine.py`, and `api_aggregator.py`) and labeled benchmark CSV (`benchmark_500.csv`) are in the parent folder.

## Windows setup

Open PowerShell in this folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

The first start downloads the NLTK Brown corpus if it is not already installed, so it needs an internet connection. Then open <http://127.0.0.1:5000>.

If PowerShell blocks virtual-environment activation, run the interpreter and pip directly instead:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Use

- In **Live Editor**, type or paste text. Spelling and LanguageTool findings appear after a short pause; click an underline to inspect suggestions.
- In **Spelling Benchmark**, choose **Run Model Evaluation**. The benchmark reads `../benchmark_500.csv`.
- Detection accuracy, precision, recall, and F1 score whether the engine flags typo rows while leaving identity rows unchanged. Top-1 and top-5 correction accuracy report whether the expected target is the first suggestion or anywhere in the first five.
- The same evaluation also runs `../benchmark_context.csv`, a small targeted suite for shopping-context word choice and a missing article before “boutique”.
- The Brown corpus supplies word-frequency ranking; the bundled English dictionary determines whether a word is valid. To allow project-specific names or terms, create `../custom_words.txt` and add one accepted word per line.

The CSV currently contains 730 labeled rows (56 typo pairs and 674 identity pairs), despite the legacy filename `benchmark_500.csv`.

## Free public deployment (Render)

The workspace root contains `render.yaml`, which configures a free Render web service. Render builds from the repository root, installs `nlp-text-assistant/requirements.txt`, and starts the root Flask app with Gunicorn.

1. Create a GitHub repository containing only this app's deployment files: root `app.py`, `api_aggregator.py`, `context_rules.py`, `nlp_engine.py`, `benchmark_500.csv`, `benchmark_context.csv`, `render.yaml`, and the `nlp-text-assistant` folder. Do not upload either virtual-environment folder or the separate `Autocorrector_Project` folder.
2. In Render, choose **New > Blueprint**, connect that GitHub repository, and approve the `nlp-text-assistant` service described by `render.yaml`.
3. Wait for the build and first startup to finish, then use the `.onrender.com` URL shown for the service.

Render's free web service may spin down when idle, so its first request after inactivity can be slow. The app downloads the NLTK Brown corpus at startup if it is not available in the instance. Live grammar checking also sends text to the external LanguageTool service.
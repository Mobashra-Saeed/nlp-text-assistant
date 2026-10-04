import os
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from api_aggregator import APIAggregator
from nlp_engine import NLPEngine

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(PROJECT_DIR, 'nlp-text-assistant')

app = Flask(
    __name__,
    template_folder=os.path.join(UI_DIR, 'templates'),
    static_folder=os.path.join(UI_DIR, 'static')
)
CORS(app)

# Initialize engines on startup
nlp_engine = NLPEngine()
aggregator = APIAggregator(nlp_engine)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check-text', methods=['POST'])
def check_text():
    data = request.get_json() or {}
    text = data.get('text', '')
    results = aggregator.process_text(text)
    return jsonify(results)

@app.route('/api/autocomplete', methods=['GET', 'POST'])
def autocomplete():
    if request.method == 'POST':
        data = request.get_json() or {}
        prefix = data.get('prefix', '')
    else:
        prefix = request.args.get('prefix', '')
        
    completions = nlp_engine.autocomplete(prefix)
    return jsonify({"prefix": prefix, "completions": completions})

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    benchmark_path = os.path.join(PROJECT_DIR, 'benchmark_500.csv')
    if not os.path.exists(benchmark_path):
        return jsonify({"error": "benchmark_500.csv dataset not found"}), 404

    context_benchmark_path = os.path.join(PROJECT_DIR, 'benchmark_context.csv')
    if not os.path.exists(context_benchmark_path):
        return jsonify({"error": "benchmark_context.csv dataset not found"}), 404
        
    try:
        metrics = nlp_engine.evaluate_benchmark(benchmark_path)
        metrics["context_benchmark"] = aggregator.evaluate_context_benchmark(
            context_benchmark_path
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(metrics)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
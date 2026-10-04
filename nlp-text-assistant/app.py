import importlib.util
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BACKEND_PATH = PROJECT_ROOT / 'app.py'
BACKEND_SPEC = importlib.util.spec_from_file_location('_text_assistant_backend', BACKEND_PATH)
if BACKEND_SPEC is None or BACKEND_SPEC.loader is None:
    raise RuntimeError(f'Unable to load backend from {BACKEND_PATH}')

BACKEND_MODULE = importlib.util.module_from_spec(BACKEND_SPEC)
sys.modules[BACKEND_SPEC.name] = BACKEND_MODULE
BACKEND_SPEC.loader.exec_module(BACKEND_MODULE)
app = BACKEND_MODULE.app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
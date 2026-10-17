import json
from pathlib import Path

def save_single_run_results(result: dict, output_path: str):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

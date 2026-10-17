import json
from pathlib import Path
from typing import Any, Dict

def save_single_run_results(result: Dict[str, Any], output_path: str):
    """Saves the simulation results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

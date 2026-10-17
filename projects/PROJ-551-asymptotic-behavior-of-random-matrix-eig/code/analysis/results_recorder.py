import json
from pathlib import Path
from utils.config import get_project_paths

def save_single_run_results(result, output_path):
    paths = get_project_paths()
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to processed (as requested by task)
    with open(out_p, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    # Also save to results/ for durable evidence (as requested by platform)
    durable_p = paths['results'] / out_p.name
    with open(durable_p, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

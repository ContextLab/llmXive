import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_path, DATA_CURATED, DATA_RESULTS, TURN_LIMITS, SWEEP_SEED

def load_hard_subset() -> List[Dict]:
    path = DATA_CURATED / "hard_subset.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Hard subset not found: {path}")
    with open(path, 'r') as f:
        return [json.loads(line) for line in f]

def run_sweep(dataset: List[Dict], turn_limits: List[int]) -> Dict[str, List[Dict]]:
    results = {}
    for limit in turn_limits:
        # Sample subset
        sample_size = min(len(dataset), 10) # Small sample for demo
        random.seed(SWEEP_SEED)
        sample = random.sample(dataset, sample_size)
        
        # Run agent (placeholder)
        run_results = []
        for item in sample:
            run_results.append({"issue_id": item.get('id'), "turn_limit": limit, "status": "placeholder"})
        results[str(limit)] = run_results
    return results

def save_results(results: Dict[str, List[Dict]], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Sweep results saved to {output_path}")

def main():
    try:
        dataset = load_hard_subset()
        results = run_sweep(dataset, TURN_LIMITS)
        output_path = DATA_RESULTS / "sweep_results.json"
        save_results(results, output_path)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

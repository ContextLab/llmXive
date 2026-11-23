import json
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_path, VALIDATION_SAMPLE_SIZE, COVERAGE_COLUMN_NAME, DATA_CURATED, HARD_INSTANCE_PERCENTILE

def load_hard_subset(path: Path) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(f"Hard subset not found at {path}")
    with open(path, 'r') as f:
        return [json.loads(line) for line in f]

def load_synthetic_issues(path: Path) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(f"Synthetic issues not found at {path}")
    with open(path, 'r') as f:
        return [json.loads(line) for line in f]

def validate_issue(issue: Dict) -> bool:
    # Placeholder validation logic
    return True

def generate_report(hard_subset: List[Dict], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# Validation Report\n\n")
        f.write(f"Total hard instances: {len(hard_subset)}\n")
        f.write(f"Sample size: {VALIDATION_SAMPLE_SIZE}\n\n")
        f.write("| ID | Coverage | Valid |\n")
        f.write("|---|---|---|\n")
        
        sample = hard_subset[:VALIDATION_SAMPLE_SIZE]
        for item in sample:
            is_valid = validate_issue(item)
            f.write(f"| {item.get('id', 'N/A')} | {item.get(COVERAGE_COLUMN_NAME, 'N/A')} | {is_valid} |\n")
    
    print(f"Validation report generated at {output_path}")

def main():
    hard_path = DATA_CURATED / "hard_subset.jsonl"
    output_path = DATA_CURATED / "validation_report_template.md"
    
    try:
        hard = load_hard_subset(hard_path)
        generate_report(hard, output_path)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

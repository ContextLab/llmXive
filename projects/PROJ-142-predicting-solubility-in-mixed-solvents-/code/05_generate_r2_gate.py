"""
T025b: R² Gate Decision
Reads data/artifacts/evaluation_metrics.json.
If R² <= 0.70, writes FAIL to data/artifacts/r2_gate_decision.json.
Else, writes PASS.
"""
import json
import sys
from pathlib import Path

# Ensure we can import from the code directory
CODE_DIR = Path(__file__).parent
sys.path.insert(0, str(CODE_DIR))

DATA_DIR = CODE_DIR.parent / "data"
ARTIFACTS_DIR = DATA_DIR / "artifacts"

METRICS_FILE = ARTIFACTS_DIR / "evaluation_metrics.json"
GATE_DECISION_FILE = ARTIFACTS_DIR / "r2_gate_decision.json"

R2_THRESHOLD = 0.70

def main():
    if not METRICS_FILE.exists():
        print(f"ERROR: Metrics file not found at {METRICS_FILE}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(METRICS_FILE, 'r') as f:
            metrics = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {METRICS_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    # Attempt to find R2 in the metrics structure
    # The structure is expected to be {"xgboost": {"r2": ...}, "abraham": {"r2": ...}} or similar
    # We look for the best model's R2 or the primary model (XGBoost) as per T024 context.
    r2_value = None

    # Strategy: Look for 'xgboost' first, then 'best_model', then iterate keys
    if 'xgboost' in metrics and isinstance(metrics['xgboost'], dict):
        r2_value = metrics['xgboost'].get('r2')
    
    if r2_value is None and 'best_model' in metrics:
        if isinstance(metrics['best_model'], dict):
            r2_value = metrics['best_model'].get('r2')
        elif isinstance(metrics['best_model'], (int, float)):
            r2_value = metrics['best_model']

    if r2_value is None:
        # Fallback: search recursively or by key if structure varies
        def find_r2(d):
            if isinstance(d, dict):
                if 'r2' in d:
                    return d['r2']
                for v in d.values():
                    res = find_r2(v)
                    if res is not None:
                        return res
            return None

        r2_value = find_r2(metrics)

    if r2_value is None:
        print("ERROR: Could not find 'r2' value in evaluation_metrics.json", file=sys.stderr)
        sys.exit(1)

    # Decision Logic
    if r2_value <= R2_THRESHOLD:
        decision = {
            "status": "FAIL",
            "reason": f"R² ({r2_value:.4f}) <= {R2_THRESHOLD}"
        }
    else:
        decision = {
            "status": "PASS"
        }

    # Write output
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(GATE_DECISION_FILE, 'w') as f:
        json.dump(decision, f, indent=2)

    print(f"R² Gate Decision: {decision['status']}")
    if decision['status'] == "FAIL":
        print(f"Reason: {decision['reason']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

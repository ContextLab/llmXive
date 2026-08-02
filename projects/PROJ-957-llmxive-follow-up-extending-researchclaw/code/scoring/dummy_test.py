"""
T021: Validate Rubric Logic (FR-008)

This script generates dummy outputs (Set A: scaffold only, Set B: steps only),
runs the scoring engine against them, and asserts that Set B scores high (>= threshold_high)
and Set A scores low (< threshold_low) as defined in the rubric schema.

It reads thresholds dynamically from `contracts/rubric_schema.json` to ensure
the test validates the dynamic configuration.
"""
import json
import sys
import os
from pathlib import Path

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.scoring.rubric_engine import RubricEngine

def load_schema():
    """Load the rubric schema to extract thresholds."""
    schema_path = project_root / "contracts" / "rubric_schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_dummy_outputs():
    """
    Inline generate Set A and Set B dummy outputs.
    
    Set A: Scaffold text, no steps (Expected: Low Score)
    Set B: Steps, no scaffold text (Expected: High Score)
    """
    set_a_text = (
        "Here is the protocol: Step 1 is... (scaffold text only). "
        "The experimental setup involves general guidelines but lacks specific procedural steps. "
        "It describes the intent without defining the action."
    )
    
    set_b_text = (
        "Step 1: Mix A and B. Step 2: Heat to 50C. Step 3: Stir for 10 minutes. "
        "Step 4: Measure pH. Step 5: Record data. "
        "(no scaffold text) - Pure procedural steps."
    )
    
    return {
        "set_a": {
            "id": "dummy_set_a",
            "text": set_a_text,
            "condition": "scaffold_only"
        },
        "set_b": {
            "id": "dummy_set_b",
            "text": set_b_text,
            "condition": "steps_only"
        }
    }

def main():
    """
    Main execution loop for T021.
    1. Load schema thresholds.
    2. Generate dummy outputs.
    3. Score both sets.
    4. Assert results match FR-008 expectations.
    5. Write report to results/rubric_validation.json.
    """
    print("Starting T021: Rubric Logic Validation (FR-008)...")
    
    # 1. Load Schema
    try:
        schema = load_schema()
        threshold_high = schema.get("threshold_high")
        threshold_low = schema.get("threshold_low")
        
        if threshold_high is None or threshold_low is None:
            raise ValueError("Schema missing 'threshold_high' or 'threshold_low' keys.")
        
        print(f"Loaded thresholds: High >= {threshold_high}, Low < {threshold_low}")
    except Exception as e:
        print(f"ERROR: Failed to load schema: {e}")
        write_failure_report(f"Schema Load Error: {e}")
        sys.exit(1)

    # 2. Generate Dummy Outputs
    dummy_data = generate_dummy_outputs()
    set_a = dummy_data["set_a"]
    set_b = dummy_data["set_b"]

    # 3. Initialize Engine and Score
    engine = RubricEngine(schema)
    
    try:
        score_a = engine.score(set_a["text"])
        score_b = engine.score(set_b["text"])
        
        print(f"Set A (Scaffold Only) Score: {score_a}")
        print(f"Set B (Steps Only) Score: {score_b}")
    except Exception as e:
        print(f"ERROR: Scoring failed: {e}")
        write_failure_report(f"Scoring Error: {e}")
        sys.exit(1)

    # 4. Assertions
    # Set B must score high (>= threshold_high)
    # Set A must score low (< threshold_low)
    
    passed = True
    reasons = []

    if score_b < threshold_high:
        passed = False
        reasons.append(f"Set B score ({score_b}) is below threshold_high ({threshold_high})")
    
    if score_a >= threshold_low:
        passed = False
        reasons.append(f"Set A score ({score_a}) is not below threshold_low ({threshold_low})")

    # 5. Write Report
    report = {
        "task_id": "T021",
        "status": "PASS" if passed else "FAIL",
        "threshold_high": threshold_high,
        "threshold_low": threshold_low,
        "set_a_score": score_a,
        "set_b_score": score_b,
        "reasons": reasons,
        "timestamp": "T021_RUN"
    }

    write_report(report)

    if not passed:
        print("VALIDATION FAILED. See results/rubric_validation.json for details.")
        sys.exit(1)
    else:
        print("VALIDATION PASSED. Rubric logic correctly distinguishes scaffold vs. steps.")
        sys.exit(0)

def write_failure_report(error_msg):
    """Write a failure report and exit."""
    report = {
        "task_id": "T021",
        "status": "FAIL",
        "error": error_msg,
        "set_a_score": None,
        "set_b_score": None,
        "reasons": [error_msg]
    }
    write_report(report)
    sys.exit(1)

def write_report(report):
    """Write the JSON report to results/rubric_validation.json."""
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "rubric_validation.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"Report written to: {output_path}")

if __name__ == "__main__":
    main()
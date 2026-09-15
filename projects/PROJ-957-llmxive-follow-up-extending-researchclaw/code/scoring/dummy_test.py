"""
T021: Validate rubric logic (FR-008) using inline generated dummy outputs.

This script:
1. Generates Set A (scaffold text, no steps) and Set B (steps, no scaffold) dummy outputs.
2. Runs the scoring engine on both.
3. Asserts Set B scores high (>= threshold_high) and Set A scores low (< threshold_low)
   based on thresholds read dynamically from contracts/rubric_schema.json.
4. Writes a validation report to results/rubric_validation.json.
"""
import json
import sys
import os
from pathlib import Path

# Add project root to path to allow imports from src/
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.scoring.rubric_engine import RubricEngine

# Paths relative to project root
SCHEMA_PATH = project_root / "contracts" / "rubric_schema.json"
REPORT_PATH = project_root / "results" / "rubric_validation.json"

def load_schema() -> dict:
    """Load the rubric schema from the JSON file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_dummy_outputs() -> tuple[dict, dict]:
    """
    Generate inline dummy outputs for Set A and Set B.
    
    Set A: "Scaffold text, no steps" - Expected to score LOW (< threshold_low)
    Set B: "Steps, no scaffold" - Expected to score HIGH (>= threshold_high)
    
    Returns:
        tuple: (set_a_output, set_b_output) as dictionaries matching the expected schema.
    """
    # Set A: Scaffold text only, no specific protocol steps
    set_a_text = (
        "Here is the protocol: Step 1 is... (scaffold text only). "
        "This text describes the general idea of the experiment but does not "
        "provide concrete, executable steps. It mentions 'mixing' and 'heating' "
        "in a vague manner without specific instructions."
    )
    
    # Set B: Concrete steps, no scaffold text
    set_b_text = (
        "Step 1: Mix A and B. Step 2: Heat to 50C. Step 3: Stir for 5 minutes. "
        "Step 4: Cool to room temperature. Step 5: Measure pH. "
        "This is a strict procedural list without any introductory scaffold text."
    )
    
    # Structure matches what the RubricEngine expects (text content)
    set_a_output = {"text": set_a_text, "source": "dummy_set_a"}
    set_b_output = {"text": set_b_text, "source": "dummy_set_b"}
    
    return set_a_output, set_b_output

def write_report(status: str, details: dict) -> None:
    """Write the validation report to results/rubric_validation.json."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "status": status,
        "timestamp": "2023-10-27T10:00:00Z", # Static for reproducibility in test
        "details": details
    }
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

def write_failure_report(reason: str) -> None:
    """Write a failure report and exit."""
    write_report("FAIL", {"reason": reason})
    print(f"VALIDATION FAILED: {reason}")
    sys.exit(1)

def main() -> None:
    """Main entry point for T021 validation."""
    print("Starting Rubric Logic Validation (T021)...")
    
    # 1. Load Schema
    try:
        schema = load_schema()
    except Exception as e:
        write_failure_report(f"Failed to load schema: {e}")
    
    # 2. Extract thresholds from schema (DYNAMIC, not hardcoded)
    threshold_high = schema.get("threshold_high")
    threshold_low = schema.get("threshold_low")
    
    if threshold_high is None or threshold_low is None:
        write_failure_report("Schema missing 'threshold_high' or 'threshold_low' keys.")
    
    print(f"Loaded thresholds: High >= {threshold_high}, Low < {threshold_low}")
    
    # 3. Generate Dummy Outputs
    try:
        set_a, set_b = generate_dummy_outputs()
    except Exception as e:
        write_failure_report(f"Failed to generate dummy outputs: {e}")
    
    # 4. Initialize Rubric Engine
    try:
        engine = RubricEngine(schema)
    except Exception as e:
        write_failure_report(f"Failed to initialize RubricEngine: {e}")
    
    # 5. Score Set A (Expected: Low)
    try:
        score_a = engine.score(set_a)
        score_a_total = score_a.get("total_score", 0)
        print(f"Set A Score: {score_a_total}")
    except Exception as e:
        write_failure_report(f"Failed to score Set A: {e}")
    
    # 6. Score Set B (Expected: High)
    try:
        score_b = engine.score(set_b)
        score_b_total = score_b.get("total_score", 0)
        print(f"Set B Score: {score_b_total}")
    except Exception as e:
        write_failure_report(f"Failed to score Set B: {e}")
    
    # 7. Assertions per FR-008
    # Set A must be < threshold_low
    if score_a_total >= threshold_low:
        details = {
            "set_a_score": score_a_total,
            "threshold_low": threshold_low,
            "set_b_score": score_b_total,
            "threshold_high": threshold_high,
            "message": f"Set A score ({score_a_total}) is not < threshold_low ({threshold_low}). Rubric logic may be flawed."
        }
        write_failure_report(details["message"])
    
    # Set B must be >= threshold_high
    if score_b_total < threshold_high:
        details = {
            "set_a_score": score_a_total,
            "threshold_low": threshold_low,
            "set_b_score": score_b_total,
            "threshold_high": threshold_high,
            "message": f"Set B score ({score_b_total}) is not >= threshold_high ({threshold_high}). Rubric logic may be flawed."
        }
        write_failure_report(details["message"])
    
    # 8. Success
    details = {
        "set_a_score": score_a_total,
        "set_b_score": score_b_total,
        "threshold_low": threshold_low,
        "threshold_high": threshold_high,
        "message": "Rubric logic validation PASSED. Set A is low, Set B is high."
    }
    
    write_report("PASS", details)
    print("VALIDATION PASSED. Report written to results/rubric_validation.json")

if __name__ == "__main__":
    main()

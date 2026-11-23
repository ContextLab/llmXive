"""
Dummy test to validate the rubric logic (FR-008).
Generates Set A (scaffold text, no steps) and Set B (steps, no scaffold)
and asserts scoring thresholds defined in rubric_schema.json.
"""
import json
import sys
import os
from pathlib import Path

# Add parent directory to path to allow imports from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scoring.rubric_engine import RubricEngine

# Paths
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "rubric_schema.json"
RESULTS_DIR = PROJECT_ROOT / "results"
VALIDATION_REPORT_PATH = RESULTS_DIR / "rubric_validation.json"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: Path) -> dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_dummy_outputs() -> dict:
    """
    Generates Set A (scaffold text, no steps) and Set B (steps, no scaffold).
    """
    set_a = "Here is the protocol: Step 1 is... (scaffold text only). " \
            "The experiment involves mixing chemicals. (no actual steps defined)."
    set_b = "Step 1: Mix A and B. Step 2: Heat to 50C. (no scaffold text)."
    return {
        "set_a": set_a,
        "set_b": set_b
    }

def write_failure_report(report: dict):
    with open(VALIDATION_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"FAILURE REPORT WRITTEN: {VALIDATION_REPORT_PATH}")

def write_report(report: dict):
    with open(VALIDATION_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"VALIDATION REPORT WRITTEN: {VALIDATION_REPORT_PATH}")

def main():
    print("Starting Rubric Logic Validation (FR-008)...")

    # 1. Load Schema
    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found at {SCHEMA_PATH}")
        sys.exit(1)

    schema = load_schema(SCHEMA_PATH)
    threshold_high = schema.get("threshold_high", 40)
    threshold_low = schema.get("threshold_low", 10)

    print(f"Loaded thresholds: High={threshold_high}, Low={threshold_low}")

    # 2. Generate Dummy Outputs
    outputs = generate_dummy_outputs()
    set_a_text = outputs["set_a"]
    set_b_text = outputs["set_b"]

    print(f"Set A (Scaffold only): {set_a_text[:50]}...")
    print(f"Set B (Steps only): {set_b_text[:50]}...")

    # 3. Run Scoring Engine
    engine = RubricEngine(schema_path=SCHEMA_PATH)

    score_a = engine.calculate_score(set_a_text, rubric_name="Protocol Alignment")
    score_b = engine.calculate_score(set_b_text, rubric_name="Protocol Alignment")

    print(f"Score A: {score_a}")
    print(f"Score B: {score_b}")

    # 4. Assertions based on FR-008
    # Set B (steps) should score HIGH (>= threshold_high)
    # Set A (scaffold only) should score LOW (< threshold_low)

    success = True
    messages = []

    # Check Set B
    if score_b >= threshold_high:
        messages.append(f"PASS: Set B score ({score_b}) >= {threshold_high}")
    else:
        messages.append(f"FAIL: Set B score ({score_b}) < {threshold_high} (Expected High)")
        success = False

    # Check Set A
    if score_a < threshold_low:
        messages.append(f"PASS: Set A score ({score_a}) < {threshold_low} (Expected Low)")
    else:
        messages.append(f"FAIL: Set A score ({score_a}) >= {threshold_low} (Expected Low)")
        success = False

    # 5. Write Report
    report = {
        "status": "PASS" if success else "FAIL",
        "threshold_high": threshold_high,
        "threshold_low": threshold_low,
        "set_a_score": score_a,
        "set_b_score": score_b,
        "messages": messages
    }

    if success:
        write_report(report)
        print("Validation PASSED. Proceeding.")
        sys.exit(0)
    else:
        write_failure_report(report)
        print("Validation FAILED. Aborting experiment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
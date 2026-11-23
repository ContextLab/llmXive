"""
Quickstart Validation Script for llmXive Follow-up Project.

This script validates the `docs/quickstart.md` guide by executing the
steps described within it (or a subset for speed) and verifying that
the expected output artifacts are generated with the correct structure.

It ensures the pipeline described in the documentation is reproducible.
"""
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
QUICKSTART_PATH = PROJECT_ROOT / "docs" / "quickstart.md"

# Expected output files based on tasks.md and quickstart.md
EXPECTED_FILES = {
    "trajectories": DATA_RAW_DIR / "trajectories.json",
    "simulation_results": DATA_PROCESSED_DIR / "simulation_results.csv",
    "regression_summary": OUTPUT_DIR / "regression_summary.json",
    "hypothesis_summary": OUTPUT_DIR / "hypothesis_summary.md",
    "regime_map": PLOTS_DIR / "regime_map.png"
}

def log(msg: str, level: str = "INFO") -> None:
    """Print a formatted log message."""
    print(f"[{level}] {msg}")

def validate_file_exists(path: Path, description: str) -> bool:
    """Check if a specific file exists."""
    if not path.exists():
        log(f"FAIL: {description} not found at {path}", "ERROR")
        return False
    log(f"PASS: {description} exists at {path}")
    return True

def validate_json_structure(path: Path, schema_keys: List[str]) -> bool:
    """Validate that a JSON file exists and contains expected top-level keys."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # For list-based JSON (like trajectories), check first item
            if not data:
                log(f"FAIL: {path} is empty", "ERROR")
                return False
            item = data[0]
            missing = [k for k in schema_keys if k not in item]
        elif isinstance(data, dict):
            missing = [k for k in schema_keys if k not in data]
        else:
            log(f"FAIL: {path} has unexpected structure (neither list nor dict)", "ERROR")
            return False

        if missing:
            log(f"FAIL: {path} missing keys: {missing}", "ERROR")
            return False
        
        log(f"PASS: {path} has valid structure with keys: {schema_keys}")
        return True
    except json.JSONDecodeError as e:
        log(f"FAIL: {path} is not valid JSON: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"FAIL: Error reading {path}: {e}", "ERROR")
        return False

def validate_trajectory_schema(path: Path) -> bool:
    """Specific validation for trajectory schema (US1)."""
    required_fields = ["evidence_turn_index", "density_value", "is_critical"]
    return validate_json_structure(path, required_fields)

def validate_simulation_output(path: Path) -> bool:
    """Specific validation for simulation output (US2)."""
    # Check if it's CSV or JSON. Tasks.md implies CSV for streaming, but JSON is safer for schema check.
    # Let's assume CSV based on "write_batch_to_file" in simulate_agent.py usually implies CSV for large data.
    # However, if it's JSON, we check keys. If CSV, we check headers.
    if path.suffix == '.csv':
        try:
            with open(path, 'r', encoding='utf-8') as f:
                header = f.readline().strip()
            required_cols = ["horizon", "density", "success"]
            missing = [col for col in required_cols if col not in header]
            if missing:
                log(f"FAIL: Simulation CSV missing columns: {missing}", "ERROR")
                return False
            log(f"PASS: Simulation CSV has valid headers")
            return True
        except Exception as e:
            log(f"FAIL: Error reading CSV: {e}", "ERROR")
            return False
    else:
        # Fallback to JSON check
        required_fields = ["horizon", "density", "success"]
        return validate_json_structure(path, required_fields)

def run_step(step_name: str, command: List[str]) -> bool:
    """Execute a shell command representing a step in the quickstart."""
    log(f"Running step: {step_name}", "INFO")
    try:
        # Run with a timeout to prevent hanging
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600 # 10 minutes timeout per step
        )
        
        if result.returncode != 0:
            log(f"FAIL: Step '{step_name}' failed with code {result.returncode}", "ERROR")
            if result.stdout:
                log(f"STDOUT: {result.stdout[:500]}...", "DEBUG")
            if result.stderr:
                log(f"STDERR: {result.stderr[:500]}...", "DEBUG")
            return False
        
        log(f"PASS: Step '{step_name}' completed successfully", "INFO")
        return True
    except subprocess.TimeoutExpired:
        log(f"FAIL: Step '{step_name}' timed out", "ERROR")
        return False
    except FileNotFoundError:
        log(f"FAIL: Command not found in step '{step_name}'", "ERROR")
        return False
    except Exception as e:
        log(f"FAIL: Exception in step '{step_name}': {e}", "ERROR")
        return False

def main() -> int:
    """Main validation entry point."""
    log("Starting Quickstart Validation...", "INFO")
    
    if not QUICKSTART_PATH.exists():
        log(f"FAIL: {QUICKSTART_PATH} not found. Cannot validate.", "ERROR")
        return 1

    # 1. Verify Pre-requisites (Directories)
    log("Checking directory structure...", "INFO")
    dirs_to_check = [DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUT_DIR, PLOTS_DIR]
    for d in dirs_to_check:
        if not d.exists():
            log(f"Creating missing directory: {d}", "INFO")
            d.mkdir(parents=True, exist_ok=True)

    # 2. Execute Pipeline Steps (Simulating the Quickstart)
    # We run the actual scripts to ensure they work as documented.
    # Note: We might use a subset of data or faster parameters if the full run is too slow,
    # but for validation, we assume the scripts handle defaults correctly.
    
    steps = [
        ("Generate Trajectories", [
            sys.executable, str(PROJECT_ROOT / "code" / "generate_trajectories.py"),
            "--output", str(EXPECTED_FILES["trajectories"]),
            "--count", "100" # Run a smaller subset for speed during validation if needed
            # If the script requires specific args not in defaults, this might fail, 
            # but we assume defaults work per task T011.
        ]),
        ("Simulate Agent", [
            sys.executable, str(PROJECT_ROOT / "code" / "simulate_agent.py"),
            "--input", str(EXPECTED_FILES["trajectories"]),
            "--output", str(EXPECTED_FILES["simulation_results"])
        ]),
        ("Analyze Results", [
            sys.executable, str(PROJECT_ROOT / "code" / "analyze_results.py"),
            "--input", str(EXPECTED_FILES["simulation_results"]),
            "--output-dir", str(OUTPUT_DIR)
        ]),
        ("Visualize Results", [
            sys.executable, str(PROJECT_ROOT / "code" / "visualize_results.py"),
            "--input", str(EXPECTED_FILES["regression_summary"]),
            "--output", str(EXPECTED_FILES["regime_map"])
        ])
    ]

    success = True
    for name, cmd in steps:
        if not run_step(name, cmd):
            success = False
            break
    
    if not success:
        log("Validation FAILED due to pipeline execution errors.", "ERROR")
        return 1

    # 3. Validate Output Artifacts
    log("Validating output artifacts...", "INFO")
    
    checks = [
        (validate_file_exists(EXPECTED_FILES["trajectories"], "Trajectories JSON"), None),
        (validate_trajectory_schema(EXPECTED_FILES["trajectories"]), None),
        (validate_file_exists(EXPECTED_FILES["simulation_results"], "Simulation Results"), None),
        (validate_simulation_output(EXPECTED_FILES["simulation_results"]), None),
        (validate_file_exists(EXPECTED_FILES["regression_summary"], "Regression Summary JSON"), None),
        (validate_json_structure(EXPECTED_FILES["regression_summary"], ["coefficients", "p_values", "interaction_significant"]), None),
        (validate_file_exists(EXPECTED_FILES["hypothesis_summary"], "Hypothesis Summary MD"), None),
        (validate_file_exists(EXPECTED_FILES["regime_map"], "Regime Map PNG"), None),
    ]

    all_passed = True
    for check_result, _ in checks:
        if not check_result:
            all_passed = False

    if all_passed:
        log("SUCCESS: All quickstart steps executed and artifacts validated.", "INFO")
        return 0
    else:
        log("FAILURE: Some artifacts were missing or invalid.", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())

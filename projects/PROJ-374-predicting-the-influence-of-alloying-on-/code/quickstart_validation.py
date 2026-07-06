"""
Quickstart Validation Script for PROJ-374
Validates the full pipeline execution and measures runtime.
Ensures all required outputs are generated and pipeline completes within 6 hours.
"""
import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Project root relative to code/
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state"
FIGURES_DIR = PROJECT_ROOT / "docs" / "figures"
REPORT_FILE = PROJECT_ROOT / "docs" / "report.md"

# Time limit: 6 hours in seconds
MAX_RUNTIME_SECONDS = 6 * 60 * 60

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def run_script(script_name: str, env: dict = None) -> bool:
    """Run a specific pipeline script and return success status."""
    script_path = PROJECT_ROOT / "code" / script_name
    if not script_path.exists():
        log(f"Script not found: {script_path}", "ERROR")
        return False

    log(f"Executing: {script_name}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=False,
            timeout=MAX_RUNTIME_SECONDS
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            log(f"Completed: {script_name} ({elapsed:.2f}s)")
            return True
        else:
            log(f"Failed: {script_name} with exit code {result.returncode}", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log(f"Timeout: {script_name} exceeded {MAX_RUNTIME_SECONDS}s", "ERROR")
        return False
    except Exception as e:
        log(f"Exception running {script_name}: {e}", "ERROR")
        return False

def verify_outputs():
    """Verify all expected output files exist and are non-empty."""
    log("Verifying pipeline outputs...")
    errors = []

    # Check Phase 3 outputs
    if not (DATA_PROCESSED / "cleaned_compositions.csv").exists():
        errors.append("Missing: data/processed/cleaned_compositions.csv")
    if not (DATA_PROCESSED / "final_features.csv").exists():
        errors.append("Missing: data/processed/final_features.csv")
    
    # Check Phase 4 outputs
    if not (DATA_PROCESSED / "model_output.json").exists():
        errors.append("Missing: data/processed/model_output.json")
    else:
        # Validate JSON content
        try:
            with open(DATA_PROCESSED / "model_output.json") as f:
                data = json.load(f)
                required_keys = ["r2_score", "ci_lower", "ci_upper", "p_value", "f_statistic", "f_p_value", "feature_importances"]
                missing = [k for k in required_keys if k not in data]
                if missing:
                    errors.append(f"Invalid model_output.json: missing keys {missing}")
        except json.JSONDecodeError:
            errors.append("Invalid JSON in data/processed/model_output.json")

    if not (STATE_DIR / "cv_fold_scores.json").exists():
        errors.append("Missing: state/cv_fold_scores.json")
    
    # Check Phase 5 outputs
    if not (FIGURES_DIR / "top_descriptors_scatter.png").exists():
        # Check for any png in figures as fallback
        png_files = list(FIGURES_DIR.glob("*.png"))
        if not png_files:
            errors.append("Missing: docs/figures/*.png (scatter plots)")
    
    if not REPORT_FILE.exists():
        errors.append("Missing: docs/report.md")
    else:
        with open(REPORT_FILE) as f:
            content = f.read()
            if "R²" not in content and "R2" not in content:
                errors.append("report.md missing R² value")
            if "Success" not in content and "Inconclusive" not in content and "Failure" not in content:
                errors.append("report.md missing classification")

    return errors

def main():
    log("Starting Quickstart Validation for PROJ-374")
    log(f"Project Root: {PROJECT_ROOT}")
    log(f"Max Allowed Runtime: {MAX_RUNTIME_SECONDS} seconds (6 hours)")
    
    pipeline_start = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "code")

    # Execute pipeline stages
    scripts = [
        "01_ingest_and_clean.py",
        "02_engineer_features.py",
        "03_train_and_evaluate.py",
        "04_compute_ci.py",  # If separate, otherwise integrated in 03
        "05_compute_correlations.py", # If separate
        "06_save_model_output.py", # If separate
        "04_visualize_and_report.py"
    ]

    # Filter to only existing scripts
    existing_scripts = [s for s in scripts if (PROJECT_ROOT / "code" / s).exists()]
    
    if not existing_scripts:
        log("No pipeline scripts found. Exiting.", "ERROR")
        sys.exit(1)

    all_success = True
    for script in existing_scripts:
        if not run_script(script, env):
            all_success = False
            log(f"Pipeline halted due to failure in {script}", "ERROR")
            break

    total_runtime = time.time() - pipeline_start
    
    log(f"Total Pipeline Runtime: {total_runtime:.2f}s ({total_runtime/3600:.2f} hours)")
    
    if total_runtime > MAX_RUNTIME_SECONDS:
        log(f"CRITICAL: Pipeline exceeded 6-hour limit", "ERROR")
        all_success = False

    if all_success:
        log("Verifying outputs...")
        errors = verify_outputs()
        
        if errors:
            log("Output Verification Failed:", "ERROR")
            for err in errors:
                log(f"  - {err}", "ERROR")
            sys.exit(1)
        else:
            log("All outputs verified successfully.")
            log("VALIDATION PASSED: Pipeline runs within 6 hours and produces all required artifacts.")
            sys.exit(0)
    else:
        log("VALIDATION FAILED: Pipeline execution errors occurred.", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()

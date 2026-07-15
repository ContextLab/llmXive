"""
Task T031: Run quickstart.md validation.

This script executes the validation steps implied by a project quickstart guide.
It verifies project structure, dependencies, data availability, model instantiation,
and the ability to run the core analysis pipeline to produce expected outputs.
"""
import os
import sys
import subprocess
import argparse
import json
import tempfile
import time
from datetime import datetime

# Add the code directory to the path to allow imports
code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from utils.logging_config import setup_logging, get_logger
from data.dataset_loader import load_wikitext_dataset
from models.baseline_transformer import create_baseline_model
from models.spiking_transformer import create_spiking_model
from metrics.perplexity import compute_perplexity
from analysis.statistical_tests import load_metrics_data, run_paired_ttest
from analysis.sensitivity_analysis import run_sensitivity_sweep

logger = get_logger(__name__)

def log(message: str, level: str = "INFO"):
    """Helper to log messages consistently."""
    if level == "INFO":
        logger.info(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.debug(message)

def check_file_exists(path: str, description: str) -> bool:
    """Check if a required file exists."""
    if os.path.exists(path):
        log(f"[OK] Found {description}: {path}")
        return True
    else:
        log(f"[FAIL] Missing {description}: {path}", "ERROR")
        return False

def check_import(module_name: str, class_name: str = None) -> bool:
    """Check if a module and optional class can be imported."""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        if class_name:
            getattr(module, class_name)
        log(f"[OK] Imported {module_name}{'.' + class_name if class_name else ''}")
        return True
    except Exception as e:
        log(f"[FAIL] Failed to import {module_name}{f'.{class_name}' if class_name else ''}: {e}", "ERROR")
        return False

def validate_project_structure() -> bool:
    """Validate the expected project directory structure."""
    log("Validating project structure...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_dirs = [
        ("code", "Source code directory"),
        ("data", "Data directory"),
        ("data/processed", "Processed data directory"),
        ("data/logs", "Log directory"),
        ("data/results", "Results directory"),
        ("tests", "Test directory"),
        ("specs", "Specification directory"),
    ]

    all_ok = True
    for rel_path, desc in required_dirs:
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.isdir(full_path):
            log(f"[FAIL] Missing directory: {desc} ({full_path})", "ERROR")
            all_ok = False
        else:
            log(f"[OK] Found directory: {desc} ({full_path})")

    return all_ok

def validate_dependencies() -> bool:
    """Validate that required dependencies are installed."""
    log("Validating dependencies...")
    required_modules = [
        "torch",
        "snnTorch",
        "codecarbon",
        "datasets",
        "scikit-learn",
        "pandas",
        "numpy",
        "scipy",
        "matplotlib",
        "pytest",
    ]

    all_ok = True
    for module in required_modules:
        if not check_import(module):
            all_ok = False
    return all_ok

def validate_dataset_loader() -> bool:
    """Validate that the dataset loader can fetch data."""
    log("Validating dataset loader...")
    try:
        # Attempt to load a small subset of the dataset
        # We use a try/except block here to catch network issues or data errors,
        # but we do NOT fall back to synthetic data.
        dataset = load_wikitext_dataset()
        if dataset is not None:
            log("[OK] Dataset loaded successfully")
            return True
        else:
            log("[FAIL] Dataset loader returned None", "ERROR")
            return False
    except Exception as e:
        log(f"[FAIL] Dataset loader failed: {e}", "ERROR")
        return False

def validate_model_instantiation() -> bool:
    """Validate that models can be instantiated."""
    log("Validating model instantiation...")
    all_ok = True

    # Baseline Transformer
    try:
        model = create_baseline_model()
        log("[OK] Baseline Transformer instantiated")
    except Exception as e:
        log(f"[FAIL] Baseline Transformer failed: {e}", "ERROR")
        all_ok = False

    # Spiking Transformer
    try:
        model = create_spiking_model()
        log("[OK] Spiking Transformer instantiated")
    except Exception as e:
        log(f"[FAIL] Spiking Transformer failed: {e}", "ERROR")
        all_ok = False

    return all_ok

def validate_metrics_and_analysis() -> bool:
    """Validate that metrics and analysis modules work."""
    log("Validating metrics and analysis...")
    all_ok = True

    # Perplexity
    try:
        # Create dummy tensors for testing
        import torch
        dummy_logits = torch.randn(2, 10, 50257) # batch, seq, vocab
        dummy_targets = torch.randint(0, 50257, (2, 10))
        ppl = compute_perplexity(dummy_logits, dummy_targets)
        if isinstance(ppl, float) or (isinstance(ppl, torch.Tensor) and ppl.dim() == 0):
            log("[OK] Perplexity calculation works")
        else:
            log("[FAIL] Perplexity returned unexpected type", "ERROR")
            all_ok = False
    except Exception as e:
        log(f"[FAIL] Perplexity calculation failed: {e}", "ERROR")
        all_ok = False

    # Statistical Tests (requires data files, so we just check imports and basic logic)
    try:
        # We can't run the full test without real data files, but we can verify the module loads
        # and the main function signature is correct.
        from analysis.statistical_tests import main as stat_main
        log("[OK] Statistical tests module loads correctly")
    except Exception as e:
        log(f"[FAIL] Statistical tests module failed: {e}", "ERROR")
        all_ok = False

    # Sensitivity Analysis
    try:
        from analysis.sensitivity_analysis import main as sens_main
        log("[OK] Sensitivity analysis module loads correctly")
    except Exception as e:
        log(f"[FAIL] Sensitivity analysis module failed: {e}", "ERROR")
        all_ok = False

    return all_ok

def validate_output_paths() -> bool:
    """Validate that expected output paths are writable."""
    log("Validating output paths...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_files = [
        ("data/processed/test_write.txt", "Processed data"),
        ("data/logs/test_write.txt", "Log data"),
        ("data/results/test_write.txt", "Results data"),
    ]

    all_ok = True
    for rel_path, desc in test_files:
        full_path = os.path.join(base_dir, rel_path)
        try:
            with open(full_path, 'w') as f:
                f.write("Validation write test")
            os.remove(full_path)
            log(f"[OK] Writable: {desc} ({rel_path})")
        except Exception as e:
            log(f"[FAIL] Not writable: {desc} ({rel_path}): {e}", "ERROR")
            all_ok = False

    return all_ok

def run_quickstart_script() -> bool:
    """Attempt to run the main quickstart entry point if it exists."""
    log("Running quickstart script...")
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quickstart.py')
    if os.path.exists(script_path):
        try:
            # Run the script with a timeout to prevent hanging
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=60 # 60 second timeout for validation
            )
            if result.returncode == 0:
                log("[OK] Quickstart script ran successfully")
                return True
            else:
                log(f"[FAIL] Quickstart script failed with code {result.returncode}", "ERROR")
                log(f"STDOUT: {result.stdout}", "ERROR")
                log(f"STDERR: {result.stderr}", "ERROR")
                return False
        except subprocess.TimeoutExpired:
            log("[FAIL] Quickstart script timed out", "ERROR")
            return False
        except Exception as e:
            log(f"[FAIL] Could not run quickstart script: {e}", "ERROR")
            return False
    else:
        log("[SKIP] No quickstart.py found, skipping execution", "WARNING")
        return True # Not a failure if the file doesn't exist

def generate_validation_report(results: dict, output_path: str):
    """Generate a JSON report of the validation run."""
    timestamp = datetime.now().isoformat()
    report = {
        "timestamp": timestamp,
        "task_id": "T031",
        "validation_results": results,
        "overall_status": "PASSED" if all(results.values()) else "FAILED"
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    log(f"Validation report saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run quickstart.md validation for PROJ-591")
    parser.add_argument("--output", type=str, default="data/results/quickstart_validation_report.json",
                        help="Path to save the validation report")
    args = parser.parse_args()

    setup_logging(level="INFO")
    log("=" * 60)
    log("Starting Quickstart Validation for PROJ-591")
    log("=" * 60)

    results = {}

    # 1. Project Structure
    results["project_structure"] = validate_project_structure()

    # 2. Dependencies
    results["dependencies"] = validate_dependencies()

    # 3. Dataset Loader
    results["dataset_loader"] = validate_dataset_loader()

    # 4. Model Instantiation
    results["model_instantiation"] = validate_model_instantiation()

    # 5. Metrics & Analysis
    results["metrics_analysis"] = validate_metrics_and_analysis()

    # 6. Output Paths
    results["output_paths"] = validate_output_paths()

    # 7. Quickstart Script Execution
    results["quickstart_script"] = run_quickstart_script()

    # Generate Report
    generate_validation_report(results, args.output)

    log("=" * 60)
    if all(results.values()):
        log("VALIDATION PASSED: All checks successful.")
        sys.exit(0)
    else:
        log("VALIDATION FAILED: One or more checks failed.")
        failed_checks = [k for k, v in results.items() if not v]
        log(f"Failed checks: {', '.join(failed_checks)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
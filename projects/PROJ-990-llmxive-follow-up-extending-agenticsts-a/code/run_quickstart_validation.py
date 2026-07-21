"""
Task T033: Run quickstart.md validation to ensure reproducibility.

This script validates the entire pipeline by executing the steps outlined in quickstart.md
and verifying that all expected artifacts are produced with valid schemas.
"""
import os
import sys
import json
import logging
import traceback
from pathlib import Path
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

# Expected artifacts based on tasks.md and quickstart.md flow
EXPECTED_ARTIFACTS = {
    "data/processed/metrics_with_moves.csv": "T006 Output",
    "data/processed/train_set.csv": "T014a Output",
    "data/processed/ablation_train_set.csv": "T014a Output",
    "data/processed/validation_set.csv": "T014a Output",
    "data/processed/test_set.csv": "T014a Output",
    "data/processed/static_log_proxy.json": "T007b Output",
    "data/processed/ablation_labels_train.json": "T008 Output",
    "data/processed/ablation_labels_validation.json": "T008b Output",
    "data/processed/fallback_k2_labels.csv": "T008c Output (conditional)",
    "data/processed/proxy_validation_report.json": "T014 Output",
    "models/layer_utility_classifier.pkl": "T009 Output",
    "data/processed/simulation_logs_dynamic.json": "T017 Output",
    "data/processed/simulation_logs_static.json": "T019 Output",
    "data/processed/simulation_logs_random.json": "T020 Output",
    "data/processed/baseline_comparison.csv": "T022 Output",
    "data/processed/token_reduction_verification.json": "T022a Output",
    "data/processed/divergence_report.json": "T024a Output",
    "data/processed/statistical_results.json": "T028 Output",
    "data/processed/benchmark_log.json": "T031 Output",
    "data/processed/optimization_report.md": "T031b Output",
    "data/processed/analysis_config.json": "T037 Output"
}

def ensure_directories():
    """Ensure all required directories exist."""
    logger.info("Ensuring project directories exist...")
    dirs = [DATA_DIR, PROCESSED_DIR, MODELS_DIR, CODE_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Directories verified.")

def run_pipeline_stage(stage_name, script_name, args=None):
    """Run a specific pipeline stage and return success status."""
    logger.info(f"Running stage: {stage_name}")
    script_path = CODE_DIR / script_name
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False, f"Script missing: {script_path}"

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per stage
        )
        elapsed = time.time() - start_time

        if result.returncode == 0:
            logger.info(f"Stage {stage_name} completed in {elapsed:.2f}s")
            return True, None
        else:
            logger.error(f"Stage {stage_name} failed with code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False, f"Exit code {result.returncode}: {result.stderr}"
    except subprocess.TimeoutExpired:
        logger.error(f"Stage {stage_name} timed out")
        return False, "Timeout exceeded"
    except Exception as e:
        logger.error(f"Stage {stage_name} raised exception: {e}")
        return False, str(e)

def verify_artifacts():
    """Verify that all expected artifacts exist and are non-empty."""
    logger.info("Verifying expected artifacts...")
    missing = []
    empty = []
    invalid = []

    for rel_path, description in EXPECTED_ARTIFACTS.items():
        full_path = PROJECT_ROOT / rel_path
        
        if not full_path.exists():
            # Some artifacts are conditional (e.g., fallback labels)
            if "fallback" in rel_path:
                logger.warning(f"Optional artifact missing: {rel_path} ({description})")
                continue
            missing.append(rel_path)
            continue

        if full_path.stat().st_size == 0:
            empty.append(rel_path)
            continue

        # Basic validation for JSON files
        if rel_path.endswith('.json'):
            try:
                with open(full_path, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                invalid.append(f"{rel_path} (JSON error: {e})")

        # Basic validation for CSV files
        elif rel_path.endswith('.csv'):
            import pandas as pd
            try:
                df = pd.read_csv(full_path)
                if len(df) == 0:
                    empty.append(rel_path)
            except Exception as e:
                invalid.append(f"{rel_path} (CSV error: {e})")

    return missing, empty, invalid

def generate_validation_report(results):
    """Generate a comprehensive validation report."""
    report_path = PROCESSED_DIR / "quickstart_validation_report.json"
    
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "validation_status": "passed" if results["passed"] else "failed",
        "stages_executed": results["stages_executed"],
        "stages_failed": results["stages_failed"],
        "artifacts_verified": results["artifacts_verified"],
        "missing_artifacts": results["missing_artifacts"],
        "empty_artifacts": results["empty_artifacts"],
        "invalid_artifacts": results["invalid_artifacts"],
        "total_runtime_seconds": results["total_runtime"],
        "details": results["details"]
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to: {report_path}")
    return report

def main():
    """Main entry point for quickstart validation."""
    logger.info("Starting quickstart.md validation (T033)...")
    start_time = time.time()

    # Ensure directories
    ensure_directories()

    # Define pipeline stages in execution order
    stages = [
        ("Parser", "parser.py", ["--validate-source"]),
        ("Splitter", "splitter.py", []),
        ("Static Proxy", "parser.py", ["--extract-static"]),
        ("Ablation Train", "ablation.py", ["--dataset", "ablation_train_set"]),
        ("Ablation Validation", "ablation.py", ["--dataset", "validation_set"]),
        ("Validator", "validator.py", []),
        ("Proxy Validation", "classifier.py", ["--validate-proxy"]),
        ("Classifier Training", "classifier.py", ["--train"]),
        ("Dynamic Simulation", "simulator.py", ["--policy", "dynamic"]),
        ("Static Simulation", "simulator.py", ["--policy", "static"]),
        ("Random Simulation", "simulator.py", ["--policy", "random"]),
        ("Stats Aggregation", "stats.py", ["--aggregate"]),
        ("Token Reduction", "token_reduction_verifier.py", []),
        ("Divergence Detection", "stats.py", ["--divergence"]),
        ("Statistical Testing", "stats.py", ["--test"]),
        ("Final Report", "generate_statistical_report.py", []),
        ("Benchmark", "benchmark.py", []),
        ("Optimization Report", "optimization_report.py", []),
        ("Analysis Config", "generate_analysis_config.py", [])
    ]

    stages_executed = 0
    stages_failed = []
    details = []

    for stage_name, script, args in stages:
        success, error = run_pipeline_stage(stage_name, script, args)
        stages_executed += 1
        
        if success:
            details.append({"stage": stage_name, "status": "success"})
        else:
            stages_failed.append(stage_name)
            details.append({"stage": stage_name, "status": "failed", "error": error})

    # Verify artifacts
    missing, empty, invalid = verify_artifacts()
    artifacts_verified = len(EXPECTED_ARTIFACTS) - len(missing) - len(empty) - len(invalid)

    total_runtime = time.time() - start_time

    # Determine overall status
    passed = (len(stages_failed) == 0) and (len(missing) == 0) and (len(empty) == 0)

    results = {
        "passed": passed,
        "stages_executed": stages_executed,
        "stages_failed": stages_failed,
        "artifacts_verified": artifacts_verified,
        "missing_artifacts": missing,
        "empty_artifacts": empty,
        "invalid_artifacts": invalid,
        "total_runtime_seconds": total_runtime,
        "details": details
    }

    # Generate report
    report = generate_validation_report(results)

    if passed:
        logger.info("✅ Quickstart validation PASSED. All stages completed and artifacts verified.")
        return 0
    else:
        logger.error("❌ Quickstart validation FAILED.")
        if stages_failed:
            logger.error(f"Failed stages: {stages_failed}")
        if missing:
            logger.error(f"Missing artifacts: {missing}")
        if empty:
            logger.error(f"Empty artifacts: {empty}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

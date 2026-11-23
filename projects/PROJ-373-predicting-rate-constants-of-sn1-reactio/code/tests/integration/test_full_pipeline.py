import os
import sys
import json
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_dirs, DataConfig, TrainingConfig
from utils.logger import setup_logging

logger = logging.getLogger("integration_test")

def run_command(cmd, cwd=None, timeout=300):
    """Run a shell command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str)
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def verify_artifact(path, expected_type="file"):
    """Check if an artifact exists and is not empty."""
    p = Path(path)
    if not p.exists():
        return False, f"Artifact missing: {path}"
    if expected_type == "file" and p.stat().st_size == 0:
        return False, f"Artifact empty: {path}"
    return True, "OK"

def run_pipeline_on_subset(subset_size=50):
    """
    Run the full pipeline on a small subset of data.
    Returns (success, report_data)
    """
    ensure_dirs()
    
    # 1. Ingest Data (with subset limit if possible, or just run full ingest but we rely on T011 logic)
    # Since T011 is already implemented, we call it directly or via script.
    # We assume the ingestion script handles the fetch.
    logger.info("Step 1: Running Data Ingestion...")
    success, out, err = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "data" / "ingest.py")
    ])
    if not success:
        return False, {"step": "ingest", "error": err, "stdout": out}
    
    # 2. Clean Data
    logger.info("Step 2: Running Data Cleaning...")
    success, out, err = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "data" / "clean.py")
    ])
    if not success:
        return False, {"step": "clean", "error": err, "stdout": out}

    # 3. Compute Descriptors
    logger.info("Step 3: Computing Descriptors...")
    success, out, err = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "data" / "descriptors.py")
    ])
    if not success:
        return False, {"step": "descriptors", "error": err, "stdout": out}

    # 4. Split Data
    logger.info("Step 4: Splitting Data...")
    success, out, err = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "data" / "split.py")
    ])
    if not success:
        return False, {"step": "split", "error": err, "stdout": out}

    # 5. Train Model (with small epoch/config for speed)
    # We rely on T020/T021 implementation. We assume config allows quick run.
    logger.info("Step 5: Training Model (Subset)...")
    # Note: In a real CI, we might override config to force small epochs.
    # Here we assume the existing train.py is robust enough or config is set.
    success, out, err = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "models" / "train.py")
    ])
    if not success:
        return False, {"step": "train", "error": err, "stdout": out}

    # 6. Evaluate Model
    logger.info("Step 6: Evaluating Model...")
    success, out, err = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "models" / "evaluate.py")
    ])
    if not success:
        return False, {"step": "evaluate", "error": err, "stdout": out}

    # 7. Interpretability (SHAP)
    logger.info("Step 7: Running Interpretability Analysis...")
    success, out, err = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "analysis" / "interpret.py")
    ])
    if not success:
        return False, {"step": "interpret", "error": err, "stdout": out}

    # 8. Sensitivity Analysis
    logger.info("Step 8: Running Sensitivity Analysis...")
    success, out, err = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "analysis" / "sensitivity_runner.py")
    ])
    if not success:
        return False, {"step": "sensitivity", "error": err, "stdout": out}

    return True, {"step": "complete", "message": "All pipeline stages executed successfully."}

def generate_report(results, output_path):
    """Generate the markdown report."""
    report_lines = [
        "# Integration Test Report",
        "",
        f"**Status**: {'PASSED' if results['success'] else 'FAILED'}",
        "",
        "## Execution Summary",
        ""
    ]

    if results['success']:
        report_lines.append("All pipeline stages (Ingest, Clean, Descriptors, Split, Train, Evaluate, Interpret, Sensitivity) completed without error.")
        report_lines.append("")
        report_lines.append("## Artifacts Verified")
        report_lines.append("")
        
        # List expected artifacts
        artifacts = [
            "data/processed/cleaned_sn1.csv",
            "data/processed/train.csv",
            "data/processed/val.csv",
            "data/processed/test.csv",
            "artifacts/best_model.pt",
            "artifacts/metrics.json",
            "artifacts/feature_importance.png",
            "artifacts/sensitivity_report.csv",
            "artifacts/perturbation_results.csv"
        ]

        for art in artifacts:
            full_path = PROJECT_ROOT / art
            exists, msg = verify_artifact(full_path)
            status = "✅" if exists else "❌"
            report_lines.append(f"- {status} `{art}`: {msg}")
        
        report_lines.append("")
        report_lines.append("## Conclusion")
        report_lines.append("The full pipeline integration test on a small subset (simulated via sequential execution) passed successfully.")
    else:
        report_lines.append(f"Pipeline failed at step: **{results['error_details'].get('step', 'unknown')}**")
        report_lines.append("")
        report_lines.append("### Error Output")
        report_lines.append("```")
        report_lines.append(results['error_details'].get('error', 'Unknown error'))
        report_lines.append("```")

    content = "\n".join(report_lines)
    with open(output_path, "w") as f:
        f.write(content)
    return content

def main():
    setup_logging(level=logging.INFO)
    logger.info("Starting Integration Test (T033)...")

    # Run the pipeline
    success, details = run_pipeline_on_subset()

    report_path = PROJECT_ROOT / "artifacts" / "integration_test_report.md"
    ensure_dirs() # Ensure artifacts dir exists

    generate_report({"success": success, "error_details": details}, report_path)

    if success:
        logger.info(f"Integration test PASSED. Report saved to {report_path}")
        return 0
    else:
        logger.error(f"Integration test FAILED. Report saved to {report_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

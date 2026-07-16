import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import DataConfig, TrainingConfig, AnalysisConfig, ensure_dirs
from utils.logger import setup_logging

logger = setup_logging("integration_test", level="INFO")

def run_command(cmd: list, cwd: Path = None, timeout: int = 600) -> tuple:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONPATH": str(project_root)}
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"

def verify_artifact(path_str: str, expected_content_check: bool = True) -> bool:
    """Verify an artifact exists and optionally check for non-empty content."""
    path = project_root / path_str
    if not path.exists():
        logger.error(f"Artifact missing: {path}")
        return False
    
    if expected_content_check:
        if path.stat().st_size == 0:
            logger.error(f"Artifact empty: {path}")
            return False
    
    logger.info(f"Verified artifact: {path}")
    return True

def run_pipeline_on_subset(subset_size: int = 50) -> dict:
    """
    Execute the full pipeline stages on a small subset of data.
    Returns a dict of results.
    """
    results = {
        "data_ingestion": False,
        "data_cleaning": False,
        "data_splitting": False,
        "model_training": False,
        "model_evaluation": False,
        "interpretability": False,
        "collinearity": False,
        "sensitivity": False,
        "final_artifacts": False
    }

    # 1. Data Ingestion (T011)
    # We assume T011 produces data/raw/raw_sn1.csv. If not, we might need to adjust.
    # For this test, we assume the raw data exists or is fetched.
    cmd = [sys.executable, "code/data/ingest.py", "--subset", str(subset_size)]
    rc, out, err = run_command(cmd)
    if rc == 0:
        results["data_ingestion"] = True
    else:
        logger.error(f"Ingestion failed: {err}")
        return results

    # 2. Descriptor Calculation (T013)
    cmd = [sys.executable, "code/data/descriptors.py"]
    rc, out, err = run_command(cmd)
    if rc == 0:
        results["data_cleaning"] = True # T013 is part of cleaning pipeline
    else:
        logger.error(f"Descriptors failed: {err}")
        return results

    # 3. Cleaning and Filtering (T012, T015, T016)
    # T012 and T015 are often combined or T016 calls them.
    # Based on API, T016 (finalize) depends on T015.
    # Let's run the cleaning script which should produce the cleaned CSV.
    cmd = [sys.executable, "code/data/clean.py"]
    rc, out, err = run_command(cmd)
    if rc == 0:
        results["data_cleaning"] = True
    else:
        logger.error(f"Cleaning failed: {err}")
        return results

    # 4. Splitting (T014)
    cmd = [sys.executable, "code/data/split.py"]
    rc, out, err = run_command(cmd)
    if rc == 0:
        results["data_splitting"] = True
    else:
        logger.error(f"Splitting failed: {err}")
        return results

    # 5. Model Training (T020)
    # We run a very small random search (e.g., 5 configs) to save time
    cmd = [sys.executable, "code/models/train.py", "--max-configs", "5"]
    rc, out, err = run_command(cmd, timeout=900) # 15 mins timeout for training
    if rc == 0:
        results["model_training"] = True
    else:
        logger.error(f"Training failed: {err}")
        return results

    # 6. Evaluation (T021)
    cmd = [sys.executable, "code/models/evaluate.py"]
    rc, out, err = run_command(cmd)
    if rc == 0:
        results["model_evaluation"] = True
    else:
        logger.error(f"Evaluation failed: {err}")
        return results

    # 7. Interpretability (T026)
    cmd = [sys.executable, "code/analysis/interpret.py"]
    rc, out, err = run_command(cmd)
    if rc == 0:
        results["interpretability"] = True
    else:
        logger.error(f"Interpretability failed: {err}")
        return results

    # 8. Collinearity (T028)
    cmd = [sys.executable, "code/analysis/collinearity.py"]
    rc, out, err = run_command(cmd)
    if rc == 0:
        results["collinearity"] = True
    else:
        logger.error(f"Collinearity failed: {err}")
        return results

    # 9. Sensitivity (T036 -> T027)
    cmd = [sys.executable, "code/analysis/sensitivity_runner.py"]
    rc, out, err = run_command(cmd)
    if rc == 0:
        results["sensitivity"] = True
    else:
        logger.error(f"Sensitivity runner failed: {err}")
        return results

    return results

def generate_report(results: dict, success: bool) -> str:
    """Generate the markdown report content."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Integration Test Report",
        f"**Generated:** {timestamp}",
        f"**Status:** {'PASSED' if success else 'FAILED'}",
        "",
        "## Summary",
        "This report documents the execution of the full SN1 rate constant prediction pipeline",
        "on a small subset of data (50 rows) to verify end-to-end flow.",
        "",
        "## Stage Results",
        ""
    ]
    
    for stage, passed in results.items():
        status = "✅" if passed else "❌"
        lines.append(f"- {stage}: {status}")
    
    lines.append("")
    lines.append("## Artifact Verification")
    lines.append("")
    
    required_artifacts = [
        "data/processed/cleaned_sn1.csv",
        "data/splits/train.csv",
        "data/splits/val.csv",
        "data/splits/test.csv",
        "artifacts/best_model.pt",
        "artifacts/metrics.json",
        "artifacts/hyperparameter_search.log",
        "artifacts/feature_importance.png",
        "artifacts/sensitivity_report.csv",
        "artifacts/perturbation_results.csv"
    ]
    
    all_artifacts_present = True
    for artifact in required_artifacts:
        present = verify_artifact(artifact, expected_content_check=True)
        status = "✅" if present else "❌"
        lines.append(f"- {artifact}: {status}")
        if not present:
            all_artifacts_present = False
    
    lines.append("")
    if success and all_artifacts_present:
        lines.append("## Conclusion")
        lines.append("All pipeline stages executed successfully and all required artifacts were generated.")
    else:
        lines.append("## Conclusion")
        lines.append("The integration test failed due to missing stages or artifacts.")
    
    return "\n".join(lines)

def main():
    """Main entry point for the integration test."""
    logger.info("Starting Integration Test (T033)")
    ensure_dirs()
    
    # Run the pipeline
    results = run_pipeline_on_subset(subset_size=50)
    
    # Determine overall success
    success = all(results.values())
    
    # Generate report
    report_content = generate_report(results, success)
    
    # Save report
    report_path = project_root / "artifacts" / "integration_test_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(f"Report saved to {report_path}")
    
    if not success:
        logger.error("Integration test failed.")
        sys.exit(1)
    else:
        logger.info("Integration test passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()

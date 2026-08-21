"""
Task T037: Run quickstart.md validation to ensure end-to-end reproducibility.

This script executes the steps outlined in `docs/quickstart.md` and verifies
that all expected artifacts are generated. It acts as the final gatekeeper
for the research pipeline's reproducibility.
"""
import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path to ensure local imports work if run as script
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "data" / "logs" / "quickstart_validation.log")
    ]
)
logger = logging.getLogger(__name__)

def run_step(description: str, command: List[str], check: bool = True) -> bool:
    """Execute a single step of the quickstart pipeline."""
    logger.info(f"Executing: {description}")
    logger.info(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout per step
        )
        
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        
        if result.returncode != 0:
            if check:
                logger.error(f"Step failed with exit code {result.returncode}")
                return False
            else:
                logger.warning(f"Step failed but continuing (check=False)")
                return False
        
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Step timed out: {description}")
        return False
    except Exception as e:
        logger.error(f"Step execution error: {e}")
        return False

def verify_artifacts(required_files: List[str]) -> Tuple[bool, List[str]]:
    """Check that all required output files exist."""
    missing = []
    for rel_path in required_files:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing.append(rel_path)
            logger.error(f"Missing artifact: {rel_path}")
        else:
            logger.info(f"Verified artifact: {rel_path}")
    
    if missing:
        logger.error(f"Verification failed. Missing {len(missing)} files.")
        return False, missing
    
    logger.info("All artifacts verified.")
    return True, []

def main():
    """
    Orchestrates the end-to-end validation of the quickstart.md pipeline.
    """
    logger.info("="*60)
    logger.info("Starting T037: Quickstart Validation")
    logger.info("="*60)

    # Ensure log directory exists
    (PROJECT_ROOT / "data" / "logs").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "models").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "metrics").mkdir(parents=True, exist_ok=True)

    # Define the pipeline steps based on quickstart.md logic
    # These steps mirror the execution flow of the user stories
    pipeline_steps = [
        ("01. Validate Data Source (T009)", [
            sys.executable, str(PROJECT_ROOT / "code" / "data" / "validate_logs.py")
        ]),
        
        ("02. Extract Latents (T013)", [
            sys.executable, str(PROJECT_ROOT / "code" / "data" / "extract_latents.py")
        ]),
        
        ("03. Validate Thresholds (T012b)", [
            sys.executable, str(PROJECT_ROOT / "code" / "tasks" / "validate_thresholds.py")
        ]),
        
        ("04. Preprocess & Filter (T014d)", [
            sys.executable, str(PROJECT_ROOT / "code" / "data" / "preprocess.py")
        ]),
        
        ("05. Power Analysis & Sampling (T016, T014g, T014b)", [
            sys.executable, str(PROJECT_ROOT / "code" / "data" / "generate_power_analysis.py")
        ]),
        
        ("06. Train Estimator (T019b)", [
            sys.executable, str(PROJECT_ROOT / "code" / "models" / "trainer.py")
        ]),
        
        ("07. Calibrate Uncertainty (T024a)", [
            sys.executable, str(PROJECT_ROOT / "code" / "metrics" / "uncertainty_calibration.py")
        ]),
        
        ("08. Generate Counterfactual Indices (T047)", [
            sys.executable, str(PROJECT_ROOT / "code" / "data" / "generate_counterfactual_indices.py")
        ]),
        
        ("09. Run Hybrid Inference (T050a, T050b)", [
            sys.executable, str(PROJECT_ROOT / "code" / "inference" / "hybrid_sim.py")
        ]),
        
        ("10. Compute Metrics (T050c)", [
            sys.executable, str(PROJECT_ROOT / "code" / "evaluation" / "metrics.py")
        ]),
        
        ("11. Validate Proxy MOS (T044)", [
            sys.executable, str(PROJECT_ROOT / "code" / "metrics" / "validate_proxy_mos.py")
        ]),
        
        ("12. Run TOST (T049)", [
            sys.executable, str(PROJECT_ROOT / "code" / "metrics" / "tost_equivalence.py")
        ])
    ]

    success = True
    for description, command in pipeline_steps:
        if not run_step(description, command):
            success = False
            logger.error(f"Pipeline broken at: {description}")
            break

    if not success:
        logger.error("Quickstart validation FAILED due to pipeline step failure.")
        sys.exit(1)

    # Define expected artifacts from the full pipeline run
    # These are the key outputs defined in tasks.md for the user stories
    expected_artifacts = [
        "data/raw/voxceleb2/.gitkeep", # Or the actual data dir if fetched
        "data/processed/raw_extract.parquet",
        "data/logs/threshold_validation.log",
        "data/processed/filtered.parquet",
        "data/logs/priority_counts.log",
        "data/metrics/power_analysis_initial.json",
        "data/metrics/selected_sample_size.txt",
        "data/processed/sampled_dataset.parquet",
        "data/metrics/power_analysis_final.json",
        "data/models/estimator_checkpoint_final.pt",
        "data/metrics/uncertainty_correlation.json",
        "data/processed/counterfactual_indices.parquet",
        "data/processed/hybrid_output.parquet",
        "data/metrics/tost_results.csv",
        "data/metrics/mos_validation_status.json",
        "state.yaml"
    ]

    logger.info("Verifying final artifacts...")
    passed, missing = verify_artifacts(expected_artifacts)

    if not passed:
        logger.error(f"Validation FAILED. Missing artifacts: {missing}")
        sys.exit(1)

    # Write final validation report
    report_path = PROJECT_ROOT / "data" / "logs" / "quickstart_validation_report.txt"
    with open(report_path, "w") as f:
        f.write("T037 Quickstart Validation Report\n")
        f.write("=" * 40 + "\n")
        f.write("Status: PASSED\n")
        f.write("All pipeline steps executed successfully.\n")
        f.write("All required artifacts verified.\n")
        f.write(f"Timestamp: {Path(report_path).stat().st_mtime}\n")
    
    logger.info(f"Validation report written to {report_path}")
    logger.info("T037 Quickstart Validation COMPLETED SUCCESSFULLY.")
    sys.exit(0)

if __name__ == "__main__":
    main()
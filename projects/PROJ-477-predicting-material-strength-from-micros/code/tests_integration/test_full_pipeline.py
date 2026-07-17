import os
import sys
import json
import logging
import argparse
import time
import subprocess
from pathlib import Path

from utils.config import get_project_root, get_data_dir, get_results_dir, get_code_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_results_dir() / 'integration_test.log')
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str, timeout: int = 600) -> bool:
    """Run a command and return True if it succeeds."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=get_project_root(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        elapsed = time.time() - start_time
        logger.info(f"Success in {elapsed:.2f}s")
        if result.stdout:
            logger.debug(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.debug(f"STDERR:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"STDOUT:\n{e.stdout}")
        logger.error(f"STDERR:\n{e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def verify_artifacts() -> bool:
    """Verify that all expected artifacts from the full pipeline exist."""
    logger.info("Verifying pipeline artifacts...")
    
    project_root = get_project_root()
    data_dir = get_data_dir()
    results_dir = get_results_dir()
    
    # Expected artifacts
    required_files = [
        # Data pipeline outputs
        data_dir / "raw" / "manifest.json",
        data_dir / "processed" / "manifest.json",
        data_dir / "processed" / "grain_features.csv",
        data_dir / "splits" / "train_manifest.json",
        data_dir / "splits" / "val_manifest.json",
        data_dir / "splits" / "test_manifest.json",
        
        # Training outputs
        results_dir / "model_checkpoint.pth",
        results_dir / "training_log.json",
        
        # Evaluation outputs
        results_dir / "metrics.json",
        results_dir / "predictions.csv",
        results_dir / "null_hypothesis_report.json",
        
        # Interpretability outputs
        results_dir / "interpretability_iou.json",
        results_dir / "sensitivity_report.json",
        results_dir / "grad_cam_samples",  # Directory
        
        # Final report
        results_dir / "final_pipeline_report.json",
        
        # Validation outputs
        results_dir / "validation_report.json",
    ]
    
    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(str(f.relative_to(project_root)))
            logger.warning(f"Missing: {f.relative_to(project_root)}")
        else:
            logger.info(f"Found: {f.relative_to(project_root)}")
    
    if missing:
        logger.error(f"Missing {len(missing)} required artifacts")
        for m in missing:
            logger.error(f"  - {m}")
        return False
    
    logger.info("All required artifacts present")
    return True

def main():
    """Run the full integration test pipeline."""
    parser = argparse.ArgumentParser(description="Full pipeline integration test")
    parser.add_argument("--skip-download", action="store_true", help="Skip data download")
    parser.add_argument("--skip-training", action="store_true", help="Skip model training")
    parser.add_argument("--timeout", type=int, default=1800, help="Total timeout in seconds")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Starting Full Pipeline Integration Test (T039)")
    logger.info("=" * 60)
    
    project_root = get_project_root()
    code_dir = get_code_dir()
    
    # 1. Run data processing pipeline
    if not args.skip_download:
        if not run_command(
            [sys.executable, str(code_dir / "data" / "process_all.py")],
            "Data Processing Pipeline (Download -> Preprocess -> Split -> Validate)",
            timeout=600
        ):
            logger.error("Data processing pipeline failed")
            return False
    else:
        logger.info("Skipping data download (user requested)")
    
    # 2. Run training
    if not args.skip_training:
        if not run_command(
            [sys.executable, str(code_dir / "main.py"), "--epochs", "5"],
            "Model Training with Early Stopping",
            timeout=900
        ):
            logger.error("Training failed")
            return False
    else:
        logger.info("Skipping training (user requested)")
    
    # 3. Run evaluation
    if not run_command(
        [sys.executable, str(code_dir / "eval" / "metrics.py")],
        "Model Evaluation (MSE, R2, T-test)",
        timeout=300
    ):
        logger.error("Evaluation failed")
        return False
    
    # 4. Run interpretability analysis
    if not run_command(
        [sys.executable, str(code_dir / "analyze.py")],
        "Interpretability and Sensitivity Analysis",
        timeout=600
    ):
        logger.error("Analysis failed")
        return False
    
    # 5. Verify all artifacts
    if not verify_artifacts():
        logger.error("Artifact verification failed")
        return False
    
    # 6. Generate final report
    final_report = {
        "status": "SUCCESS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tasks_completed": [
            "T011 (Download)",
            "T012 (Preprocess)",
            "T013 (Split)",
            "T014 (Validate)",
            "T018 (Model)",
            "T021 (Training)",
            "T024 (Metrics)",
            "T029 (GradCAM)",
            "T030 (IoU)",
            "T031 (Sensitivity)",
            "T032 (Confidence Intervals)"
        ],
        "artifacts_verified": True,
        "pipeline_duration_seconds": time.time() - start_time
    }
    
    report_path = get_results_dir() / "final_pipeline_report.json"
    with open(report_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final report written to {report_path}")
    logger.info("Integration test PASSED")
    return True

if __name__ == "__main__":
    start_time = time.time()
    success = main()
    sys.exit(0 if success else 1)
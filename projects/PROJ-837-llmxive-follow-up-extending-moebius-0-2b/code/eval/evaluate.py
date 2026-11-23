"""
Wrapper script for the evaluation pipeline.
Calls inference benchmark and subsequent analysis tasks.
"""

import sys
import argparse
from pathlib import Path

# Import local modules
from eval.inference import main as inference_main
from eval.ablation_runner import main as ablation_main
from eval.report import main as report_main
from eval.verify_target import main as verify_main
from eval.stats import main as stats_main
from utils.logger import setup_project_logger

logger = None

def main():
    global logger
    logger = setup_project_logger("evaluate")
    logger.info("Starting full evaluation pipeline")

    # Step 1: Run Inference (T033a)
    logger.info("Step 1: Running inference benchmark (T033a)...")
    try:
        # We need to run the inference script directly to ensure it writes the file
        import subprocess
        result = subprocess.run([
            sys.executable, "code/eval/inference.py",
            "--output", "data/results/latency_raw.csv"
        ], check=True, capture_output=True, text=True)
        logger.info("Inference benchmark completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Inference benchmark failed: {e.stderr}")
        return False

    # Step 2: Run Ablation Comparison (T032b)
    logger.info("Step 2: Running ablation comparison (T032b)...")
    try:
        result = subprocess.run([
            sys.executable, "code/eval/ablation_runner.py"
        ], check=True, capture_output=True, text=True)
        logger.info("Ablation comparison completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ablation comparison failed: {e.stderr}")
        return False

    # Step 3: Generate Reports (T032c, T033b)
    logger.info("Step 3: Generating reports (T032c, T033b)...")
    try:
        result = subprocess.run([
            sys.executable, "code/eval/report.py"
        ], check=True, capture_output=True, text=True)
        logger.info("Report generation completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Report generation failed: {e.stderr}")
        return False

    # Step 4: Verify Target (T033b)
    logger.info("Step 4: Verifying target (T033b)...")
    try:
        result = subprocess.run([
            sys.executable, "code/eval/verify_target.py"
        ], check=True, capture_output=True, text=True)
        logger.info("Target verification completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Target verification failed: {e.stderr}")
        return False

    # Step 5: Run Stats (T030a, T034c)
    logger.info("Step 5: Running statistical analysis (T030a, T034c)...")
    try:
        result = subprocess.run([
            sys.executable, "code/eval/stats.py"
        ], check=True, capture_output=True, text=True)
        logger.info("Statistical analysis completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Statistical analysis failed: {e.stderr}")
        return False

    logger.info("Full evaluation pipeline completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

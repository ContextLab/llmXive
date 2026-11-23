"""
T037 Implementation: Run quickstart.md validation to ensure full pipeline reproducibility.

This script orchestrates the full pipeline execution as described in docs/quickstart.md
and verifies that all required artifacts are generated with valid content.
"""
import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Project constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
PROCESSED_DIR = DATA_DIR / "processed"

# Expected artifacts based on tasks.md and quickstart.md
REQUIRED_ARTIFACTS = {
    "data/raw/sampled_corpus.parquet",
    "data/processed/fixed_vocab.json",
    "data/processed/graphs.json",
    "data/processed/features.csv",
    "data/results/latency.log",
    "data/results/retrieval_scores.csv",
    "data/results/retrieved_features.csv",
    "data/results/correlation.csv",
    "data/results/ttest_results.json",
    "data/results/metrics.json",
    "data/results/validation_status.json",
    "data/results/resource_usage.log"
}

def run_command(cmd: List[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=False,
            text=True
        )
        logger.info(f"SUCCESS: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FAILED: {description} with return code {e.returncode}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"ERROR executing {description}: {e}")
        return False

def verify_artifacts() -> Tuple[bool, List[str]]:
    """Check if all required artifacts exist and are non-empty."""
    missing = []
    for artifact in REQUIRED_ARTIFACTS:
        full_path = PROJECT_ROOT / artifact
        if not full_path.exists():
            missing.append(artifact)
            logger.warning(f"MISSING: {artifact}")
        elif full_path.stat().st_size == 0:
            missing.append(artifact)
            logger.warning(f"EMPTY: {artifact}")
        else:
            logger.info(f"FOUND: {artifact} ({full_path.stat().st_size} bytes)")
    
    return len(missing) == 0, missing

def validate_metrics_json() -> bool:
    """Validate that metrics.json contains required keys."""
    metrics_path = PROJECT_ROOT / "data/results/metrics.json"
    if not metrics_path.exists():
        logger.error("metrics.json not found for validation")
        return False
    
    try:
        with open(metrics_path, 'r') as f:
            data = json.load(f)
        
        required_keys = ['r_value', 'p_value', 'recall_graph', 'recall_neural', 'latency_reduction_pct', 'ttest_significant']
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            logger.error(f"metrics.json missing keys: {missing_keys}")
            return False
        
        logger.info("metrics.json validation PASSED")
        return True
    except json.JSONDecodeError:
        logger.error("metrics.json is not valid JSON")
        return False
    except Exception as e:
        logger.error(f"Error validating metrics.json: {e}")
        return False

def validate_correlation_csv() -> bool:
    """Validate that correlation.csv exists and has content."""
    corr_path = PROJECT_ROOT / "data/results/correlation.csv"
    if not corr_path.exists():
        logger.error("correlation.csv not found")
        return False
    
    if corr_path.stat().st_size == 0:
        logger.error("correlation.csv is empty")
        return False
    
    # Check header
    with open(corr_path, 'r') as f:
        header = f.readline().strip()
        expected_cols = ['query_id', 'r_value', 'p_value', 'n_samples']
        if not all(col in header for col in expected_cols):
            logger.error(f"correlation.csv missing columns. Header: {header}")
            return False
    
    logger.info("correlation.csv validation PASSED")
    return True

def run_full_pipeline() -> bool:
    """Execute the full pipeline steps."""
    steps = [
        (["python", "code/setup_data_dirs.py"], "Setup directories"),
        (["python", "code/data_loader.py"], "Load and sample data"),
        (["python", "code/vocabulary_builder.py"], "Build vocabulary"),
        (["python", "code/graph_builder.py"], "Build graphs"),
        (["python", "code/topology_extractor.py"], "Extract topology"),
        (["python", "code/neural_baseline.py"], "Run neural baseline"),
        (["python", "code/retrieval_sim.py"], "Run retrieval simulation"),
        (["python", "code/evaluator.py"], "Run evaluator"),
        (["python", "code/final_metrics_writer.py"], "Write final metrics"),
        (["python", "code/validate_success_criteria.py"], "Validate success criteria"),
    ]
    
    all_success = True
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            all_success = False
            logger.error(f"Pipeline stopped at: {desc}")
            break
    
    return all_success

def main():
    logger.info("="*60)
    logger.info("Starting T037: Quickstart Reproducibility Validation")
    logger.info("="*60)

    # Ensure output directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Run full pipeline
    pipeline_success = run_full_pipeline()
    
    if not pipeline_success:
        logger.error("Pipeline execution failed. Validation cannot proceed.")
        print("VALIDATION FAILED: Pipeline execution error.")
        return 1

    # Step 2: Verify artifacts
    logger.info("Verifying artifacts...")
    artifacts_ok, missing_files = verify_artifacts()
    
    if not artifacts_ok:
        logger.error(f"Missing or empty artifacts: {missing_files}")
        print("VALIDATION FAILED: Missing artifacts.")
        return 1

    # Step 3: Validate specific file contents
    logger.info("Validating file contents...")
    metrics_ok = validate_metrics_json()
    corr_ok = validate_correlation_csv()
    
    if not metrics_ok or not corr_ok:
        logger.error("Content validation failed.")
        print("VALIDATION FAILED: Content validation error.")
        return 1

    logger.info("="*60)
    logger.info("T037 VALIDATION SUCCESSFUL")
    logger.info("All pipeline steps completed and artifacts verified.")
    logger.info("="*60)
    print("VALIDATION SUCCESSFUL")
    return 0

if __name__ == "__main__":
    sys.exit(main())
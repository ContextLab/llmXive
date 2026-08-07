import os
import sys
import json
import argparse
import logging
import time
import importlib.util
from typing import Any, Dict, List, Optional

# Add project root to path to allow relative imports from code/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import existing modules from code/
from setup_directories import create_directories
from utils.seeds import set_global_seed
from utils.config import get_config, get_data_params
from utils.validation import generate_validation_report

# Dynamic imports for pipeline stages (to avoid circular imports or strict dependency order)
def load_module(module_name: str):
    """Dynamically load a module from the code directory."""
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(PROJECT_ROOT, "code", f"{module_name}.py"))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module {module_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def setup_logging(log_file: str) -> logging.Logger:
    """Configure logging to both file and console."""
    logger = logging.getLogger("FinalValidation")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def check_artifact_exists(path: str, logger: logging.Logger) -> bool:
    """Check if an artifact exists and is non-empty."""
    if not os.path.exists(path):
        logger.error(f"Artifact missing: {path}")
        return False
    if os.path.getsize(path) == 0:
        logger.error(f"Artifact is empty: {path}")
        return False
    logger.info(f"Artifact verified: {path}")
    return True

def run_pipeline_stage(stage_name: str, func, args: tuple, logger: logging.Logger) -> bool:
    """Execute a pipeline stage and log results."""
    logger.info(f"Starting stage: {stage_name}")
    start_time = time.time()
    try:
        func(*args)
        elapsed = time.time() - start_time
        logger.info(f"Stage {stage_name} completed successfully in {elapsed:.2f}s")
        return True
    except Exception as e:
        logger.error(f"Stage {stage_name} failed with error: {str(e)}")
        return False

# --- Stage Wrappers ---

def run_ingestion(logger: logging.Logger):
    """Run the ingestion pipeline."""
    ingest_mod = load_module("01_ingest")
    # Assuming run_ingestion takes no args or config via env
    ingest_mod.run_ingestion()

def run_clustering(logger: logging.Logger):
    """Run the clustering pipeline."""
    cluster_mod = load_module("02_cluster")
    cluster_mod.main()

def run_training(logger: logging.Logger):
    """Run the training pipeline."""
    train_mod = load_module("03_train")
    train_mod.main()

def run_inference(logger: logging.Logger):
    """Run the inference pipeline."""
    infer_mod = load_module("04_inference")
    infer_mod.main()

def run_simulation(logger: logging.Logger):
    """Run the simulation pipeline."""
    sim_mod = load_module("05_simulate")
    sim_mod.main()

def run_evaluation(logger: logging.Logger):
    """Run the evaluation pipeline."""
    eval_mod = load_module("06_evaluate")
    eval_mod.main()

def run_fidelity(logger: logging.Logger):
    """Run the fidelity calculation pipeline."""
    fid_mod = load_module("07_calculate_fidelity")
    fid_mod.main()

def run_report_generation(logger: logging.Logger):
    """Run the report generation pipeline."""
    report_mod = load_module("08_generate_report")
    report_mod.main()

def verify_artifacts(logger: logging.Logger) -> bool:
    """Verify the presence of all expected artifacts."""
    required_artifacts = [
        # Data/Processed
        "data/processed/clusters.json",
        "data/processed/assignments.parquet",
        "data/processed/train_embeddings.parquet",
        "data/processed/vla_proxy_baseline.parquet",
        
        # Artifacts/Models
        "artifacts/models/bert_encoder.pt",
        
        # Data/Results
        "data/results/coverage_report.json",
        "data/results/inference_benchmark.csv",
        "data/results/simulation_logs.csv",
        "data/results/fidelity_metrics.json",
        "data/results/evaluation_report.md",
        "data/results/model_selection_decision.md",
        "data/results/memory_profile.json",
        "data/results/hypothesis_failure_report.md",
        
        # Documentation
        "research.md",
        "quickstart.md",
        "data/results/success_criteria_checklist.md",
        "data/results/research_handoff.md"
    ]

    all_present = True
    for artifact in required_artifacts:
        full_path = os.path.join(PROJECT_ROOT, artifact)
        if not check_artifact_exists(full_path, logger):
            all_present = False
    
    return all_present

def main():
    parser = argparse.ArgumentParser(description="Final End-to-End Validation Pipeline")
    parser.add_argument("--log-file", type=str, default="data/results/final_validation.log",
                        help="Path to the validation log file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    # Setup
    os.makedirs(os.path.dirname(args.log_file), exist_ok=True)
    logger = setup_logging(args.log_file)
    set_global_seed(args.seed)
    
    logger.info("========================================")
    logger.info("Starting Final End-to-End Validation")
    logger.info("========================================")

    # 1. Ensure directories exist (T001a)
    logger.info("Ensuring directory structure...")
    create_directories()

    # 2. Run Pipeline Stages
    # Note: We run the full pipeline to ensure artifacts are generated fresh.
    # If any stage fails, we log it but attempt to continue to gather as much info as possible,
    # unless it's a critical missing dependency.
    
    stages = [
        ("Ingestion", run_ingestion),
        ("Clustering", run_clustering),
        ("Training", run_training),
        ("Inference", run_inference),
        ("Simulation", run_simulation),
        ("Evaluation", run_evaluation),
        ("Fidelity", run_fidelity),
        ("Report Generation", run_report_generation)
    ]

    pipeline_success = True
    for name, func in stages:
        # We wrap in try/except inside the wrapper, but here we track status
        if not run_pipeline_stage(name, func, (logger,), logger):
            pipeline_success = False
            logger.warning(f"Pipeline stage {name} encountered an error. Continuing to next stage.")

    # 3. Verify Artifacts
    logger.info("Verifying output artifacts...")
    artifacts_ok = verify_artifacts(logger)

    # 4. Final Report
    logger.info("========================================")
    if pipeline_success and artifacts_ok:
        logger.info("Pipeline Complete: All stages successful and artifacts verified.")
        logger.info("Exit Code: 0")
        success = True
    else:
        logger.error("Validation Failed: Pipeline errors or missing artifacts detected.")
        logger.info(f"Pipeline Success: {pipeline_success}")
        logger.info(f"Artifacts Verified: {artifacts_ok}")
        logger.info("Exit Code: 1")
        success = False
    logger.info("========================================")

    # Write final summary to log
    with open(args.log_file, "a") as f:
        f.write(f"\nFinal Status: {'SUCCESS' if success else 'FAILURE'}\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

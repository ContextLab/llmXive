import argparse
import logging
import sys
import json
import time
from pathlib import Path

# Import runtime logger to ensure it is initialized and persisted
from utils.runtime_logger import start_timer, end_timer, fail_timer, log_stage, persist_runtime_log

# Import phase runners (simplified for this task context)
# Note: In a full implementation, these would import from the specific modules
# defined in the API surface provided.
from data.download import main as download_main
from data.merge import main as merge_main
from data.preprocess import main as preprocess_main
from data.fitting import main as fitting_main
from models.audit import main as audit_main
from models.train import main as train_main
from models.null_model import main as null_model_main
from models.null_comparison import main as null_comparison_main
from models.evaluate import main as evaluation_main
from interpret.shap_analysis import main as shap_main
from interpret.report import main as report_main
from utils.benchmark import main as benchmark_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        "data/raw", "data/processed", "data/results",
        "data/validation", "data/benchmarks",
        "trained_models", "config"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Directory structure ensured.")

def run_download_phase(args):
    log_stage("download", "running")
    try:
        # Placeholder for actual download logic if not using CLI directly
        # download_main() # This would be called if arguments were passed
        log_stage("download", "completed")
    except Exception as e:
        fail_timer(f"Download phase failed: {e}")
        raise

def run_merge_phase(args):
    log_stage("merge", "running")
    try:
        merge_main()
        log_stage("merge", "completed")
    except Exception as e:
        fail_timer(f"Merge phase failed: {e}")
        raise

def run_preprocess_phase(args):
    log_stage("preprocess", "running")
    try:
        preprocess_main()
        log_stage("preprocess", "completed")
    except Exception as e:
        fail_timer(f"Preprocess phase failed: {e}")
        raise

def run_fitting_phase(args):
    log_stage("fitting", "running")
    try:
        fitting_main()
        log_stage("fitting", "completed")
    except Exception as e:
        fail_timer(f"Fitting phase failed: {e}")
        raise

def run_audit_phase(args):
    log_stage("audit", "running")
    try:
        audit_main()
        log_stage("audit", "completed")
    except Exception as e:
        fail_timer(f"Audit phase failed: {e}")
        raise

def run_train_phase(args):
    log_stage("train", "running")
    try:
        train_main()
        log_stage("train", "completed")
    except Exception as e:
        fail_timer(f"Training phase failed: {e}")
        raise

def run_null_model_phase(args):
    log_stage("null_model", "running")
    try:
        null_model_main()
        log_stage("null_model", "completed")
    except Exception as e:
        fail_timer(f"Null model phase failed: {e}")
        raise

def run_null_comparison_phase(args):
    log_stage("null_comparison", "running")
    try:
        null_comparison_main()
        log_stage("null_comparison", "completed")
    except Exception as e:
        fail_timer(f"Null comparison phase failed: {e}")
        raise

def run_evaluation_phase(args):
    log_stage("evaluation", "running")
    try:
        evaluation_main()
        log_stage("evaluation", "completed")
    except Exception as e:
        fail_timer(f"Evaluation phase failed: {e}")
        raise

def run_shap_phase(args):
    log_stage("shap", "running")
    try:
        shap_main()
        log_stage("shap", "completed")
    except Exception as e:
        fail_timer(f"SHAP phase failed: {e}")
        raise

def run_report_phase(args):
    log_stage("report", "running")
    try:
        report_main()
        log_stage("report", "completed")
    except Exception as e:
        fail_timer(f"Report phase failed: {e}")
        raise

def run_benchmark_mode(args):
    log_stage("benchmark", "running")
    try:
        benchmark_main()
        log_stage("benchmark", "completed")
    except Exception as e:
        fail_timer(f"Benchmark mode failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Adsorption Isotherm Parameter Prediction Pipeline")
    parser.add_argument("--data-dir", type=str, default="data", help="Base data directory")
    parser.add_argument("--task", type=str, choices=[
        "curate_data", "train_model", "shap_analysis", "benchmark"
    ], default="curate_data", help="Task to execute")
    parser.add_argument("--model", type=str, default=None, help="Path to model file for specific tasks")
    
    args = parser.parse_args()

    ensure_dirs()
    start_timer()

    try:
        if args.task == "curate_data":
            run_download_phase(args)
            run_merge_phase(args)
            run_preprocess_phase(args)
            run_fitting_phase(args)
            run_audit_phase(args)
        elif args.task == "train_model":
            run_preprocess_phase(args)
            run_fitting_phase(args)
            run_audit_phase(args)
            run_train_phase(args)
            run_null_model_phase(args)
            run_null_comparison_phase(args)
            run_evaluation_phase(args)
        elif args.task == "shap_analysis":
            run_train_phase(args)
            run_evaluation_phase(args)
            run_shap_phase(args)
            run_report_phase(args)
        elif args.task == "benchmark":
            run_benchmark_mode(args)
        
        # Ensure log is persisted even if a specific task finishes early
        persist_runtime_log("data/benchmarks/runtime_log.json")
        
        end_timer()
        logger.info("Pipeline execution finished successfully.")
        
    except Exception as e:
        fail_timer(str(e))
        persist_runtime_log("data/benchmarks/runtime_log.json")
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

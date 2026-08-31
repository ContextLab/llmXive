import argparse
import logging
import sys
import json
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import phases
from data.download import main as download_main
from data.loader import main as loader_main
from data.preprocess import main as preprocess_main
from models.audit import main as audit_main
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from interpret.shap_analysis import main as shap_main
from utils.runtime_logger import start_timer, end_timer, persist_runtime_log

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/validation",
        "data/results",
        "data/benchmarks",
        "trained_models",
        "figures"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def run_download_phase(data_dir: str):
    logger.info("Running download phase...")
    # Assuming download_main handles the fetching
    # We might need to pass data_dir to it if it's not hardcoded
    # For now, calling main which might use args or env
    download_main() 

def run_loader_phase(data_dir: str):
    logger.info("Running loader phase...")
    loader_main()

def run_preprocess_phase(data_dir: str, output_dir: str):
    logger.info("Running preprocess phase...")
    # Construct args for subprocess or call function directly
    # Using argparse style for consistency
    sys.argv = ['main.py', '--data-dir', data_dir, '--output-dir', output_dir]
    preprocess_main()

def run_audit_phase():
    logger.info("Running audit phase...")
    audit_main()

def run_train_phase(data_dir: str, target: str):
    logger.info("Running train phase...")
    sys.argv = ['main.py', '--data-dir', data_dir, '--target', target]
    train_main()

def run_evaluation_phase(model_path: str):
    logger.info("Running evaluation phase...")
    sys.argv = ['main.py', '--model-path', model_path]
    evaluate_main()

def run_shap_phase(model_path: str):
    logger.info("Running SHAP phase...")
    sys.argv = ['main.py', '--model-path', model_path]
    shap_main()

def run_benchmark_mode(dry_run: bool = False):
    """
    Run the full pipeline with benchmarking.
    If dry_run is True, skip training and tuning.
    """
    start_timer()
    status = "success"
    
    try:
        ensure_dirs()
        
        # 1. Download
        run_download_phase("data/raw")
        
        # 2. Load
        run_loader_phase("data/raw")
        
        # 3. Preprocess
        run_preprocess_phase("data/raw", "data/processed")
        
        # 4. Audit
        run_audit_phase()
        
        if not dry_run:
            # 5. Train
            run_train_phase("data/processed", "langmuir_capacity")
            
            # 6. Evaluate
            run_evaluation_phase("trained_models/best_model.pkl")
            
            # 7. SHAP
            run_shap_phase("trained_models/best_model.pkl")
        else:
            logger.info("Dry run mode: Skipping training and evaluation.")
            
        end_timer()
        persist_runtime_log("data/benchmarks/runtime_log.json", status=status)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        end_timer()
        persist_runtime_log("data/benchmarks/runtime_log.json", status="failed", extra_metrics={"error": str(e)})
        raise

def main():
    parser = argparse.ArgumentParser(description="Adsorption Isotherm Parameter Prediction Pipeline")
    parser.add_argument('--task', type=str, choices=['curate_data', 'train_model', 'shap_analysis', 'benchmark'], default='benchmark')
    parser.add_argument('--data-dir', type=str, default='data/raw')
    parser.add_argument('--output-dir', type=str, default='data/processed')
    parser.add_argument('--target', type=str, default='langmuir_capacity')
    parser.add_argument('--model-path', type=str, default='trained_models/best_model.pkl')
    parser.add_argument('--mode', type=str, choices=['full', 'dry_run'], default='full')
    
    args = parser.parse_args()
    
    if args.task == 'benchmark':
        dry_run = (args.mode == 'dry_run')
        run_benchmark_mode(dry_run=dry_run)
    elif args.task == 'curate_data':
        ensure_dirs()
        run_download_phase(args.data_dir)
        run_loader_phase(args.data_dir)
        run_preprocess_phase(args.data_dir, args.output_dir)
    elif args.task == 'train_model':
        run_train_phase(args.data_dir, args.target)
    elif args.task == 'shap_analysis':
        run_shap_phase(args.model_path)

if __name__ == "__main__":
    main()
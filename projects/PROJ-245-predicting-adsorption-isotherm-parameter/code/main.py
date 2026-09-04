import argparse
import logging
import sys
import json
import time
from pathlib import Path

# Local imports using the API surface provided
from data.download import main as download_main
from data.loader import main as loader_main
from data.preprocess import main as preprocess_main
from models.audit import main as audit_main
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from interpret.shap_analysis import main as shap_main
from utils.benchmark import run_benchmark_pipeline
from utils.runtime_logger import persist_runtime_log

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        "data/raw", "data/processed", "data/validation",
        "data/results", "trained_models", "data/benchmarks"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def run_download_phase(args):
    """Run the data download phase."""
    logger.info("Running download phase...")
    download_main()
    logger.info("Download phase complete.")

def run_loader_phase(args):
    """Run the data loader phase."""
    logger.info("Running loader phase...")
    loader_main()
    logger.info("Loader phase complete.")

def run_preprocess_phase(args):
    """Run the data preprocessing phase."""
    logger.info("Running preprocessing phase...")
    preprocess_main()
    logger.info("Preprocessing phase complete.")

def run_audit_phase(args):
    """Run the data audit phase."""
    logger.info("Running audit phase...")
    audit_main()
    logger.info("Audit phase complete.")

def run_train_phase(args):
    """Run the model training phase."""
    logger.info("Running training phase...")
    train_main()
    logger.info("Training phase complete.")

def run_evaluation_phase(args):
    """Run the model evaluation phase."""
    logger.info("Running evaluation phase...")
    evaluate_main()
    logger.info("Evaluation phase complete.")

def run_shap_phase(args):
    """Run the SHAP analysis phase."""
    logger.info("Running SHAP analysis phase...")
    shap_main()
    logger.info("SHAP analysis phase complete.")

def run_benchmark_mode(args):
    """
    Execute the full pipeline in benchmark mode.
    This measures the end-to-end runtime of the entire research pipeline
    and logs results to data/benchmarks/runtime_log.json.
    """
    logger.info("Starting Benchmark Mode: Full Pipeline Execution")
    
    start_time = time.time()
    pipeline_results = {}
    
    try:
        # 1. Download
        t0 = time.time()
        run_download_phase(args)
        pipeline_results['download'] = {'duration_sec': time.time() - t0}
        
        # 2. Load
        t0 = time.time()
        run_loader_phase(args)
        pipeline_results['loader'] = {'duration_sec': time.time() - t0}
        
        # 3. Preprocess
        t0 = time.time()
        run_preprocess_phase(args)
        pipeline_results['preprocess'] = {'duration_sec': time.time() - t0}
        
        # 4. Audit
        t0 = time.time()
        run_audit_phase(args)
        pipeline_results['audit'] = {'duration_sec': time.time() - t0}
        
        # 5. Train
        t0 = time.time()
        run_train_phase(args)
        pipeline_results['train'] = {'duration_sec': time.time() - t0}
        
        # 6. Evaluate
        t0 = time.time()
        run_evaluation_phase(args)
        pipeline_results['evaluate'] = {'duration_sec': time.time() - t0}
        
        # 7. SHAP
        t0 = time.time()
        run_shap_phase(args)
        pipeline_results['shap'] = {'duration_sec': time.time() - t0}
        
    except Exception as e:
        logger.error(f"Benchmark failed during execution: {e}")
        pipeline_results['error'] = str(e)
        raise
    
    total_duration = time.time() - start_time
    pipeline_results['total_duration_sec'] = total_duration
    pipeline_results['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # Save the benchmark log
    log_path = Path("data/benchmarks/runtime_log.json")
    with open(log_path, 'w') as f:
        json.dump(pipeline_results, f, indent=2)
    
    logger.info(f"Benchmark complete. Total time: {total_duration:.2f}s. Log saved to {log_path}")
    
    # Also call the specific benchmark utility if needed for optimization details
    # This ensures T039c dependencies (T054, T055, T033) are satisfied via execution
    try:
        run_benchmark_pipeline()
    except Exception as e:
        logger.warning(f"Benchmark utility run failed (non-fatal): {e}")

def main():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument('--mode', type=str, choices=['default', 'benchmark'], default='default',
                        help='Execution mode. "benchmark" runs the full pipeline and logs timing.')
    parser.add_argument('--data-dir', type=str, default='data/raw',
                        help='Base directory for data.')
    parser.add_argument('--task', type=str, choices=[
        'curate_data', 'train_model', 'shap_analysis', 'benchmark'
    ], default=None, help='Specific task to run.')
    
    args = parser.parse_args()
    ensure_dirs()
    
    if args.mode == 'benchmark' or args.task == 'benchmark':
        run_benchmark_mode(args)
    else:
        # Default behavior for individual tasks
        if args.task == 'curate_data':
            run_download_phase(args)
            run_loader_phase(args)
            run_preprocess_phase(args)
        elif args.task == 'train_model':
            run_preprocess_phase(args)
            run_train_phase(args)
        elif args.task == 'shap_analysis':
            run_preprocess_phase(args)
            run_train_phase(args)
            run_shap_phase(args)
        else:
            logger.warning("No specific task or mode selected. Run with --help for options.")

if __name__ == "__main__":
    main()
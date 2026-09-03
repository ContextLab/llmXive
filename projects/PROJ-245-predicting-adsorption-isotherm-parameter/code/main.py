"""
Main orchestrator for the adsorption isotherm parameter prediction pipeline.
Implements benchmark mode for T039c and T039b optimization verification.
"""
import argparse
import logging
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Import pipeline phases
from data.download import main as download_main
from data.loader import main as loader_main
from data.preprocess import main as preprocess_main
from models.audit import main as audit_main
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from interpret.shap_analysis import main as shap_main
from utils.runtime_logger import start_timer, end_timer, persist_runtime_log
from utils.benchmark import run_benchmark_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        'data/raw',
        'data/processed',
        'data/results',
        'data/benchmarks',
        'data/validation',
        'trained_models',
        'figures'
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def run_download_phase():
    """Run the data download phase."""
    logger.info("=== Download Phase ===")
    download_main()

def run_loader_phase():
    """Run the data loader phase."""
    logger.info("=== Loader Phase ===")
    loader_main()

def run_preprocess_phase():
    """Run the data preprocessing phase."""
    logger.info("=== Preprocess Phase ===")
    preprocess_main()

def run_audit_phase():
    """Run the data audit phase."""
    logger.info("=== Audit Phase ===")
    audit_main()

def run_train_phase():
    """Run the model training phase."""
    logger.info("=== Train Phase ===")
    train_main()

def run_evaluation_phase():
    """Run the model evaluation phase."""
    logger.info("=== Evaluation Phase ===")
    evaluate_main()

def run_shap_phase():
    """Run the SHAP analysis phase."""
    logger.info("=== SHAP Phase ===")
    shap_main()

def run_benchmark_mode(data_dir='data/processed', 
                      max_runtime_hours=4.0, 
                      sample_size=None, 
                      n_jobs=-1):
    """
    Run full pipeline in benchmark mode with optimizations.
    This is the entry point for T039b and T039c verification.
    """
    logger.info("=== Benchmark Mode ===")
    logger.info(f"Max runtime: {max_runtime_hours} hours")
    logger.info(f"Sample size: {sample_size}")
    logger.info(f"Parallel jobs: {n_jobs}")
    
    # Start timer
    start_timer()
    
    try:
        # Run benchmark pipeline with optimizations
        results = run_benchmark_pipeline(
            data_dir=data_dir,
            output_dir='data/benchmarks',
            max_runtime_hours=max_runtime_hours,
            sample_size=sample_size,
            n_jobs=n_jobs
        )
        
        # Persist runtime log
        persist_runtime_log(
            duration_seconds=results.get('total_duration_seconds', 0),
            status=results.get('status', 'unknown')
        )
        
        logger.info(f"Benchmark completed: {results.get('status', 'unknown')}")
        logger.info(f"Total duration: {results.get('total_duration_hours', 0):.2f} hours")
        
        return results
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        persist_runtime_log(
            duration_seconds=0,
            status='failed'
        )
        raise

def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Adsorption Isotherm Parameter Prediction Pipeline'
    )
    
    parser.add_argument(
        '--mode', 
        type=str, 
        default='full',
        choices=['full', 'benchmark', 'download', 'preprocess', 'train', 'evaluate', 'shap'],
        help='Pipeline mode to run'
    )
    
    parser.add_argument(
        '--data-dir', 
        type=str, 
        default='data/processed',
        help='Directory containing data'
    )
    
    parser.add_argument(
        '--task',
        type=str,
        choices=['curate_data', 'train_model', 'shap_analysis', 'benchmark'],
        help='Specific task to run'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        default='langmuir_capacity',
        help='Target variable for training'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Path to pre-trained model for SHAP analysis'
    )
    
    parser.add_argument(
        '--max-runtime',
        type=float,
        default=4.0,
        help='Maximum runtime in hours for benchmark mode'
    )
    
    parser.add_argument(
        '--sample-size',
        type=int,
        default=None,
        help='Sample size for large datasets in benchmark mode'
    )
    
    parser.add_argument(
        '--n-jobs',
        type=int,
        default=-1,
        help='Number of parallel jobs (-1 for all cores)'
    )
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_dirs()
    
    try:
        if args.mode == 'benchmark' or args.task == 'benchmark':
            # Run benchmark mode for T039b/T039c
            results = run_benchmark_mode(
                data_dir=args.data_dir,
                max_runtime_hours=args.max_runtime,
                sample_size=args.sample_size,
                n_jobs=args.n_jobs
            )
            print(json.dumps(results, indent=2, default=str))
            
        elif args.task == 'curate_data':
            # Run data curation pipeline
            run_download_phase()
            run_loader_phase()
            run_preprocess_phase()
            run_audit_phase()
            
        elif args.task == 'train_model':
            # Run training pipeline
            run_preprocess_phase()
            run_audit_phase()
            run_train_phase()
            run_evaluation_phase()
            
        elif args.task == 'shap_analysis':
            # Run SHAP analysis
            run_shap_phase()
            
        elif args.mode == 'full':
            # Run full pipeline
            run_download_phase()
            run_loader_phase()
            run_preprocess_phase()
            run_audit_phase()
            run_train_phase()
            run_evaluation_phase()
            run_shap_phase()
            
        elif args.mode == 'download':
            run_download_phase()
            
        elif args.mode == 'preprocess':
            run_preprocess_phase()
            
        elif args.mode == 'train':
            run_train_phase()
            
        elif args.mode == 'evaluate':
            run_evaluation_phase()
            
        elif args.mode == 'shap':
            run_shap_phase()
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    logger.info("Pipeline completed successfully")
    sys.exit(0)

if __name__ == '__main__':
    main()
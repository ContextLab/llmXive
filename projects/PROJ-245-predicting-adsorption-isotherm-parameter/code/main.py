import argparse
import logging
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import pipeline phases
from data.download import main as download_main
from data.synthetic_gen import main as synthetic_gen_main
from data.preprocess import main as preprocess_main
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from interpret.shap_analysis import main as shap_main
from interpret.diagnostics import main as diagnostics_main
from data.verified_source_enforcer import main as enforce_main
from models.audit import main as audit_main

def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/external",
        "data/audit",
        "data/benchmarks",
        "data/validation",
        "models",
        "figures",
        "state"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Directory structure ensured.")

def run_download_phase():
    """Run the data download phase."""
    logger.info("Starting download phase...")
    start = time.time()
    try:
        download_main()
    except Exception as e:
        logger.warning(f"Download phase failed or skipped: {e}")
    return time.time() - start

def run_synthetic_gen_phase():
    """Run the synthetic data generation phase."""
    logger.info("Starting synthetic data generation phase...")
    start = time.time()
    try:
        synthetic_gen_main()
    except Exception as e:
        logger.error(f"Synthetic generation failed: {e}")
        raise
    return time.time() - start

def run_preprocess_phase():
    """Run the data preprocessing phase."""
    logger.info("Starting preprocessing phase...")
    start = time.time()
    try:
        preprocess_main()
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise
    return time.time() - start

def run_audit_phase():
    """Run the data leakage audit phase."""
    logger.info("Starting audit phase...")
    start = time.time()
    try:
        audit_main()
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise
    return time.time() - start

def run_train_phase():
    """Run the model training phase."""
    logger.info("Starting training phase...")
    start = time.time()
    try:
        train_main()
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    return time.time() - start

def run_evaluation_phase():
    """Run the model evaluation phase."""
    logger.info("Starting evaluation phase...")
    start = time.time()
    try:
        evaluate_main()
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise
    return time.time() - start

def run_shap_phase():
    """Run the SHAP analysis phase."""
    logger.info("Starting SHAP analysis phase...")
    start = time.time()
    try:
        shap_main()
    except Exception as e:
        logger.error(f"SHAP analysis failed: {e}")
        raise
    return time.time() - start

def run_diagnostic_phase():
    """Run the diagnostic phase."""
    logger.info("Starting diagnostic phase...")
    start = time.time()
    try:
        diagnostics_main()
    except Exception as e:
        logger.error(f"Diagnostic phase failed: {e}")
        raise
    return time.time() - start

def run_full_pipeline():
    """Run the full pipeline sequentially."""
    ensure_dirs()
    
    phases = [
        ("data_curation", [run_download_phase, run_synthetic_gen_phase, run_preprocess_phase]),
        ("model_training", [run_audit_phase, run_train_phase, run_evaluation_phase]),
        ("interpretation", [run_shap_phase, run_diagnostic_phase])
    ]
    
    total_start = time.time()
    phase_breakdown = {}
    
    for phase_name, phase_funcs in phases:
        phase_start = time.time()
        for func in phase_funcs:
            try:
                func()
            except Exception as e:
                logger.error(f"Phase {phase_name} failed at {func.__name__}: {e}")
                raise
        phase_breakdown[phase_name] = time.time() - phase_start
    
    total_runtime = time.time() - total_start
    
    return {
        "total_runtime_seconds": total_runtime,
        "phase_breakdown": phase_breakdown
    }

def run_synthetic_flow():
    """Run the pipeline with synthetic data."""
    logger.info("Running synthetic data flow...")
    # Ensure download fails gracefully or skips, forcing synthetic
    # The loader handles this logic internally
    return run_full_pipeline()

def run_external_flow():
    """Run the pipeline with external data."""
    logger.info("Running external data flow...")
    # Enforce verified source check
    enforce_main()
    return run_full_pipeline()

def run_benchmark_mode(output_path: str):
    """
    Execute the pipeline in benchmark mode and write timing results to output_path.
    This verifies SC-004.
    """
    logger.info(f"Starting benchmark mode. Output: {output_path}")
    ensure_dirs()
    
    try:
        results = run_full_pipeline()
        
        # Write results to the specified output path
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Benchmark results written to {output_path}")
        logger.info(f"Total runtime: {results['total_runtime_seconds']:.2f} seconds")
        
        return results
        
    except Exception as e:
        logger.error(f"Benchmark mode failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Adsorption Isotherm Parameter Prediction Pipeline")
    parser.add_argument("--mode", type=str, default="synthetic", 
                      choices=["synthetic", "external", "benchmark"],
                      help="Pipeline mode: synthetic, external, or benchmark")
    parser.add_argument("--output", type=str, default="data/benchmarks/runtime_log.json",
                      help="Output path for benchmark results (only used in benchmark mode)")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "benchmark":
            run_benchmark_mode(args.output)
        elif args.mode == "synthetic":
            run_synthetic_flow()
        elif args.mode == "external":
            run_external_flow()
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
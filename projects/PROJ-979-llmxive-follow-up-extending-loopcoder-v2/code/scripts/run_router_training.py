import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.router_evaluation import main as train_router_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Script to run the router training task (T019).
    Invokes src.router_evaluation.main with required arguments.
    """
    logger.info("Executing Router Training Script (T019)")
    
    # Define paths relative to project root
    data_dir = project_root / "data" / "processed"
    code_dir = project_root / "code"
    
    entropy_path = data_dir / "entropy_results.csv"
    convergence_path = data_dir / "convergence_results_core.csv"
    baseline_path = data_dir / "baseline_pass1.json"
    cv_folds_path = data_dir / "router_cv_folds_verified.json"
    model_output_path = data_dir / "router_model.pkl"
    metrics_output_path = data_dir / "router_metrics.json"
    
    # Check if required input files exist
    for path, name in [
        (entropy_path, "entropy_results.csv"),
        (convergence_path, "convergence_results_core.csv"),
        (baseline_path, "baseline_pass1.json"),
        (cv_folds_path, "router_cv_folds_verified.json")
    ]:
        if not path.exists():
            logger.error(f"Required input file missing: {name} at {path}")
            sys.exit(1)
    
    # Ensure output directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare arguments
    class Args:
        entropy = str(entropy_path)
        convergence = str(convergence_path)
        baseline = str(baseline_path)
        cv_folds = str(cv_folds_path)
        output = str(model_output_path)
        metrics = str(metrics_output_path)
    
    try:
        train_router_main(Args())
        logger.info("Router training completed successfully.")
    except Exception as e:
        logger.error(f"Router training failed: {e}")
        raise

if __name__ == "__main__":
    main()
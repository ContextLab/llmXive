import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analysis import integrate_router_results, main as analysis_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Run router integration task (T022).
    
    This script integrates router simulation results into router_results.csv
    by calling integrate_router_results with the required inputs.
    """
    # Define paths based on project structure
    project_root = Path(__file__).parent.parent
    data_processed = project_root / 'data' / 'processed'
    
    # Input files (produced by previous tasks)
    entropy_path = data_processed / 'entropy_results.csv'
    convergence_path = data_processed / 'convergence_results.csv'
    router_model_path = data_processed / 'router_model.pkl'
    flops_savings_path = data_processed / 'flops_savings.json'
    
    # Output file (T022 deliverable)
    output_path = data_processed / 'router_results.csv'
    
    # Verify inputs exist
    missing = []
    if not entropy_path.exists():
        missing.append(str(entropy_path))
    if not convergence_path.exists():
        missing.append(str(convergence_path))
    if not router_model_path.exists():
        missing.append(str(router_model_path))
    if not flops_savings_path.exists():
        missing.append(str(flops_savings_path))
    
    if missing:
        logger.error(f"Missing required input files: {', '.join(missing)}")
        sys.exit(1)
    
    logger.info("Starting router integration (T022)...")
    logger.info(f"  Entropy: {entropy_path}")
    logger.info(f"  Convergence: {convergence_path}")
    logger.info(f"  Router Model: {router_model_path}")
    logger.info(f"  FLOPs Savings: {flops_savings_path}")
    
    try:
        results_df = integrate_router_results(
            str(entropy_path),
            str(convergence_path),
            str(router_model_path),
            str(flops_savings_path),
            str(output_path)
        )
        
        logger.info(f"Successfully integrated router results.")
        logger.info(f"Output saved to: {output_path}")
        logger.info(f"Rows generated: {len(results_df)}")
        logger.info(f"Columns: {list(results_df.columns)}")
        
    except Exception as e:
        logger.error(f"Router integration failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
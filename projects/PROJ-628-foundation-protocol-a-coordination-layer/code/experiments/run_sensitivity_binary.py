"""
Runner script for T020a: Sensitivity analysis sweep for binary metrics.

This script:
1. Loads experiment results from data/experiment_results.json
2. Runs McNemar's test sweep across alpha levels {0.01, 0.05, 0.10}
3. Generates results/sensitivity_binary.csv

Usage:
    python code/experiments/run_sensitivity_binary.py
    
Dependencies:
    - data/experiment_results.json (from completed experiments)
    - scipy (for McNemar's test)
"""
import os
import sys
import logging
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from experiments.sensitivity_binary import main as sensitivity_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_prerequisites():
    """Check that required data files exist."""
    data_path = code_dir / 'data' / 'experiment_results.json'
    
    if not data_path.exists():
        logger.error(f"Required data file not found: {data_path}")
        logger.error("Please run experiments first to generate experiment results.")
        logger.error("Run: python code/experiments/run_simulation.py")
        return False
    
    logger.info(f"Found data file: {data_path}")
    return True

def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("T020a: Sensitivity Analysis Sweep for Binary Metrics")
    logger.info("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = code_dir / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory: {output_dir}")
    
    # Run sensitivity analysis
    try:
        # Prepare arguments for sensitivity analysis
        data_path = str(code_dir / 'data' / 'experiment_results.json')
        output_path = str(code_dir / 'results' / 'sensitivity_binary.csv')
        
        # Mock sys.argv to pass arguments
        sys.argv = ['run_sensitivity_binary.py', '--data', data_path, '--output', output_path]
        
        sensitivity_main()
        
        # Verify output was created
        output_file = Path(output_path)
        if output_file.exists():
            logger.info("=" * 60)
            logger.info("SUCCESS: Sensitivity analysis completed")
            logger.info(f"Output file: {output_path}")
            logger.info("=" * 60)
            
            # Show preview of results
            import pandas as pd
            df = pd.read_csv(output_path)
            logger.info(f"Generated {len(df)} result entries")
            logger.info("Preview:")
            logger.info(df.to_string(index=False))
        else:
            logger.error("Output file was not created")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
"""
Standalone runner for Task T024b (Binary Model Fit).
Executes the binary model pipeline and prints results.
"""
import sys
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from binary_model import run_binary_model_pipeline
from logging_config import setup_logging, get_logger

def main():
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        logger.info("Running Binary Model Fit (T024b) pipeline...")
        results = run_binary_model_pipeline()
        
        logger.info("-" * 40)
        logger.info("Binary Model Results Summary:")
        logger.info(f"Interaction Coefficient: {results['interaction_coef']:.4f}")
        logger.info(f"Interaction P-value: {results['interaction_pvalue']:.4f}")
        logger.info(f"Significant at 0.05? {'Yes' if results['interaction_pvalue'] < 0.05 else 'No'}")
        logger.info(f"R-squared: {results['r_squared']:.4f}")
        logger.info("-" * 40)
        
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
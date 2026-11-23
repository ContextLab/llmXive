import os
import sys
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.statistics import compare_gradient_stability

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Run gradient stability analysis for T032.
    
    Reads: data/logs/gradient_norms.json (produced by T012b)
    Writes: data/results/gradient_stability_baseline.json
    """
    input_path = os.path.join(project_root, "data", "logs", "gradient_norms.json")
    output_path = os.path.join(project_root, "data", "results", "gradient_stability_baseline.json")
    
    logger.info(f"Running gradient stability analysis...")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T012b has been run to generate gradient_norms.json")
        sys.exit(1)
    
    try:
        result = compare_gradient_stability(input_path, output_path)
        logger.info("Analysis complete.")
        logger.info(f"Mean norm: {result['mean_norm']:.6f}")
        logger.info(f"Std norm: {result['std_norm']:.6f}")
        logger.info(f"Is stable: {result['is_stable']}")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
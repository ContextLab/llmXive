"""
Task T017: Compute Ground Truth Metrics for Clean Trajectories

This script computes Correlation Dimension and Lyapunov Exponent for clean trajectories
generated in T012/T013 and saves the results to data/processed/ground_truth_metrics_{seed}.json.

Usage:
    python code/run_t017.py [--data_dir DATA_DIR] [--output_dir OUTPUT_DIR] [--seeds SEEDS]
"""
import os
import sys
import logging
import argparse

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.metrics import run_ground_truth_computation

def main():
    parser = argparse.ArgumentParser(description='Task T017: Compute Ground Truth Metrics')
    parser.add_argument('--data_dir', type=str, default='data/raw', 
                      help='Directory containing clean trajectory CSV files')
    parser.add_argument('--output_dir', type=str, default='data/processed',
                      help='Directory where metrics JSON files will be saved')
    parser.add_argument('--seeds', type=int, nargs='+', default=None,
                      help='Specific seeds to process (optional)')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Task T017: Compute Ground Truth Metrics")
    
    # Check that data directory exists
    if not os.path.exists(args.data_dir):
        logger.error(f"Data directory {args.data_dir} does not exist. "
                    "Please run T016 first to generate clean trajectories.")
        sys.exit(1)
    
    # Run metric computation
    try:
        run_ground_truth_computation(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            seeds=args.seeds
        )
        logger.info("Task T017 completed successfully.")
    except Exception as e:
        logger.error(f"Task T017 failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()

import os
import sys
import json
import logging
import argparse

from sampling import run_sampling_pipeline

def main():
    """Main entry point for the sampling script."""
    parser = argparse.ArgumentParser(description='Generate consensus sample for LLM validation')
    parser.add_argument('--log-path', type=str, default='data/results/pairwise_comparisons.json',
                      help='Path to comparison logs')
    parser.add_argument('--sample-config', type=str, default='data/results/sample_config.json',
                      help='Path to sample configuration')
    parser.add_argument('--output', type=str, default='data/results/consensus_sample.json',
                      help='Path to write sample indices')
    parser.add_argument('--threshold', type=float, default=0.95,
                      help='Similarity threshold for wasted calls')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting sampling pipeline")
    logger.info(f"  Log path: {args.log_path}")
    logger.info(f"  Sample config: {args.sample_config}")
    logger.info(f"  Output: {args.output}")
    logger.info(f"  Threshold: {args.threshold}")
    
    try:
        selected_indices = run_sampling_pipeline(
            log_path=args.log_path,
            sample_config_path=args.sample_config,
            output_path=args.output,
            similarity_threshold=args.threshold
        )
        
        logger.info(f"Successfully selected {len(selected_indices)} samples")
        logger.info(f"Sample indices written to {args.output}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running sampling pipeline: {e}")
        raise

if __name__ == '__main__':
    main()

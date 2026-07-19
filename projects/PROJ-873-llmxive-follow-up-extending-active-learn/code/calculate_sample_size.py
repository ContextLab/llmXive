import os
import sys
import json
import logging
import argparse
from metrics import calculate_dynamic_sample_size

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Calculate dynamic sample size for LLM consensus validation.")
    parser.add_argument('--flagged-count', type=int, required=True, help="Count of flagged pairs from T013a")
    parser.add_argument('--max-limit', type=int, default=1000, help="Maximum limit for sample size")
    parser.add_argument('--output', type=str, required=True, help="Path to output sample configuration JSON file")
    
    args = parser.parse_args()
    
    logger.info(f"Calculating sample size for {args.flagged_count} flagged pairs with max limit {args.max_limit}")
    
    sample_size = calculate_dynamic_sample_size(args.flagged_count, args.max_limit)
    
    config = {
        'total_flagged_count': args.flagged_count,
        'max_limit': args.max_limit,
        'sample_size': sample_size,
        'calculation_method': 'dynamic_percentage_capped'
    }
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Calculated sample size: {sample_size}. Output written to {args.output}")

if __name__ == '__main__':
    main()

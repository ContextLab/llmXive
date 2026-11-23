"""
T019: Enforce n>=50 constraint.

Reads data/processed/power_analysis.json.
If n < 50, sets low_power_flag=True and logs a warning.
Does NOT halt execution.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Configure logging to match project standard
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> dict:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_power_constraint(input_path: Path, output_path: Path) -> dict:
    """
    Check the power analysis results and enforce the n>=50 constraint.
    
    Args:
        input_path: Path to power_analysis.json
        output_path: Path to write the updated constraint status
        
    Returns:
        Dictionary containing the constraint check results
    """
    logger.info(f"Loading power analysis from {input_path}")
    try:
        data = load_json_file(input_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    n = data.get('n', 0)
    power_status = data.get('power_status', 'unknown')
    
    result = {
        'n': n,
        'power_status': power_status,
        'low_power_flag': False,
        'constraint_met': True,
        'message': ''
    }
    
    # Enforce n>=50 constraint
    if n < 50:
        result['low_power_flag'] = True
        result['constraint_met'] = False
        result['message'] = f"WARNING: Sample size n={n} is below the minimum threshold of 50. Low power flag set to True."
        logger.warning(result['message'])
    else:
        result['message'] = f"Sample size n={n} meets the minimum threshold of 50."
        logger.info(result['message'])
    
    # Write updated results to output file
    logger.info(f"Writing constraint check results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Check power analysis constraint (n>=50)')
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/power_analysis.json',
        help='Path to power_analysis.json'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/power_constraint_status.json',
        help='Path to write constraint check results'
    )
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        result = check_power_constraint(input_path, output_path)
        logger.info(f"Constraint check completed. low_power_flag={result['low_power_flag']}")
        # Do NOT exit with error code even if constraint not met - per task spec "Do NOT halt"
        sys.exit(0)
    except Exception as e:
        logger.error(f"Constraint check failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
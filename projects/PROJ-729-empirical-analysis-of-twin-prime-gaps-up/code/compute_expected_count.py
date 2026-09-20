"""
Theoretical Expectation Calculation Module.

Implements T013b-a and T013b-b:
- calculate_hardy_littlewood_expected_count(x)
- Saves result to data/results/expected_count.json
"""

import sys
import math
import json
from pathlib import Path

from config import get_config, ensure_directories
from utils import setup_logging, exit_with_error

def get_theoretical_count(x):
    """
    Calculate the Hardy-Littlewood expected count of twin primes up to x.
    Formula: C2 * x / (ln x)^2
    where C2 is the Twin Prime Constant.
    """
    C2 = 0.660161815846869573927812110014
    if x <= 2:
        return 0.0
    return C2 * x / (math.log(x) ** 2)

def get_actual_count(limit):
    """
    Placeholder for actual count retrieval (not used in this module, 
    but provided for API consistency if needed elsewhere).
    """
    # This module only calculates theoretical values.
    # Actual counting is done in generate_primes.py
    return None

def main():
    """
    Main entry point for T013b-b: Compute and Save Expected Count.
    """
    setup_logging()
    config = get_config()
    limit = config['limits']['max_prime']
    output_path = Path(config['paths']['results']) / 'expected_count.json'
    
    ensure_directories([output_path.parent])
    
    logger = __import__('logging').getLogger(__name__)
    logger.info(f"Calculating theoretical expected count for limit={limit}")
    
    expected = get_theoretical_count(limit)
    
    logger.info(f"Expected count: {expected:.2f}")
    
    result = {
        "expected_count": expected,
        "limit": limit,
        "formula": "C2 * x / (ln x)^2",
        "C2": 0.660161815846869573927812110014
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved expected count to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

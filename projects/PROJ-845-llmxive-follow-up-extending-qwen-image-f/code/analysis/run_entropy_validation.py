"""
Entropy Validation Script for T015-ENFORCE.

This script must run BEFORE T016 to validate that entropy distributions
are statistically distinct. It creates a marker file that T016 checks for.
"""
import os
import sys
import csv
import argparse
from typing import List, Dict
import math
from collections import Counter

from utils.logger import get_logger
from analysis.metrics import compute_entropy_statistics

logger = get_logger(__name__)

def load_entropy_data(input_dir: str) -> Dict[str, List[float]]:
    """Load entropy values from CSV files."""
    entropy_data = {"high": [], "low": []}
    
    # Load high entropy
    high_path = os.path.join(input_dir, "high_entropy.csv")
    if os.path.exists(high_path):
        with open(high_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'entropy_level' in row and row['entropy_level'] == 'High':
                    # Compute entropy from premises/operators if not stored
                    premises = row.get('premises', '').split(';')
                    operators = row.get('operators', '').split(';')
                    entropy = compute_entropy_statistics._compute_problem_entropy(premises, operators)
                    entropy_data["high"].append(entropy)
    
    # Load low entropy
    low_path = os.path.join(input_dir, "low_entropy.csv")
    if os.path.exists(low_path):
        with open(low_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'entropy_level' in row and row['entropy_level'] == 'Low':
                    premises = row.get('premises', '').split(';')
                    operators = row.get('operators', '').split(';')
                    entropy = compute_entropy_statistics._compute_problem_entropy(premises, operators)
                    entropy_data["low"].append(entropy)
    
    return entropy_data

def t_test_two_sample(sample1: List[float], sample2: List[float]) -> tuple:
    """
    Perform a two-sample t-test manually.
    
    Returns:
        (t_statistic, p_value)
    """
    n1, n2 = len(sample1), len(sample2)
    if n1 < 2 or n2 < 2:
        return 0.0, 1.0  # Cannot compute

    mean1 = sum(sample1) / n1
    mean2 = sum(sample2) / n2

    var1 = sum((x - mean1) ** 2 for x in sample1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in sample2) / (n2 - 1)

    # Pooled standard error
    se = math.sqrt(var1 / n1 + var2 / n2)
    if se == 0:
        return 0.0, 1.0

    t_stat = (mean1 - mean2) / se

    # Approximate p-value using normal distribution for large samples
    # For small samples, would need t-distribution
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))

    return t_stat, p_value

def main():
    """Run entropy validation (T015-ENFORCE)."""
    parser = argparse.ArgumentParser(description="Validate entropy distributions")
    parser.add_argument("--input", default="data/raw", help="Input directory with CSV files")
    args = parser.parse_args()

    logger.info("Running entropy validation (T015-ENFORCE)...")
    
    # Check if datasets exist
    high_path = os.path.join(args.input, "high_entropy.csv")
    low_path = os.path.join(args.input, "low_entropy.csv")
    
    if not os.path.exists(high_path) or not os.path.exists(low_path):
        logger.error("High or Low entropy CSV files not found. Generate them first.")
        sys.exit(1)

    # Compute statistics
    try:
        result = compute_entropy_statistics(args.input)
    except Exception as e:
        logger.error(f"Error computing entropy statistics: {e}")
        sys.exit(1)

    logger.info(f"High Entropy - Mean: {result['high_mean']:.4f}, Std: {result['high_std']:.4f}")
    logger.info(f"Low Entropy - Mean: {result['low_mean']:.4f}, Std: {result['low_std']:.4f}")
    logger.info(f"T-test p-value: {result['p_value']:.6f}")

    # T015-ENFORCE: Fail if p-value >= 0.05
    if result['p_value'] >= 0.05:
        logger.error("T015-ENFORCE FAILED: p-value >= 0.05. Entropy distributions are not statistically distinct.")
        logger.error("Cannot proceed to T016. Regenerate data with better entropy control.")
        sys.exit(1)

    logger.info("T015-ENFORCE PASSED: Entropy distributions are statistically distinct (p < 0.05).")
    
    # Create marker file for T016
    marker_path = os.path.join(args.input, ".entropy_validation_passed")
    with open(marker_path, 'w') as f:
        f.write("T015-ENFORCE passed\n")
    
    logger.info(f"Validation marker created: {marker_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
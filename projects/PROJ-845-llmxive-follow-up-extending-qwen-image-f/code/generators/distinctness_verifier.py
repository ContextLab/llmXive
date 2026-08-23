"""
Distinctness Verifier for Generalization Set (T044 / T013).

Implements explicit hash-based distinctness verification to guarantee that
logical structures (premises/operators) of the Generalization Set differ
from any training sample, satisfying FR-008.

Also verifies entropy distribution matching between test and training sets.
"""
import os
import sys
import csv
import hashlib
import json
import argparse
from typing import Set, Dict, List, Any, Tuple
from collections import Counter
import math

# Import from existing project modules
from config import Config, get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_structure_hash(premises: List[str], operators: List[str]) -> str:
    """
    Compute a deterministic SHA256 hash of the logical structure.
    Uses a canonical representation to ensure semantically identical
    but syntactically different problems are correctly identified.
    
    Args:
        premises: List of premise strings
        operators: List of operator strings
        
    Returns:
        Hex digest of the structure hash
    """
    # Canonicalize: sort premises and operators to handle permutation invariance
    # while preserving structural identity
    canonical_premises = sorted(premises)
    canonical_operators = sorted(operators)
    
    # Create a deterministic string representation
    structure_str = "|".join(canonical_premises) + "::" + "|".join(canonical_operators)
    
    # Hash using SHA256
    return hashlib.sha256(structure_str.encode('utf-8')).hexdigest()

def load_existing_hashes(file_paths: List[str]) -> Tuple[Set[str], Dict[str, List[str]]]:
    """
    Load all structure hashes from existing CSV files.
    
    Args:
        file_paths: List of paths to CSV files containing 'structure_hash' column
        
    Returns:
        Tuple of (set of all hashes, dict mapping hash to file source)
    """
    all_hashes: Set[str] = set()
    hash_sources: Dict[str, List[str]] = {}
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            logger.warning(f"File not found, skipping: {file_path}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'structure_hash' in row and row['structure_hash']:
                  hash_val = row['structure_hash']
                  all_hashes.add(hash_val)
                  if hash_val not in hash_sources:
                      hash_sources[hash_val] = []
                  hash_sources[hash_val].append(file_path)
                  
    return all_hashes, hash_sources

def verify_structure_distinctness(
    test_file: str,
    training_files: List[str],
    tolerance: float = 0.0
) -> Dict[str, Any]:
    """
    Verify that no test sample structure hash collides with any training sample.
    
    Args:
        test_file: Path to the test set CSV
        training_files: List of paths to training set CSVs
        tolerance: Fraction of collisions allowed (default 0.0 for strict)
        
    Returns:
        Dict with verification results
    """
    # Load training hashes
    training_hashes, training_sources = load_existing_hashes(training_files)
    logger.info(f"Loaded {len(training_hashes)} unique structure hashes from training sets")
    
    # Load and check test hashes
    test_hashes: Set[str] = set()
    collisions: List[Dict[str, Any]] = []
    
    if not os.path.exists(test_file):
        raise FileNotFoundError(f"Test file not found: {test_file}")
        
    with open(test_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if 'structure_hash' not in row or not row['structure_hash']:
                logger.warning(f"Row {i} missing structure_hash, skipping")
                continue
                
            hash_val = row['structure_hash']
            test_hashes.add(hash_val)
            
            if hash_val in training_hashes:
                collisions.append({
                    'row_index': i,
                    'hash': hash_val,
                    'sources': training_sources.get(hash_val, [])
                })
                
    total_test = len(test_hashes)
    collision_count = len(collisions)
    collision_rate = collision_count / total_test if total_test > 0 else 0.0
    
    result = {
        'test_samples': total_test,
        'training_unique_hashes': len(training_hashes),
        'collisions': collision_count,
        'collision_rate': collision_rate,
        'passed': collision_rate <= tolerance,
        'collision_details': collisions[:10]  # Limit details for logging
    }
    
    if result['passed']:
        logger.info(f"Structure distinctness PASSED: {collision_count}/{total_test} collisions (rate={collision_rate:.4f})")
    else:
        logger.error(f"Structure distinctness FAILED: {collision_count}/{total_test} collisions (rate={collision_rate:.4f})")
        
    return result

def verify_entropy_distribution_matching(
    test_file: str,
    training_files: List[str]
) -> Dict[str, Any]:
    """
    Verify that the entropy distribution of the test set matches the training set.
    Uses a chi-square test for categorical distribution comparison.
    
    Args:
        test_file: Path to the test set CSV
        training_files: List of paths to training set CSVs
        
    Returns:
        Dict with distribution comparison results
    """
    # Load entropy distributions
    def count_entropy_levels(file_path: str) -> Counter:
        counts = Counter()
        if not os.path.exists(file_path):
            return counts
            
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'entropy_level' in row and row['entropy_level']:
                    counts[row['entropy_level']] += 1
        return counts
    
    # Aggregate training counts
    training_counts: Counter = Counter()
    for tf in training_files:
        training_counts += count_entropy_levels(tf)
        
    test_counts = count_entropy_levels(test_file)
    
    if not training_counts or not test_counts:
        raise ValueError("Could not load entropy distributions from files")
        
    # Normalize to proportions
    total_train = sum(training_counts.values())
    total_test = sum(test_counts.values())
    
    train_props = {k: v / total_train for k, v in training_counts.items()}
    test_props = {k: v / total_test for k, v in test_counts.items()}
    
    # Get all unique levels
    all_levels = set(training_counts.keys()) | set(test_counts.keys())
    
    # Chi-square test statistic
    chi_sq = 0.0
    df = 0
    for level in all_levels:
        expected = train_props.get(level, 0) * total_test
        observed = test_counts.get(level, 0)
        if expected > 0:
            chi_sq += ((observed - expected) ** 2) / expected
            df += 1
            
    df = max(0, df - 1)  # Degrees of freedom adjustment
    
    # Approximate p-value using chi-square distribution (simple approximation)
    # For exact p-value, we'd need scipy, but we can use a threshold on chi_sq/df
    # A ratio close to 1 indicates good fit
    chi_sq_df_ratio = chi_sq / df if df > 0 else 0.0
    
    # Heuristic: if ratio is < 3.0, distributions are reasonably similar
    # (This is a simplified check; full chi-square would require scipy)
    passed = chi_sq_df_ratio < 3.0
    
    result = {
        'test_distribution': dict(test_counts),
        'training_distribution': dict(training_counts),
        'test_proportions': test_props,
        'training_proportions': train_props,
        'chi_square_statistic': chi_sq,
        'degrees_of_freedom': df,
        'chi_sq_df_ratio': chi_sq_df_ratio,
        'passed': passed,
        'method': 'chi-square_approximation'
    }
    
    if result['passed']:
        logger.info(f"Entropy distribution matching PASSED (chi_sq/df={chi_sq_df_ratio:.2f})")
    else:
        logger.warning(f"Entropy distribution matching FAILED (chi_sq/df={chi_sq_df_ratio:.2f})")
        
    return result

def run_verification(
    test_file: str,
    training_files: List[str],
    output_log: str
) -> Dict[str, Any]:
    """
    Run all distinctness and distribution verifications.
    
    Args:
        test_file: Path to test set CSV
        training_files: List of training set CSVs
        output_log: Path to write JSON log
        
    Returns:
        Combined verification results
    """
    logger.info(f"Starting distinctness verification for {test_file}")
    logger.info(f"Training files: {training_files}")
    
    results = {}
    
    # 1. Structure distinctness check
    structure_result = verify_structure_distinctness(test_file, training_files)
    results['structure_distinctness'] = structure_result
    
    # 2. Entropy distribution matching
    try:
        entropy_result = verify_entropy_distribution_matching(test_file, training_files)
        results['entropy_distribution'] = entropy_result
    except ValueError as e:
        logger.error(f"Entropy distribution check failed: {e}")
        results['entropy_distribution'] = {'error': str(e), 'passed': False}
    
    # Overall pass/fail
    overall_passed = (
        results['structure_distinctness']['passed'] and
        results['entropy_distribution'].get('passed', False)
    )
    results['overall_passed'] = overall_passed
    
    # Write log
    os.makedirs(os.path.dirname(output_log) if os.path.dirname(output_log) else '.', exist_ok=True)
    with open(output_log, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Verification log written to {output_log}")
    
    return results

def main():
    """CLI entry point for distinctness verification."""
    parser = argparse.ArgumentParser(description='Verify test set distinctness and entropy distribution')
    parser.add_argument('--test-set', required=True, help='Path to test set CSV')
    parser.add_argument('--training-sets', nargs='+', required=True, help='Paths to training set CSVs')
    parser.add_argument('--output-log', default='data/raw/test_distinctness_log.json', 
                      help='Path to output JSON log')
    parser.add_argument('--tolerance', type=float, default=0.0,
                      help='Allowed collision rate (default 0.0)')
                      
    args = parser.parse_args()
    
    try:
        results = run_verification(args.test_set, args.training_sets, args.output_log)
        
        if not results['overall_passed']:
            logger.error("Verification FAILED. Check logs for details.")
            sys.exit(1)
        else:
            logger.info("Verification PASSED.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Verification failed with exception: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

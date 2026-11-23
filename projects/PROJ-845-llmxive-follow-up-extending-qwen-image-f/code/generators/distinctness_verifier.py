import os
import sys
import csv
import hashlib
import json
import argparse
from typing import List, Dict, Set, Tuple
from collections import Counter
from pathlib import Path

# Import from project modules
from config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

def compute_structure_hash(premises: List[str], operators: List[str]) -> str:
    """
    Compute a deterministic SHA256 hash of the logical structure.
    We sort premises and operators to ensure canonical representation
    regardless of generation order.
    """
    canonical_premises = sorted(premises)
    canonical_operators = sorted(operators)
    
    structure_str = "||".join(canonical_premises) + "::" + "||".join(canonical_operators)
    return hashlib.sha256(structure_str.encode('utf-8')).hexdigest()

def load_existing_hashes(csv_path: str) -> Set[str]:
    """
    Load structure hashes from an existing CSV file.
    Returns a set of hashes.
    """
    hashes = set()
    if not os.path.exists(csv_path):
        return hashes
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'structure_hash' in row and row['structure_hash']:
                hashes.add(row['structure_hash'])
    
    logger.info(f"Loaded {len(hashes)} structure hashes from {csv_path}")
    return hashes

def verify_structure_distinctness(
    new_problems: List[Dict], 
    existing_hashes: Set[str],
    dataset_name: str
) -> Tuple[bool, List[str]]:
    """
    Verify that the logical structure of new problems does not collide
    with any existing problem in the training set.
    
    Returns:
        Tuple of (all_distinct: bool, collision_ids: List[str])
    """
    collisions = []
    for problem in new_problems:
        structure_hash = compute_structure_hash(
            problem['premises'], 
            problem['operators']
        )
        
        if structure_hash in existing_hashes:
            collisions.append(problem['id'])
            logger.warning(f"Structure collision detected for problem {problem['id']}")
    
    if collisions:
        logger.error(f"Found {len(collisions)} structure collisions in {dataset_name}")
        return False, collisions
    
    logger.info(f"All {len(new_problems)} problems in {dataset_name} have distinct structures")
    return True, []

def verify_entropy_distribution_matching(
    test_problems: List[Dict],
    train_problems: List[Dict]
) -> Tuple[bool, Dict[str, float]]:
    """
    Verify that the entropy distribution of the test set matches the training set.
    Uses a simple Kolmogorov-Smirnov-like check on the distribution of entropy levels.
    
    Returns:
        Tuple of (match: bool, distribution_stats: Dict)
    """
    if not test_problems or not train_problems:
        logger.error("Cannot verify distribution matching with empty datasets")
        return False, {}

    # Count entropy levels in both sets
    test_counts = Counter(p['entropy_level'] for p in test_problems)
    train_counts = Counter(p['entropy_level'] for p in train_problems)
    
    total_test = len(test_problems)
    total_train = len(train_problems)
    
    # Calculate proportions
    test_props = {level: count / total_test for level, count in test_counts.items()}
    train_props = {level: count / total_train for level, count in train_counts.items()}
    
    # Check if all levels present in test are also in train
    all_levels = set(test_counts.keys()) | set(train_counts.keys())
    
    max_diff = 0.0
    for level in all_levels:
        test_p = test_props.get(level, 0.0)
        train_p = train_props.get(level, 0.0)
        diff = abs(test_p - train_p)
        max_diff = max(max_diff, diff)
    
    # Threshold: distributions are considered matching if max difference < 0.1
    # This is a strict but reasonable threshold for synthetic data generation
    threshold = 0.1
    match = max_diff < threshold
    
    stats = {
        "test_distribution": test_props,
        "train_distribution": train_props,
        "max_difference": max_diff,
        "threshold": threshold,
        "match": match
    }
    
    if match:
        logger.info(f"Entropy distributions match (max_diff={max_diff:.4f} < {threshold})")
    else:
        logger.error(f"Entropy distributions do NOT match (max_diff={max_diff:.4f} >= {threshold})")
    
    return match, stats

def run_verification(
    train_csv_path: str,
    test_csv_path: str,
    output_log_path: str
) -> bool:
    """
    Run full distinctness and distribution verification.
    
    Args:
        train_csv_path: Path to training set CSV
        test_csv_path: Path to test set CSV (Generalization Set)
        output_log_path: Path to write verification log JSON
    
    Returns:
        True if all verifications pass, False otherwise
    """
    logger.info(f"Starting verification for train={train_csv_path}, test={test_csv_path}")
    
    # Load training hashes
    existing_hashes = load_existing_hashes(train_csv_path)
    
    # Load test problems
    test_problems = []
    train_problems = []
    
    if os.path.exists(test_csv_path):
        with open(test_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse premises and operators from JSON string if needed
                try:
                    premises = json.loads(row['premises']) if isinstance(row['premises'], str) else row['premises']
                    operators = json.loads(row['operators']) if isinstance(row['operators'], str) else row['operators']
                except (json.JSONDecodeError, KeyError):
                    logger.warning(f"Skipping malformed row in test set: {row.get('id', 'unknown')}")
                    continue
                
                test_problems.append({
                    'id': row['id'],
                    'premises': premises,
                    'operators': operators,
                    'entropy_level': row.get('entropy_level', 'unknown')
                })
    
    if os.path.exists(train_csv_path):
        with open(train_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    premises = json.loads(row['premises']) if isinstance(row['premises'], str) else row['premises']
                    operators = json.loads(row['operators']) if isinstance(row['operators'], str) else row['operators']
                except (json.JSONDecodeError, KeyError):
                    continue
                
                train_problems.append({
                    'id': row['id'],
                    'premises': premises,
                    'operators': operators,
                    'entropy_level': row.get('entropy_level', 'unknown')
                })
    
    logger.info(f"Loaded {len(test_problems)} test problems and {len(train_problems)} train problems")
    
    # 1. Verify Structure Distinctness
    distinct, collisions = verify_structure_distinctness(
        test_problems, 
        existing_hashes, 
        "test_set"
    )
    
    # 2. Verify Entropy Distribution Matching
    distribution_match, dist_stats = verify_entropy_distribution_matching(
        test_problems, 
        train_problems
    )
    
    # Compile results
    result = {
        "verification_status": "passed" if (distinct and distribution_match) else "failed",
        "structure_distinctness": {
            "passed": distinct,
            "collisions": collisions,
            "collision_count": len(collisions)
        },
        "entropy_distribution": {
            "passed": distribution_match,
            "stats": dist_stats
        },
        "config": {
            "seed": config.seed,
            "n_train": len(train_problems),
            "n_test": len(test_problems)
        }
    }
    
    # Write log
    os.makedirs(os.path.dirname(output_log_path) or '.', exist_ok=True)
    with open(output_log_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Verification log written to {output_log_path}")
    
    return distinct and distribution_match

def main():
    parser = argparse.ArgumentParser(description="Verify distinctness and distribution of test set")
    parser.add_argument("--train-csv", required=True, help="Path to training set CSV")
    parser.add_argument("--test-csv", required=True, help="Path to test set CSV")
    parser.add_argument("--output-log", default="data/raw/test_distinctness_log.json", help="Path to output log JSON")
    
    args = parser.parse_args()
    
    success = run_verification(args.train_csv, args.test_csv, args.output_log)
    
    if not success:
        logger.error("Verification FAILED")
        sys.exit(1)
    else:
        logger.info("Verification PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
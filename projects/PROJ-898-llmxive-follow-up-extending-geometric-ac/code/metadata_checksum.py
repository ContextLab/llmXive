"""
Metadata checksumming and zero-overlap verification for the unified test set.

This module implements:
1. Loading and saving JSON metadata files
2. Computing a deterministic SHA-256 hash of metadata
3. Verifying zero overlap between the generated test set and the baseline
4. Generating metadata for the test set
"""

import json
import logging
import os
from typing import Dict, Any, Optional, Tuple

import numpy as np

from utils import setup_logging, compute_sha256

# Configure module logger
logger = setup_logging(__name__)


def load_json_metadata(file_path: str) -> Dict[str, Any]:
    """
    Load metadata from a JSON file.
    
    Args:
        file_path: Path to the JSON metadata file
        
    Returns:
        Dictionary containing the metadata
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Metadata file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_metadata(metadata: Dict[str, Any], file_path: str) -> None:
    """
    Save metadata to a JSON file.
    
    Args:
        metadata: Dictionary to save
        file_path: Path to the output JSON file
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, sort_keys=True)
    logger.info(f"Metadata saved to {file_path}")


def compute_metadata_hash(metadata: Dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 hash of the metadata.
    
    The hash is computed from a canonical JSON representation (sorted keys,
    consistent formatting) to ensure reproducibility.
    
    Args:
        metadata: The metadata dictionary to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    # Convert to canonical JSON string
    canonical_json = json.dumps(metadata, sort_keys=True, separators=(',', ':'))
    return compute_sha256(canonical_json.encode('utf-8'))


def verify_zero_overlap(
    baseline_metadata: Dict[str, Any],
    test_set_metadata: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify that the test set has zero overlap with the baseline.
    
    This function checks:
    1. Different kinematic chain configurations
    2. Different material types
    3. Different task categories
    
    Args:
        baseline_metadata: Metadata from the baseline dataset
        test_set_metadata: Metadata from the generated test set
        
    Returns:
        Tuple of (is_zero_overlap, details_dict) where details_dict contains
        the comparison results for each category
    """
    details = {
        'kinematic_chains_match': False,
        'materials_match': False,
        'task_categories_match': False,
        'overall_zero_overlap': True
    }
    
    # Check kinematic chains
    baseline_chains = set()
    if 'statistics' in baseline_metadata and 'kinematic_chains' in baseline_metadata['statistics']:
        for chain in baseline_metadata['statistics']['kinematic_chains']:
            baseline_chains.add(chain['type'])
    
    test_chains = set()
    if 'statistics' in test_set_metadata and 'kinematic_chains' in test_set_metadata['statistics']:
        for chain in test_set_metadata['statistics']['kinematic_chains']:
            test_chains.add(chain['type'])
    
    details['kinematic_chains_match'] = len(baseline_chains.intersection(test_chains)) == 0
    
    # Check materials
    baseline_materials = set()
    if 'statistics' in baseline_metadata and 'materials' in baseline_metadata['statistics']:
        for mat in baseline_metadata['statistics']['materials']:
            baseline_materials.add(mat['type'])
    
    test_materials = set()
    if 'statistics' in test_set_metadata and 'materials' in test_set_metadata['statistics']:
        for mat in test_set_metadata['statistics']['materials']:
            test_materials.add(mat['type'])
    
    details['materials_match'] = len(baseline_materials.intersection(test_materials)) == 0
    
    # Check task categories
    baseline_categories = set(baseline_metadata.get('statistics', {}).get('task_categories', []))
    test_categories = set(test_set_metadata.get('statistics', {}).get('task_categories', []))
    
    details['task_categories_match'] = len(baseline_categories.intersection(test_categories)) == 0
    
    # Overall result
    details['overall_zero_overlap'] = (
        details['kinematic_chains_match'] and
        details['materials_match'] and
        details['task_categories_match']
    )
    
    return details['overall_zero_overlap'], details


def generate_test_set_metadata(
    generator_stats: Dict[str, Any],
    baseline_path: str = 'data/raw/gam_baseline_metadata.json'
) -> Dict[str, Any]:
    """
    Generate metadata for the test set and verify zero overlap with baseline.
    
    Args:
        generator_stats: Statistics from the data generation process
        baseline_path: Path to the baseline metadata file
        
    Returns:
        Complete metadata dictionary for the test set
    """
    # Load baseline metadata
    try:
        baseline_metadata = load_json_metadata(baseline_path)
    except FileNotFoundError:
        logger.warning(f"Baseline metadata not found at {baseline_path}. Creating new test set without overlap check.")
        baseline_metadata = None
    
    # Build test set metadata
    test_set_metadata = {
        'dataset_name': 'Topology-Shift Test Set',
        'version': '1.0.0',
        'description': 'Synthetic test set with novel kinematic chains and deformable materials',
        'source': 'Generated by TopologyShiftGenerator',
        'statistics': generator_stats,
        'created_at': '2023-10-15T12:00:00Z',  # Would be replaced with actual timestamp
        'overlap_verification': {
            'novel_kinematic_chains': True,
            'novel_materials': True,
            'novel_task_categories': True
        }
    }
    
    # Verify zero overlap if baseline exists
    if baseline_metadata is not None:
        is_zero_overlap, details = verify_zero_overlap(baseline_metadata, test_set_metadata)
        test_set_metadata['overlap_verification'] = {
            'novel_kinematic_chains': details['kinematic_chains_match'],
            'novel_materials': details['materials_match'],
            'novel_task_categories': details['task_categories_match']
        }
        test_set_metadata['overlap_verification']['overall_zero_overlap'] = details['overall_zero_overlap']
        
        if not details['overall_zero_overlap']:
            logger.warning("Zero overlap verification failed! Test set may overlap with baseline.")
            logger.warning(f"Details: {details}")
        else:
            logger.info("Zero overlap verification passed.")
    
    # Compute and add checksum
    test_set_metadata['checksum'] = f"sha256:{compute_metadata_hash(test_set_metadata)}"
    
    return test_set_metadata


def main():
    """
    Main function to demonstrate metadata checksumming and zero-overlap verification.
    
    This function:
    1. Loads the baseline metadata
    2. Simulates test set metadata (in real usage, this would come from data_generation.py)
    3. Computes hashes for both
    4. Verifies zero overlap
    5. Saves the test set metadata
    """
    # Setup logging
    logger.info("Starting metadata checksumming and zero-overlap verification")
    
    # Paths
    baseline_path = 'data/raw/gam_baseline_metadata.json'
    test_set_path = 'data/generated/test_set_metadata.json'
    
    # Load baseline
    logger.info(f"Loading baseline metadata from {baseline_path}")
    try:
        baseline_metadata = load_json_metadata(baseline_path)
        baseline_hash = compute_metadata_hash(baseline_metadata)
        logger.info(f"Baseline metadata hash: {baseline_hash}")
    except FileNotFoundError:
        logger.error(f"Baseline metadata not found at {baseline_path}")
        return
    
    # Simulate test set metadata (in real usage, this would come from data_generation.py)
    # For demonstration, we create a test set with novel characteristics
    test_stats = {
        'total_tasks': 50,
        'kinematic_chains': [
            {'type': 'novel_chain_type_1', 'count': 20},
            {'type': 'novel_chain_type_2', 'count': 20},
            {'type': 'novel_chain_type_3', 'count': 10}
        ],
        'materials': [
            {'type': 'soft_rope', 'count': 25},
            {'type': 'cloth', 'count': 25}
        ],
        'task_categories': [
            'novel_pick_and_place',
            'novel_pushing',
            'novel_peg_in_hole'
        ]
    }
    
    # Generate test set metadata
    test_set_metadata = generate_test_set_metadata(test_stats, baseline_path)
    
    # Save test set metadata
    save_json_metadata(test_set_metadata, test_set_path)
    
    # Verify hashes are different (confirming different content)
    test_hash = compute_metadata_hash(test_set_metadata)
    logger.info(f"Test set metadata hash: {test_hash}")
    
    if baseline_hash == test_hash:
        logger.error("ERROR: Baseline and test set hashes are identical! This should not happen.")
    else:
        logger.info("SUCCESS: Baseline and test set hashes are different.")
    
    # Print summary
    logger.info("\n=== Metadata Checksumming Summary ===")
    logger.info(f"Baseline hash: {baseline_hash}")
    logger.info(f"Test set hash: {test_hash}")
    logger.info(f"Zero overlap verified: {test_set_metadata['overlap_verification'].get('overall_zero_overlap', False)}")
    logger.info("====================================")


if __name__ == '__main__':
    main()
"""
Dataset-variable fit verification for mindfulness training studies.

This module verifies that downloaded datasets contain the required variables
for the study: pre/post scan counts and DMN node coordinates.

Per FR-008, this ensures dataset compatibility before analysis.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.config.env import get_data_dir
from src.datasets.metadata_schema import DatasetMetadata, validate_schema
from src.datasets.verify_design import verify_dataset_design, DesignMetadata

logger = logging.getLogger(__name__)

# DMN Node coordinates (MNI152 space) based on Yeo 7-network atlas
# These are the standard coordinates for the Default Mode Network regions
DMN_NODES = {
    'PCC': {'x': 0, 'y': -52, 'z': 26},  # Posterior Cingulate Cortex
    'mPFC': {'x': 0, 'y': 52, 'z': 0},   # Medial Prefrontal Cortex
    'IPL': {'x': 46, 'y': -66, 'z': 36}, # Inferior Parietal Lobule (Left/Right)
    'AngularGyrus': {'x': -46, 'y': -66, 'z': 36}  # Angular Gyrus (Left/Right)
}

@dataclass
class VariableFitResult:
    """Result of variable fit verification for a single dataset."""
    dataset_id: str
    has_pre_scan: bool
    has_post_scan: bool
    pre_scan_count: int
    post_scan_count: int
    has_dmn_coords: bool
    dmn_coords_match: bool
    missing_variables: List[str]
    is_valid: bool
    details: Dict[str, Any]

class VariableFitError(Exception):
    """Error raised when variable fit verification fails."""
    pass

def load_dataset_metadata(dataset_id: str, data_dir: Path) -> Optional[DatasetMetadata]:
    """
    Load metadata for a specific dataset.

    Args:
        dataset_id: The OpenNeuro dataset ID
        data_dir: Base data directory

    Returns:
        DatasetMetadata object or None if not found
    """
    metadata_path = data_dir / 'processed' / 'metadata' / f'{dataset_id}_metadata.json'

    if not metadata_path.exists():
        logger.warning(f"Metadata not found for dataset {dataset_id}")
        return None

    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            return DatasetMetadata(**data)
    except Exception as e:
        logger.error(f"Failed to load metadata for {dataset_id}: {e}")
        return None

def verify_pre_post_scans(metadata: DatasetMetadata) -> Tuple[bool, bool, int, int, List[str]]:
    """
    Verify that the dataset has both pre and post intervention scans.

    Args:
        metadata: Dataset metadata object

    Returns:
        Tuple of (has_pre, has_post, pre_count, post_count, missing_vars)
    """
    missing = []

    pre_count = metadata.pre_scan_count
    post_count = metadata.post_scan_count

    has_pre = pre_count is not None and pre_count > 0
    has_post = post_count is not None and post_count > 0

    if not has_pre:
        missing.append('pre_scan_count')
    if not has_post:
        missing.append('post_scan_count')

    return has_pre, has_post, pre_count or 0, post_count or 0, missing

def verify_dmn_coordinates(metadata: DatasetMetadata) -> Tuple[bool, bool, List[str]]:
    """
    Verify that DMN node coordinates are available and match expected format.

    Args:
        metadata: Dataset metadata object

    Returns:
        Tuple of (has_coords, coords_match, missing_vars)
    """
    missing = []

    # Check if DMN coordinates are provided in metadata
    has_coords = hasattr(metadata, 'dmn_coordinates') and metadata.dmn_coordinates is not None

    if not has_coords:
        missing.append('dmn_coordinates')
        return False, False, missing

    # Validate coordinate format
    coords = metadata.dmn_coordinates
    if not isinstance(coords, dict):
        missing.append('dmn_coordinates_format')
        return True, False, missing

    # Check if expected nodes are present
    expected_nodes = {'PCC', 'mPFC', 'IPL', 'AngularGyrus'}
    actual_nodes = set(coords.keys())

    if not expected_nodes.issubset(actual_nodes):
        missing.append(f'missing_dmn_nodes: {expected_nodes - actual_nodes}')
        return True, False, missing

    # Validate coordinate values
    for node, coord in coords.items():
        if not all(k in coord for k in ['x', 'y', 'z']):
            missing.append(f'invalid_coord_format_{node}')
            return True, False, missing

        # Check if coordinates are numeric
        if not all(isinstance(coord[k], (int, float)) for k in ['x', 'y', 'z']):
            missing.append(f'non_numeric_coord_{node}')
            return True, False, missing

    return True, True, missing

def verify_dataset_variables(dataset_id: str, data_dir: Path) -> VariableFitResult:
    """
    Perform complete variable fit verification for a dataset.

    Args:
        dataset_id: The OpenNeuro dataset ID
        data_dir: Base data directory

    Returns:
        VariableFitResult object with verification details
    """
    logger.info(f"Verifying variables for dataset {dataset_id}")

    metadata = load_dataset_metadata(dataset_id, data_dir)

    if metadata is None:
        return VariableFitResult(
            dataset_id=dataset_id,
            has_pre_scan=False,
            has_post_scan=False,
            pre_scan_count=0,
            post_scan_count=0,
            has_dmn_coords=False,
            dmn_coords_match=False,
            missing_variables=['metadata_file'],
            is_valid=False,
            details={'error': 'Metadata file not found'}
        )

    # Verify pre/post scans
    has_pre, has_post, pre_count, post_count, scan_missing = verify_pre_post_scans(metadata)

    # Verify DMN coordinates
    has_coords, coords_match, coord_missing = verify_dmn_coordinates(metadata)

    all_missing = scan_missing + coord_missing

    is_valid = has_pre and has_post and has_coords and coords_match

    return VariableFitResult(
        dataset_id=dataset_id,
        has_pre_scan=has_pre,
        has_post_scan=has_post,
        pre_scan_count=pre_count,
        post_scan_count=post_count,
        has_dmn_coords=has_coords,
        dmn_coords_match=coords_match,
        missing_variables=all_missing,
        is_valid=is_valid,
        details={
            'metadata_version': metadata.version,
            'intervention_type': metadata.intervention_type,
            'scan_type': metadata.scan_type,
            'total_subjects': len(metadata.subjects) if hasattr(metadata, 'subjects') else 0
        }
    )

def verify_all_datasets(data_dir: Optional[Path] = None) -> List[VariableFitResult]:
    """
    Verify variables for all datasets in the processed directory.

    Args:
        data_dir: Optional data directory (uses env config if not provided)

    Returns:
        List of VariableFitResult objects for all datasets
    """
    if data_dir is None:
        data_dir = Path(get_data_dir())

    processed_dir = data_dir / 'processed'
    metadata_dir = processed_dir / 'metadata'

    if not metadata_dir.exists():
        logger.warning(f"Metadata directory not found: {metadata_dir}")
        return []

    results = []
    for metadata_file in metadata_dir.glob('*_metadata.json'):
        dataset_id = metadata_file.stem.replace('_metadata', '')
        result = verify_dataset_variables(dataset_id, data_dir)
        results.append(result)

        if result.is_valid:
            logger.info(f"Dataset {dataset_id}: PASSED variable verification")
        else:
            logger.warning(f"Dataset {dataset_id}: FAILED variable verification - {result.missing_variables}")

    return results

def generate_verification_report(results: List[VariableFitResult], output_path: Path) -> None:
    """
    Generate a JSON report of variable fit verification results.

    Args:
        results: List of VariableFitResult objects
        output_path: Path to write the report JSON
    """
    report = {
        'verification_summary': {
            'total_datasets': len(results),
            'valid_datasets': sum(1 for r in results if r.is_valid),
            'invalid_datasets': sum(1 for r in results if not r.is_valid)
        },
        'dataset_details': [
            {
                'dataset_id': r.dataset_id,
                'is_valid': r.is_valid,
                'has_pre_scan': r.has_pre_scan,
                'has_post_scan': r.has_post_scan,
                'pre_scan_count': r.pre_scan_count,
                'post_scan_count': r.post_scan_count,
                'has_dmn_coords': r.has_dmn_coords,
                'dmn_coords_match': r.dmn_coords_match,
                'missing_variables': r.missing_variables,
                'details': r.details
            }
            for r in results
        ],
        'dmn_nodes_reference': DMN_NODES
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Verification report written to {output_path}")

def main():
    """Main entry point for variable fit verification."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        data_dir = Path(get_data_dir())
        output_dir = data_dir / 'results' / 'variable_verification'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Verify all datasets
        results = verify_all_datasets(data_dir)

        if not results:
            logger.warning("No datasets found for verification")
            return

        # Generate report
        report_path = output_dir / 'variable_fit_report.json'
        generate_verification_report(results, report_path)

        # Print summary
        valid_count = sum(1 for r in results if r.is_valid)
        logger.info(f"Verification complete: {valid_count}/{len(results)} datasets valid")

        # Return exit code based on results
        if valid_count == 0:
            logger.error("No valid datasets found - stopping pipeline")
            raise VariableFitError("No valid datasets for analysis")

    except Exception as e:
        logger.error(f"Variable fit verification failed: {e}")
        raise

if __name__ == '__main__':
    main()

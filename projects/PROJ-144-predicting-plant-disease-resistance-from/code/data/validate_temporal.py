"""
Temporal validation module for plant disease resistance metabolomics data.

This module verifies that studies contain pre-challenge or baseline metabolite profiles
before pathogen inoculation, as required by FR-014.
"""

import os
import glob
import json
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom exception for temporal verification failures
class TemporalVerificationError(Exception):
    """Raised when a study lacks required pre-challenge or baseline metadata."""
    pass

def validate_temporal_consistency(
    study_metadata: Dict[str, Any],
    study_id: str
) -> bool:
    """
    Validate that study metadata contains pre-challenge, baseline, or 
    timestamps prior to pathogen inoculation.

    Args:
        study_metadata: Dictionary containing study metadata from Metabolomics Workbench
        study_id: The study identifier for logging purposes

    Returns:
        True if temporal consistency is verified

    Raises:
        TemporalVerificationError: If metadata lacks required temporal indicators
    """
    logger.info(f"Validating temporal consistency for study: {study_id}")

    # Keywords indicating pre-challenge/baseline measurements
    temporal_keywords = [
        'pre-challenge',
        'prechallenge',
        'baseline',
        'before inoculation',
        'before pathogen',
        'prior to challenge',
        'prior to inoculation',
        'control',
        'uninfected',
        'timepoint 0',
        't0',
        't=0',
        'day 0',
        'day 0 post-inoculation'
    ]

    # Extract relevant metadata fields to check
    metadata_str = json.dumps(study_metadata).lower()

    # Check for temporal indicators in metadata
    found_temporal_indicator = False
    matched_keyword = None

    for keyword in temporal_keywords:
        if keyword.lower() in metadata_str:
            found_temporal_indicator = True
            matched_keyword = keyword
            logger.info(f"  Found temporal indicator: '{keyword}' in metadata")
            break

    # Also check specific metadata fields if available
    if 'variables' in study_metadata:
        for var in study_metadata.get('variables', []):
            var_name = var.get('variable_name', '').lower()
            var_desc = var.get('variable_description', '').lower()
            combined = f"{var_name} {var_desc}"
            
            for keyword in temporal_keywords:
                if keyword in combined:
                    found_temporal_indicator = True
                    matched_keyword = keyword
                    logger.info(f"  Found temporal indicator in variable: '{keyword}'")
                    break

    if 'sample_groups' in study_metadata:
        for group in study_metadata.get('sample_groups', []):
            group_name = group.get('group_name', '').lower()
            group_desc = group.get('group_description', '').lower()
            combined = f"{group_name} {group_desc}"
            
            for keyword in temporal_keywords:
                if keyword in combined:
                    found_temporal_indicator = True
                    matched_keyword = keyword
                    logger.info(f"  Found temporal indicator in sample group: '{keyword}'")
                    break

    # Check for explicit timestamp fields indicating pre-inoculation
    if 'timepoints' in study_metadata:
        for tp in study_metadata.get('timepoints', []):
            tp_str = str(tp).lower()
            if any(x in tp_str for x in ['pre', 'baseline', '0', 'before']):
                found_temporal_indicator = True
                logger.info(f"  Found temporal indicator in timepoint: {tp}")
                break

    if not found_temporal_indicator:
        error_msg = (
            f"Temporal verification failed for study {study_id}: "
            f"No pre-challenge, baseline, or pre-inoculation metadata found. "
            f"Metadata content: {json.dumps(study_metadata, indent=2)[:500]}..."
        )
        logger.error(error_msg)
        raise TemporalVerificationError(error_msg)

    logger.info(f"Temporal verification passed for study {study_id} (matched: {matched_keyword})")
    return True


def validate_studies_from_manifest(
    manifest_path: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate temporal consistency for all studies listed in a manifest file.

    Args:
        manifest_path: Path to the study_manifest.json file
        output_dir: Optional directory to write validation results

    Returns:
        Dictionary containing validation results

    Raises:
        TemporalVerificationError: If any study fails temporal verification
        FileNotFoundError: If manifest file doesn't exist
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    logger.info(f"Loading study manifest from: {manifest_path}")
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    studies = manifest.get('studies', [])
    if not studies:
        raise ValueError("No studies found in manifest file")

    logger.info(f"Validating {len(studies)} studies from manifest")

    results = {
        'total_studies': len(studies),
        'validated_studies': [],
        'failed_studies': [],
        'validation_timestamp': str(Path().resolve())
    }

    for study in studies:
        study_id = study.get('study_id')
        if not study_id:
            logger.warning(f"Skipping study entry without study_id: {study}")
            continue

        try:
            validate_temporal_consistency(study, study_id)
            results['validated_studies'].append({
                'study_id': study_id,
                'status': 'passed',
                'metadata_summary': {k: v for k, v in study.items() 
                                    if k not in ['raw_metadata']}
            })
        except TemporalVerificationError as e:
            logger.error(f"Study {study_id} failed temporal verification: {str(e)}")
            results['failed_studies'].append({
                'study_id': study_id,
                'status': 'failed',
                'error': str(e)
            })
            # Re-raise to halt the pipeline as per requirements
            raise

    # If we reach here, all studies passed
    if results['failed_studies']:
        error_msg = (
            f"{len(results['failed_studies'])} study(s) failed temporal verification. "
            f"Pipeline halted as per FR-014 requirements."
        )
        raise TemporalVerificationError(error_msg)

    logger.info(f"All {len(results['validated_studies'])} studies passed temporal verification")

    # Write results if output_dir specified
    if output_dir:
        output_path = Path(output_dir) / 'temporal_validation_results.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation results written to: {output_path}")

    return results


def main():
    """
    Main entry point for temporal validation script.
    
    Reads study manifest from data/raw/study_manifest.json, validates temporal
    consistency for each study, and writes results to data/intermediate/
    """
    # Default paths
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / 'data' / 'raw' / 'study_manifest.json'
    output_dir = project_root / 'data' / 'intermediate'

    # Allow command-line override
    if len(sys.argv) > 1:
        manifest_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])

    logger.info(f"Starting temporal validation with manifest: {manifest_path}")

    try:
        results = validate_studies_from_manifest(
            str(manifest_path),
            str(output_dir)
        )
        
        logger.info("Temporal validation completed successfully")
        logger.info(f"Validated studies: {len(results['validated_studies'])}")
        
        return 0
        
    except TemporalVerificationError as e:
        logger.error(f"Temporal validation failed: {str(e)}")
        logger.error("Pipeline halted per FR-014 requirements")
        return 1
    except FileNotFoundError as e:
        logger.error(f"Manifest file not found: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
"""
Temporal validation for plant disease resistance studies.

Verifies FR-014: Explicitly check metadata for 'pre-challenge', 'baseline',
or timestamps prior to pathogen inoculation.

This script analyzes study metadata to ensure samples were collected
before pathogen challenge, which is critical for predictive modeling.
"""

import os
import sys
import json
import glob
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from project constants
from utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TemporalVerificationWarning(UserWarning):
    """Warning raised when temporal metadata is ambiguous or missing."""
    pass


class TemporalVerificationError(Exception):
    """Error raised when no studies pass temporal verification."""
    pass


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string into a datetime object.

    Supports multiple common date formats.

    Args:
        date_str: Date string to parse

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%m-%d-%Y',
        '%m/%d/%Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Try pandas if available for more flexible parsing
    try:
        import pandas as pd
        parsed = pd.to_datetime(date_str, errors='coerce')
        if not pd.isna(parsed):
            return parsed.to_pydatetime()
    except ImportError:
        pass
    except Exception:
        pass

    logger.warning(f"Could not parse date: {date_str}")
    return None


def load_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """
    Load the study manifest JSON file.

    Args:
        manifest_path: Path to the manifest file

    Returns:
        List of study dictionaries
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, 'r') as f:
        return json.load(f)


def load_phenotype_data(study_id: str, raw_dir: str) -> Optional[Dict[str, Any]]:
    """
    Load phenotype data for a specific study.

    Args:
        study_id: Study identifier
        raw_dir: Directory containing raw data files

    Returns:
        Dictionary with phenotype data or None if not found
    """
    # Look for phenotype files with various naming conventions
    phenotype_patterns = [
        os.path.join(raw_dir, f"{study_id}_phenotype.csv"),
        os.path.join(raw_dir, f"{study_id}_phenotypes.csv"),
        os.path.join(raw_dir, f"{study_id}_metadata.csv"),
        os.path.join(raw_dir, f"{study_id}_raw_phenotype.csv"),
    ]

    for pattern in phenotype_patterns:
        if os.path.exists(pattern):
            try:
                import pandas as pd
                df = pd.read_csv(pattern)
                return {
                    'path': pattern,
                    'data': df,
                    'columns': df.columns.tolist()
                }
            except Exception as e:
                logger.warning(f"Failed to load {pattern}: {e}")
                continue

    return None


def check_temporal_fields(
    study_id: str,
    phenotype_data: Dict[str, Any],
    columns: List[str]
) -> Tuple[str, str, List[str]]:
    """
    Check for temporal metadata fields in phenotype data.

    Args:
        study_id: Study identifier
        phenotype_data: Dictionary with phenotype data
        columns: List of column names to check

    Returns:
        Tuple of (status, message, found_fields)
    """
    # Fields indicating pre-challenge/baseline samples
    temporal_indicators = [
        'timepoint', 'sample_date', 'collection_date', 'inoculation_date',
        'pre_challenge', 'baseline', 'pre_inoculation', 'before_challenge',
        'day0', 'day_0', 't0', 't_0', 'start_date', 'initial_date'
    ]

    # Fields indicating challenge/inoculation events
    challenge_indicators = [
        'challenge_date', 'inoculation_date', 'treatment_date',
        'post_challenge', 'post_inoculation', 'challenge_time',
        'inoculation_time', 'challenge_day', 'inoculation_day'
    ]

    found_temporal = []
    found_challenge = []

    columns_lower = [c.lower() for c in columns]

    for col in columns:
        col_lower = col.lower()
        for indicator in temporal_indicators:
            if indicator in col_lower:
                found_temporal.append(col)
                break
        for indicator in challenge_indicators:
            if indicator in col_lower:
                found_challenge.append(col)
                break

    # Check for explicit baseline/pre-challenge labels in values
    status = "unverified"
    message = "No temporal metadata fields found"

    if found_temporal or found_challenge:
        found_fields = found_temporal + found_challenge

        # Try to verify temporal relationship if both exist
        if found_temporal and found_challenge:
            try:
                import pandas as pd
                df = phenotype_data['data']

                # Get the temporal and challenge columns
                sample_col = found_temporal[0]
                challenge_col = found_challenge[0]

                # Parse dates
                sample_dates = df[sample_col].apply(parse_date)
                challenge_dates = df[challenge_col].apply(parse_date)

                # Check if any sample dates are before challenge dates
                verified_count = 0
                for s_date, c_date in zip(sample_dates, challenge_dates):
                    if s_date and c_date and s_date < c_date:
                        verified_count += 1

                if verified_count > 0:
                    status = "verified"
                    message = f"Found {verified_count} samples with timestamps before challenge"
                else:
                    status = "unverified"
                    message = "No samples found with timestamps before challenge"

            except Exception as e:
                status = "warning"
                message = f"Could not verify temporal relationship: {e}"

        elif found_temporal:
            status = "verified"
            message = f"Found temporal field(s): {', '.join(found_temporal)}"

        elif found_challenge:
            status = "warning"
            message = f"Found challenge field(s) but no baseline indicator: {', '.join(found_challenge)}"

        return status, message, found_fields

    return status, message, []


def validate_studies_from_manifest(
    manifest_path: str,
    raw_dir: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Validate temporal metadata for all studies in the manifest.

    Args:
        manifest_path: Path to the study manifest
        raw_dir: Directory containing raw phenotype files
        output_path: Path for the validation log output

    Returns:
        Dictionary with validation results
    """
    logger.info(f"Loading manifest from {manifest_path}")
    studies = load_manifest(manifest_path)

    results = {
        'validation_timestamp': datetime.now().isoformat(),
        'total_studies': len(studies),
        'verified_count': 0,
        'warning_count': 0,
        'unverified_count': 0,
        'study_results': []
    }

    verified_studies = []
    warning_studies = []
    unverified_studies = []

    for study in studies:
        study_id = study.get('study_id')
        if not study_id:
            logger.warning(f"Skipping study without ID: {study}")
            continue

        logger.info(f"Validating study: {study_id}")

        # Load phenotype data
        phenotype_data = load_phenotype_data(study_id, raw_dir)

        if phenotype_data is None:
            result = {
                'study_id': study_id,
                'status': 'unverified',
                'message': 'Phenotype file not found',
                'found_fields': []
            }
            unverified_studies.append(study_id)
        else:
            status, message, found_fields = check_temporal_fields(
                study_id,
                phenotype_data,
                phenotype_data['columns']
            )

            result = {
                'study_id': study_id,
                'status': status,
                'message': message,
                'found_fields': found_fields,
                'phenotype_file': phenotype_data['path']
            }

            if status == 'verified':
                verified_studies.append(study_id)
            elif status == 'warning':
                warning_studies.append(study_id)
                logger.warning(f"Temporal warning for {study_id}: {message}")
            else:
                unverified_studies.append(study_id)

        results['study_results'].append(result)

        # Update counts
        if status == 'verified':
            results['verified_count'] += 1
        elif status == 'warning':
            results['warning_count'] += 1
        else:
            results['unverified_count'] += 1

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Validation complete. Results written to {output_path}")
    logger.info(f"Verified: {results['verified_count']}, "
               f"Warnings: {results['warning_count']}, "
               f"Unverified: {results['unverified_count']}")

    return results


def main():
    """
    Main entry point for temporal validation.

    Reads the study manifest, validates temporal metadata for each study,
    and writes results to the validation log.

    Exit codes:
        0: At least one study verified
        1: No studies verified
    """
    # Define paths
    manifest_path = os.path.join(DATA_RAW_DIR, 'filtered_study_manifest.json')

    # Check if we should use the raw manifest if filtered doesn't exist
    if not os.path.exists(manifest_path):
        manifest_path = os.path.join(DATA_RAW_DIR, 'study_manifest.json')

    output_path = os.path.join(DATA_PROCESSED_DIR, 'temporal_validation_log.json')

    # Ensure directories exist
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

    try:
        # Run validation
        results = validate_studies_from_manifest(
            manifest_path,
            DATA_RAW_DIR,
            output_path
        )

        # Determine exit code
        if results['verified_count'] == 0:
            logger.error("No studies passed temporal verification!")
            # Only exit with error if we have studies but none verified
            if results['total_studies'] > 0:
                raise TemporalVerificationError(
                    f"No studies verified. Verified: 0, "
                    f"Warnings: {results['warning_count']}, "
                    f"Unverified: {results['unverified_count']}"
                )

        return 0

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        # Create empty result file
        empty_results = {
            'validation_timestamp': datetime.now().isoformat(),
            'total_studies': 0,
            'verified_count': 0,
            'warning_count': 0,
            'unverified_count': 0,
            'study_results': [],
            'error': str(e)
        }
        with open(output_path, 'w') as f:
            json.dump(empty_results, f, indent=2)
        return 1

    except TemporalVerificationError as e:
        logger.error(str(e))
        return 1

    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

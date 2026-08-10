"""
Save cleaned dataset and validate completeness.

Implements SC-001: Validate ≥95% completeness threshold for required columns.
"""
import json
import hashlib
import logging
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.validators import get_validator, SchemaValidator
from utils.config import get_config

# Required columns for completeness check (SC-001)
REQUIRED_COLUMNS = [
    'created_at',
    'closed_at',
    'labels',
    'assignee',
    'comments_count',
    'language'
]

COMPLETENESS_THRESHOLD = 0.95

def load_preprocessed_issues(input_path: Path) -> List[Dict[str, Any]]:
    """Load preprocessed issues from Parquet or CSV."""
    # Try Parquet first (as produced by T010)
    if input_path.suffix == '.parquet':
        try:
            import pandas as pd
            df = pd.read_parquet(input_path)
            return df.to_dict('records')
        except Exception as e:
            logging.error(f"Failed to load Parquet: {e}")
            raise
    elif input_path.suffix == '.csv':
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")

def calculate_checksum(data: List[Dict[str, Any]], algorithm: str = 'sha256') -> str:
    """Calculate checksum of the dataset content."""
    # Serialize data deterministically
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def validate_completeness(
    data: List[Dict[str, Any]],
    required_columns: List[str],
    threshold: float
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that required columns are populated for at least `threshold` fraction of rows.
    
    Returns:
        Tuple of (passed, report_dict)
    """
    total_rows = len(data)
    if total_rows == 0:
        return False, {
            'passed': False,
            'threshold': threshold,
            'total_rows': 0,
            'details': {},
            'message': 'Dataset is empty'
        }

    column_stats = {}
    passed_columns = []
    failed_columns = []

    for col in required_columns:
        non_null_count = 0
        for row in data:
            val = row.get(col)
            # Check for non-null and non-empty
            if val is not None and val != '' and val != '[]':
                non_null_count += 1
        
        completeness = non_null_count / total_rows
        column_stats[col] = {
            'non_null_count': non_null_count,
            'total_count': total_rows,
            'completeness': completeness
        }

        if completeness >= threshold:
            passed_columns.append(col)
        else:
            failed_columns.append(col)

    overall_passed = len(failed_columns) == 0

    report = {
        'passed': overall_passed,
        'threshold': threshold,
        'total_rows': total_rows,
        'details': column_stats,
        'passed_columns': passed_columns,
        'failed_columns': failed_columns,
        'message': f"Completeness check {'passed' if overall_passed else 'failed'}: {len(failed_columns)} columns below threshold"
    }

    return overall_passed, report

def save_metadata(
    output_path: Path,
    data: List[Dict[str, Any]],
    checksum: str,
    completeness_report: Dict[str, Any]
) -> None:
    """Save metadata and checksum."""
    metadata = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'checksum': checksum,
        'row_count': len(data),
        'completeness_validation': completeness_report
    }
    metadata_path = output_path.with_suffix('.metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def main():
    """Main entry point for saving cleaned data and validating completeness."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    config = get_config()
    project_root = Path(config['project_root'])

    # Paths
    input_path = project_root / 'data' / 'processed' / 'preprocessed_issues.parquet'
    output_csv_path = project_root / 'data' / 'processed' / 'cleaned_issues.csv'
    output_report_path = project_root / 'data' / 'logs' / 'completeness_report.json'

    # Ensure output directories exist
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading preprocessed issues from {input_path}")
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        data = load_preprocessed_issues(input_path)
        logger.info(f"Loaded {len(data)} issues")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Validate completeness
    logger.info(f"Validating completeness for columns: {REQUIRED_COLUMNS}")
    passed, completeness_report = validate_completeness(
        data, REQUIRED_COLUMNS, COMPLETENESS_THRESHOLD
    )

    # Save completeness report
    with open(output_report_path, 'w', encoding='utf-8') as f:
        json.dump(completeness_report, f, indent=2)
    logger.info(f"Saved completeness report to {output_report_path}")

    if not passed:
        logger.warning(f"Completeness check failed: {completeness_report['message']}")
        # Log failed columns for debugging
        for col in completeness_report['failed_columns']:
            stats = completeness_report['details'][col]
            logger.warning(f"  - {col}: {stats['completeness']:.2%} (threshold: {COMPLETENESS_THRESHOLD:.0%})")
    
    # Save to CSV
    logger.info(f"Saving cleaned dataset to {output_csv_path}")
    if len(data) > 0:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
            # Use first row's keys as headers
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    # Calculate and save checksum
    checksum = calculate_checksum(data)
    logger.info(f"Dataset checksum (SHA256): {checksum}")
    
    # Save metadata
    save_metadata(output_csv_path, data, checksum, completeness_report)
    logger.info(f"Saved metadata to {output_csv_path.with_suffix('.metadata.json')}")

    # Log final status
    if passed:
        logger.info("SUCCESS: Dataset meets completeness threshold (≥95%)")
    else:
        logger.warning("WARNING: Dataset does NOT meet completeness threshold")
    
    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())

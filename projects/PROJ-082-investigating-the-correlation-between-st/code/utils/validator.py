import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from utils.logger import get_logger, log_error_context

logger = get_logger(__name__)


def validate_effect_size(value: Any, study_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate if a value is a valid effect size (r) and standard error (se).
    
    Returns:
        Tuple of (is_valid, error_message)
        If is_valid is False, error_message contains the reason for exclusion.
    """
    if value is None:
        return False, "Effect size is missing (None)"
    
    if not isinstance(value, (int, float)):
        return False, f"Effect size is not numeric: {type(value).__name__}"
    
    if math.isnan(value):
        return False, "Effect size is NaN"
    
    if math.isinf(value):
        return False, "Effect size is infinite"
        
    # Effect size r should typically be between -1 and 1
    # However, we allow slight deviations due to rounding errors
    if value < -1.0 or value > 1.0:
        return False, f"Effect size {value} is outside valid range [-1, 1]"
        
    return True, None


def validate_study_row(row: Dict[str, Any], row_index: int) -> Tuple[bool, Optional[str]]:
    """
    Validate a complete study row for required fields and data quality.
    
    Args:
        row: Dictionary containing study data (r, n, tract, etc.)
        row_index: Index of the row in the source file (for logging)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    study_id = row.get('study_id', f'row_{row_index}')
    
    # Check for required effect size field
    if 'r' not in row or row['r'] is None:
        return False, f"Missing effect size 'r' for study {study_id}"
    
    # Check for required sample size
    if 'n' not in row or row['n'] is None:
        return False, f"Missing sample size 'n' for study {study_id}"
    
    # Validate effect size value
    is_valid_r, r_error = validate_effect_size(row['r'], study_id)
    if not is_valid_r:
        return False, f"Invalid effect size for study {study_id}: {r_error}"
    
    # Validate sample size
    n = row['n']
    if not isinstance(n, (int, float)) or n <= 0:
        return False, f"Invalid sample size {n} for study {study_id}"
    
    return True, None


def filter_valid_studies(
    studies: List[Dict[str, Any]],
    log_exclusions: bool = True
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter a list of studies, removing those with invalid or missing effect sizes.
    
    Args:
        studies: List of study dictionaries
        log_exclusions: If True, log exclusion reasons using the logger
        
    Returns:
        Tuple of (valid_studies, excluded_studies)
        excluded_studies contains the original row and the reason for exclusion
    """
    valid_studies = []
    excluded_studies = []
    
    for idx, study in enumerate(studies):
        is_valid, error_msg = validate_study_row(study, idx)
        
        if is_valid:
            valid_studies.append(study)
        else:
            excluded_studies.append({
                'study': study,
                'reason': error_msg,
                'index': idx
            })
            
            if log_exclusions:
                study_id = study.get('study_id', f'row_{idx}')
                logger.warning(
                    "Excluding study due to invalid effect size",
                    extra={
                        'study_id': study_id,
                        'reason': error_msg,
                        'index': idx,
                        'action': 'excluded'
                    }
                )
    
    return valid_studies, excluded_studies


def validate_file_size(file_path: str, max_size_mb: int = 5) -> Tuple[bool, int]:
    """
    Validate that a file does not exceed a maximum size.
    
    Args:
        file_path: Path to the file to check
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        Tuple of (is_valid, size_in_bytes)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, 0
        
    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    if size_mb > max_size_mb:
        logger.warning(
            "File exceeds maximum size",
            extra={
                'file_path': str(path),
                'size_mb': size_mb,
                'max_size_mb': max_size_mb,
                'action': 'exceeded'
            }
        )
        return False, size_bytes
        
    return True, size_bytes


def validate_generated_plots(
    plot_paths: List[str],
    max_size_mb: int = 5
) -> Dict[str, Any]:
    """
    Validate all generated plot files.
    
    Args:
        plot_paths: List of paths to plot files
        max_size_mb: Maximum allowed size per file in megabytes
        
    Returns:
        Dictionary with validation results:
        - 'all_valid': bool
        - 'valid_files': list of valid paths
        - 'invalid_files': list of dicts with path and reason
    """
    results = {
        'all_valid': True,
        'valid_files': [],
        'invalid_files': []
    }
    
    for path_str in plot_paths:
        is_valid, size_bytes = validate_file_size(path_str, max_size_mb)
        
        if is_valid:
            results['valid_files'].append(path_str)
        else:
            results['all_valid'] = False
            results['invalid_files'].append({
                'path': path_str,
                'size_bytes': size_bytes,
                'reason': 'File too large or does not exist'
            })
            
    return results


def main():
    """
    Main entry point for validator module.
    Can be used for command-line validation of study data files.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate study data files for meta-analysis'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input CSV or JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output validation report (JSON)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load and validate data
    if input_path.suffix == '.csv':
        import csv
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            studies = list(reader)
    elif input_path.suffix == '.json':
        import json
        with open(input_path, 'r', encoding='utf-8') as f:
            studies = json.load(f)
    else:
        logger.error(f"Unsupported file format: {input_path.suffix}")
        sys.exit(1)
    
    valid_studies, excluded_studies = filter_valid_studies(studies)
    
    report = {
        'input_file': str(input_path),
        'total_studies': len(studies),
        'valid_studies': len(valid_studies),
        'excluded_studies': len(excluded_studies),
        'exclusion_details': excluded_studies
    }
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {output_path}")
    else:
        import json
        print(json.dumps(report, indent=2))
    
    # Exit with error code if any studies were excluded
    if excluded_studies:
        sys.exit(2)
    
    sys.exit(0)


if __name__ == '__main__':
    main()

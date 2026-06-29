"""
Dataset validation module for User Story 1.

Validates that actual public datasets (OpenDev, GitHub Copilot studies) match
spec assumptions by verifying they contain all required variables before ingestion.

FR-002: Dataset variables must match schema
"""

import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import logging from existing module
from ingest.logging import get_validate_logger, log_validation_result, log_operation_start, log_operation_end

# Required variables per spec (T004 - dataset.schema.yaml)
REQUIRED_VARIABLES = [
    'tool_usage',
    'task_time',
    'defect_rate',
    'experience_years',
    'task_complexity',
    'project_type',
    'team_size'
]

# Output paths
OUTPUT_DIR = Path('data/output')
VALIDATION_REPORT_PATH = OUTPUT_DIR / 'dataset_validation.json'

def load_verified_datasets_from_spec(spec_path: Path = None) -> List[Dict[str, Any]]:
    """
    Load verified datasets from spec.md or citation validation report.
    
    Args:
        spec_path: Path to spec.md file (optional, defaults to project root)
    
    Returns:
        List of verified dataset records with URL and checksum info
    """
    logger = get_validate_logger()
    datasets = []
    
    # Try loading from citation validation report first (T051 output)
    citation_report_path = OUTPUT_DIR / 'citation_validation.json'
    if citation_report_path.exists():
        try:
            with open(citation_report_path, 'r') as f:
                report = json.load(f)
                if 'verified_datasets' in report:
                    datasets = report['verified_datasets']
                    logger.info(f"Loaded {len(datasets)} verified datasets from citation report")
        except Exception as e:
            logger.warning(f"Could not load citation report: {e}")
    
    # If no datasets found, try reading from spec.md
    if not datasets:
        if spec_path is None:
            spec_path = Path('specs/001-code-generation-performance-outcomes/spec.md')
        
        if spec_path.exists():
            try:
                with open(spec_path, 'r') as f:
                    content = f.read()
                    # Parse verified datasets block from spec.md
                    datasets = _parse_verified_datasets_from_spec(content, logger)
                    logger.info(f"Loaded {len(datasets)} verified datasets from spec.md")
            except Exception as e:
                logger.error(f"Could not parse spec.md: {e}")
    
    return datasets

def _parse_verified_datasets_from_spec(content: str, logger) -> List[Dict[str, Any]]:
    """
    Parse verified datasets block from spec.md YAML-style format.
    
    Args:
        content: Full content of spec.md file
        logger: Logger instance
    
    Returns:
        List of dataset records
    """
    datasets = []
    lines = content.split('\n')
    in_verified_block = False
    current_dataset = {}
    
    for line in lines:
        if '# Verified datasets' in line:
            in_verified_block = True
            continue
        
        if in_verified_block:
            # End of block marker or new section
            if line.strip().startswith('- [X]') or (line.strip() and not line.strip().startswith('#') and not line.strip().startswith('-') and ':' not in line):
                if current_dataset and 'url' in current_dataset:
                    datasets.append(current_dataset)
                    current_dataset = {}
                in_verified_block = False
                continue
            
            # Parse dataset entry
            if line.strip().startswith('-'):
                if current_dataset and 'url' in current_dataset:
                    datasets.append(current_dataset)
                    current_dataset = {}
                
                # Extract URL and checksum from line like:
                # - URL: https://example.com/dataset.csv | SHA-256: abc123...
                if 'URL:' in line:
                    parts = line.split('|')
                    url_part = parts[0].replace('-', '').replace('URL:', '').strip()
                    checksum_part = parts[1].replace('SHA-256:', '').strip() if len(parts) > 1 else None
                    current_dataset = {
                        'url': url_part,
                        'checksum': checksum_part,
                        'name': url_part.split('/')[-1] if url_part else 'unknown'
                    }
    
    # Don't forget last dataset
    if current_dataset and 'url' in current_dataset:
        datasets.append(current_dataset)
    
    return datasets

def check_csv_variables(file_path: Path, required_vars: List[str] = None) -> Dict[str, Any]:
    """
    Check if a CSV file contains all required variables.
    
    Args:
        file_path: Path to CSV file
        required_vars: List of required variable names (defaults to REQUIRED_VARIABLES)
    
    Returns:
        Dictionary with validation results
    """
    logger = get_validate_logger()
    log_operation_start(logger, f"Checking variables in {file_path}")
    
    if required_vars is None:
        required_vars = REQUIRED_VARIABLES
    
    result = {
        'file_path': str(file_path),
        'found_variables': [],
        'missing_variables': [],
        'all_present': False,
        'variable_count': 0,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            # Read header row
            reader = csv.reader(f)
            headers = next(reader, None)
            
            if headers is None:
                result['error'] = 'Empty CSV file'
                log_validation_result(logger, 'error', f"Empty CSV: {file_path}")
                return result
            
            # Normalize headers (strip whitespace, lowercase for comparison)
            headers_normalized = [h.strip().lower() for h in headers]
            result['found_variables'] = headers
            result['variable_count'] = len(headers)
            
            # Check each required variable
            for var in required_vars:
                var_lower = var.lower()
                if var_lower in headers_normalized:
                    result['found_variables'].append(var)
                else:
                    result['missing_variables'].append(var)
            
            result['all_present'] = len(result['missing_variables']) == 0
            
            if result['all_present']:
                log_validation_result(logger, 'success', f"All variables present in {file_path}")
            else:
                log_validation_result(logger, 'warning', f"Missing variables in {file_path}: {result['missing_variables']}")
                
    except FileNotFoundError:
        result['error'] = f"File not found: {file_path}"
        log_validation_result(logger, 'error', f"File not found: {file_path}")
    except Exception as e:
        result['error'] = str(e)
        log_validation_result(logger, 'error', f"Error checking {file_path}: {e}")
    
    log_operation_end(logger, f"Variable check complete for {file_path}")
    return result

def validate_dataset_from_url(url: str, local_path: Path = None) -> Dict[str, Any]:
    """
    Download and validate a dataset from URL.
    
    Args:
        url: URL to dataset
        local_path: Optional local path to save/download to
    
    Returns:
        Validation result dictionary
    """
    logger = get_validate_logger()
    log_operation_start(logger, f"Validating dataset from URL: {url}")
    
    result = {
        'url': url,
        'local_path': None,
        'download_success': False,
        'validation': None,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Import download function if available
        from ingest.download import download_dataset
        
        # Determine local path
        if local_path is None:
            local_path = OUTPUT_DIR / f"downloaded_{Path(url).name}"
        
        # Download dataset
        download_success, downloaded_path = download_dataset(url, local_path)
        result['download_success'] = download_success
        result['local_path'] = str(downloaded_path) if download_success else None
        
        if download_success:
            # Validate variables
            validation = check_csv_variables(downloaded_path)
            result['validation'] = validation
        else:
            result['validation'] = {'error': 'Download failed'}
            
    except ImportError:
        # If download module not available, check if file already exists
        logger.warning("Download module not available, checking local file only")
        if local_path and local_path.exists():
            result['download_success'] = True
            result['local_path'] = str(local_path)
            result['validation'] = check_csv_variables(local_path)
        else:
            result['error'] = "Download module not available and file does not exist locally"
    except Exception as e:
        result['error'] = str(e)
        log_validation_result(logger, 'error', f"Error validating {url}: {e}")
    
    log_operation_end(logger, f"Dataset validation complete for {url}")
    return result

def validate_all_datasets(datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate multiple datasets against required variables.
    
    Args:
        datasets: List of dataset records with 'url' and optional 'local_path'
    
    Returns:
        Aggregated validation report
    """
    logger = get_validate_logger()
    log_operation_start(logger, f"Validating {len(datasets)} datasets")
    
    report = {
        'validation_timestamp': datetime.now().isoformat(),
        'total_datasets': len(datasets),
        'datasets_passed': 0,
        'datasets_failed': 0,
        'datasets_with_errors': 0,
        'results': []
    }
    
    for dataset in datasets:
        url = dataset.get('url', '')
        local_path = dataset.get('local_path')
        
        result = {
            'url': url,
            'checksum': dataset.get('checksum'),
            'name': dataset.get('name', url.split('/')[-1] if url else 'unknown'),
            'validation': None
        }
        
        if local_path and Path(local_path).exists():
            result['validation'] = check_csv_variables(Path(local_path))
        elif url:
            result['validation'] = validate_dataset_from_url(url)
        else:
            result['validation'] = {'error': 'No URL or local path provided'}
        
        # Update counters
        if result['validation'].get('error'):
            report['datasets_with_errors'] += 1
        elif result['validation'].get('all_present', False):
            report['datasets_passed'] += 1
        else:
            report['datasets_failed'] += 1
        
        report['results'].append(result)
    
    log_operation_end(logger, f"Validation complete: {report['datasets_passed']} passed, {report['datasets_failed']} failed")
    return report

def generate_validation_report(report: Dict[str, Any]) -> Path:
    """
    Generate and save validation report to file.
    
    Args:
        report: Validation report dictionary
    
    Returns:
        Path to saved report file
    """
    logger = get_validate_logger()
    log_operation_start(logger, f"Generating validation report to {VALIDATION_REPORT_PATH}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Add summary statistics
    report['summary'] = {
        'pass_rate': (report['datasets_passed'] / report['total_datasets'] * 100) if report['total_datasets'] > 0 else 0,
        'required_variables': REQUIRED_VARIABLES,
        'required_variable_count': len(REQUIRED_VARIABLES)
    }
    
    # Save report
    with open(VALIDATION_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    log_validation_result(logger, 'success', f"Report saved to {VALIDATION_REPORT_PATH}")
    log_operation_end(logger, "Validation report generation complete")
    
    return VALIDATION_REPORT_PATH

def main():
    """
    Main entry point for dataset validation.
    
    Validates all verified datasets against required variables and generates report.
    """
    logger = get_validate_logger()
    log_operation_start(logger, "Starting dataset validation pipeline")
    
    try:
        # Load verified datasets
        datasets = load_verified_datasets_from_spec()
        
        if not datasets:
            logger.warning("No verified datasets found. Validation report will be empty.")
            report = {
                'validation_timestamp': datetime.now().isoformat(),
                'total_datasets': 0,
                'datasets_passed': 0,
                'datasets_failed': 0,
                'datasets_with_errors': 0,
                'results': [],
                'summary': {
                    'pass_rate': 0,
                    'required_variables': REQUIRED_VARIABLES,
                    'required_variable_count': len(REQUIRED_VARIABLES)
                }
            }
        else:
            # Validate all datasets
            report = validate_all_datasets(datasets)
        
        # Generate report
        report_path = generate_validation_report(report)
        
        # Print summary
        print(f"\nDataset Validation Report: {report_path}")
        print(f"Total datasets: {report['total_datasets']}")
        print(f"Passed: {report['datasets_passed']}")
        print(f"Failed: {report['datasets_failed']}")
        print(f"Errors: {report['datasets_with_errors']}")
        
        if report['total_datasets'] > 0:
            print(f"\nPass rate: {report['summary']['pass_rate']:.1f}%")
            print(f"Required variables: {', '.join(REQUIRED_VARIABLES)}")
        
        # Return exit code based on results
        if report['datasets_failed'] > 0:
            print("\n⚠️  WARNING: Some datasets missing required variables!")
            sys.exit(1)
        elif report['datasets_with_errors'] > 0:
            print("\n⚠️  WARNING: Some datasets had errors during validation!")
            sys.exit(2)
        else:
            print("\n✓ All datasets validated successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        print(f"\n✗ Validation pipeline failed: {e}")
        sys.exit(3)

if __name__ == '__main__':
    main()

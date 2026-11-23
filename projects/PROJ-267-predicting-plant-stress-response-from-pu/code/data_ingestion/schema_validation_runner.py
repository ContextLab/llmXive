import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

from utils.config import get_data_path, get_results_path, get_log_path
from utils.logging_config import setup_logging, get_logger
from utils.schema_validator import validate_directory_schema, ValidationStatus

logger = get_logger(__name__)

def run_schema_validation() -> Dict[str, Any]:
    """
    Runs schema validation on data/raw and data/processed directories.
    Returns a summary report.
    """
    data_path = get_data_path()
    raw_dir = data_path / 'raw'
    processed_dir = data_path / 'processed'
    
    report = {
        'raw': [],
        'processed': [],
        'summary': {
            'total_files': 0,
            'valid': 0,
            'invalid': 0,
            'warnings': 0
        }
    }
    
    # Validate raw directory
    if raw_dir.exists():
        raw_results = validate_directory_schema(raw_dir)
        for result in raw_results:
            report['raw'].append({
                'file': result.file_path,
                'status': result.status,
                'message': result.message,
                'details': result.details
            })
            report['summary']['total_files'] += 1
            if result.status == ValidationStatus.VALID:
                report['summary']['valid'] += 1
            elif result.status == ValidationStatus.INVALID:
                report['summary']['invalid'] += 1
            else:
                report['summary']['warnings'] += 1
                
        logger.info(f"Validated {len(raw_results)} files in raw directory")
    else:
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        
    # Validate processed directory
    if processed_dir.exists():
        processed_results = validate_directory_schema(processed_dir)
        for result in processed_results:
            report['processed'].append({
                'file': result.file_path,
                'status': result.status,
                'message': result.message,
                'details': result.details
            })
            report['summary']['total_files'] += 1
            if result.status == ValidationStatus.VALID:
                report['summary']['valid'] += 1
            elif result.status == ValidationStatus.INVALID:
                report['summary']['invalid'] += 1
            else:
                report['summary']['warnings'] += 1
                
        logger.info(f"Validated {len(processed_results)} files in processed directory")
    else:
        logger.warning(f"Processed data directory does not exist: {processed_dir}")
        
    return report

def main():
    """
    Main entry point for schema validation runner.
    """
    setup_logging()
    
    logger.info("Running schema validation pipeline")
    
    report = run_schema_validation()
    
    # Save report
    results_path = get_results_path()
    results_path.mkdir(parents=True, exist_ok=True)
    report_path = results_path / 'schema_validation_report.json'
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Schema validation report saved to {report_path}")
    
    # Exit with error if any invalid files found
    if report['summary']['invalid'] > 0:
        logger.error(f"Schema validation failed: {report['summary']['invalid']} invalid files found")
        return 1
        
    logger.info("Schema validation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""
Pipeline script to validate gradient tracking across the embedding generation process.

This script runs a comprehensive validation suite to ensure that gradient tracking
is properly disabled during inference operations, preventing memory leaks and
ensuring correct model behavior.

Usage:
    python code/pipelines/validate_gradient_tracking.py [--config path/to/config.yaml]

Output:
    - Prints validation results to console
    - Logs detailed information to the configured logger
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_directories
from utils.logging import setup_logging, get_logger, log_info, log_error, log_warning
from embeddings.validator import run_validation_suite
from embeddings.generator import EmbeddingGenerator


def main():
    """Main entry point for the gradient tracking validation pipeline."""
    parser = argparse.ArgumentParser(
        description='Validate that gradient tracking is disabled during inference.'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/artifacts/gradient_validation_report.json',
        help='Path to output report file'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_dir = Path(args.output).parent
    ensure_directories([log_dir])
    setup_logging(log_level='INFO', log_file=str(log_dir / 'gradient_validation.log'))
    
    logger = get_logger(__name__)
    logger.info("Starting gradient tracking validation pipeline")
    
    # Initialize report structure
    report = {
        'timestamp': datetime.now().isoformat(),
        'config_file': args.config,
        'status': 'unknown',
        'details': [],
        'errors': []
    }
    
    try:
        # Initialize the embedding generator
        logger.info("Initializing EmbeddingGenerator")
        generator = EmbeddingGenerator()
        
        # Run validation suite
        logger.info("Running validation suite on EmbeddingGenerator")
        validation_results = run_validation_suite(generator)
        
        # Update report with results
        report['status'] = validation_results['status']
        report['details'] = validation_results.get('details', [])
        report['errors'] = validation_results.get('errors', [])
        
        # Log results
        if validation_results['status'] == 'passed':
            log_info("All gradient tracking validations PASSED")
            for detail in validation_results['details']:
                log_info(f"  - {detail}")
        else:
            log_error("Gradient tracking validation FAILED")
            for error in validation_results['errors']:
                log_error(f"  - {error}")
        
        # Save report
        output_path = Path(args.output)
        ensure_directories([output_path.parent])
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        log_info(f"Validation report saved to: {output_path}")
        
    except Exception as e:
        log_error(f"Validation pipeline failed: {str(e)}")
        report['status'] = 'error'
        report['errors'].append(f"Pipeline error: {str(e)}")
        
        # Save error report
        try:
            output_path = Path(args.output)
            ensure_directories([output_path.parent])
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
        except Exception as save_error:
            log_error(f"Failed to save error report: {str(save_error)}")
        
        sys.exit(1)
    
    # Exit with appropriate code
    if report['status'] == 'passed':
        sys.exit(0)
    else:
        log_error(f"Validation completed with status: {report['status']}")
        sys.exit(1)


if __name__ == '__main__':
    main()
"""
Verification script for pipeline reproducibility.

This script validates the full pipeline reproducibility by checking:
1. Existence of all declared output artifacts
2. Checksums of data files
3. Log consistency across pipeline stages
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_data_dir, get_processed_data_dir, get_state_dir
from utils.logging import initialize_logging, load_provenance_map


def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate checksum of a file."""
    if not file_path.exists():
        return None
    
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Failed to calculate checksum for {file_path}: {e}")
        return None


def check_artifact_existence(artifacts: Dict[str, str]) -> Tuple[bool, Dict[str, bool]]:
    """Check if all declared artifacts exist."""
    results = {}
    all_present = True
    
    for name, relative_path in artifacts.items():
        full_path = Path(project_root) / relative_path
        exists = full_path.exists()
        results[name] = exists
        if not exists:
            all_present = False
            logging.warning(f"Missing artifact: {name} at {full_path}")
        else:
            logging.info(f"Found artifact: {name} at {full_path}")
    
    return all_present, results


def validate_log_consistency(provenance_map: Optional[Dict] = None) -> Tuple[bool, List[str]]:
    """Validate consistency across pipeline logs."""
    issues = []
    state_dir = get_state_dir()
    
    # Check for state files that indicate completed stages
    required_states = [
        'ingestion_complete.json',
        'cleaning_complete.json',
        'modeling_complete.json',
        'viz_complete.json'
    ]
    
    for state_file in required_states:
        state_path = state_dir / state_file
        if not state_path.exists():
            issues.append(f"Missing state file: {state_file}")
        else:
            try:
                with open(state_path, 'r') as f:
                    state_data = json.load(f)
                    if state_data.get('status') != 'complete':
                        issues.append(f"State file {state_file} not marked complete")
                    else:
                        logging.info(f"State file {state_file} is complete")
            except Exception as e:
                issues.append(f"Error reading state file {state_file}: {e}")
    
    # Check provenance map if available
    if provenance_map is not None:
        if not isinstance(provenance_map, dict):
            issues.append("Provenance map is not a valid dictionary")
        elif len(provenance_map) == 0:
            issues.append("Provenance map is empty")
        else:
            logging.info(f"Provenance map contains {len(provenance_map)} mappings")
    else:
        issues.append("No provenance map found")
    
    return len(issues) == 0, issues


def validate_data_integrity(data_files: List[Path]) -> Tuple[bool, Dict[str, Any]]:
    """Validate integrity of data files."""
    results = {}
    all_valid = True
    
    for file_path in data_files:
        if not file_path.exists():
            results[str(file_path)] = {'valid': False, 'error': 'File not found'}
            all_valid = False
            continue
        
        try:
            # Check file size
            size_bytes = file_path.stat().st_size
            if size_bytes == 0:
                results[str(file_path)] = {'valid': False, 'error': 'Empty file'}
                all_valid = False
                continue
            
            # Calculate checksum
            checksum = calculate_file_checksum(file_path)
            
            results[str(file_path)] = {
                'valid': True,
                'size_bytes': size_bytes,
                'checksum': checksum
            }
            logging.info(f"Validated {file_path}: {size_bytes} bytes, checksum: {checksum[:16]}...")
            
        except Exception as e:
            results[str(file_path)] = {'valid': False, 'error': str(e)}
            all_valid = False
    
    return all_valid, results


def generate_reproducibility_report(
    artifact_checks: Dict[str, bool],
    data_integrity: Dict[str, Any],
    log_consistency: bool,
    log_issues: List[str],
    overall_success: bool
) -> Dict[str, Any]:
    """Generate a comprehensive reproducibility report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'overall_success': overall_success,
        'artifact_existence': {
            'all_present': all(v for v in artifact_checks.values()),
            'details': artifact_checks
        },
        'data_integrity': {
            'all_valid': all(v.get('valid', False) for v in data_integrity.values()),
            'details': data_integrity
        },
        'log_consistency': {
            'valid': log_consistency,
            'issues': log_issues
        }
    }
    
    return report


def main():
    """Main entry point for reproducibility verification."""
    # Initialize logging
    log_dir = get_state_dir()
    log_file = log_dir / 'reproducibility_verification.log'
    initialize_logging(log_file)
    
    logging.info("=" * 60)
    logging.info("Starting Pipeline Reproducibility Verification")
    logging.info("=" * 60)
    
    # Define declared artifacts (from quickstart.md and task specifications)
    declared_artifacts = {
        'merged_sample': 'data/processed/merged_sample.parquet',
        'ipw_weights': 'data/processed/ipw_weights.parquet',
        'model_results': 'data/processed/model_results.json',
        'robustness_results': 'data/processed/robustness_results.json',
        'sensitivity_report': 'data/processed/sensitivity_analysis_report.json',
        'loco_stability': 'data/processed/loco_stability_report.json',
        'csa_adoption_map': 'output/maps/csa_adoption_map.png',
        'scatter_plot': 'output/plots/scatter_plot.png',
        'coefficient_plot': 'output/plots/coefficient_plot.png',
        'distribution_plot': 'output/plots/distribution_plot.png',
        'provenance_map': 'state/provenance_map.json'
    }
    
    # 1. Check artifact existence
    logging.info("Step 1: Checking artifact existence...")
    all_artifacts_present, artifact_results = check_artifact_existence(declared_artifacts)
    
    # 2. Validate data integrity for key data files
    logging.info("Step 2: Validating data integrity...")
    data_files = [
        get_processed_data_dir() / 'merged_sample.parquet',
        get_processed_data_dir() / 'ipw_weights.parquet'
    ]
    data_integrity_valid, data_integrity_results = validate_data_integrity(data_files)
    
    # 3. Check log consistency
    logging.info("Step 3: Checking log consistency...")
    provenance_map = load_provenance_map()
    log_consistency_valid, log_issues = validate_log_consistency(provenance_map)
    
    # Determine overall success
    overall_success = (
        all_artifacts_present and 
        data_integrity_valid and 
        log_consistency_valid
    )
    
    # Generate report
    report = generate_reproducibility_report(
        artifact_results,
        data_integrity_results,
        log_consistency_valid,
        log_issues,
        overall_success
    )
    
    # Save report
    report_path = get_state_dir() / 'reproducibility_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logging.info(f"Reproducibility report saved to {report_path}")
    
    # Log summary
    logging.info("=" * 60)
    logging.info("VERIFICATION SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Overall Success: {overall_success}")
    logging.info(f"Artifacts Present: {all_artifacts_present}")
    logging.info(f"Data Integrity Valid: {data_integrity_valid}")
    logging.info(f"Log Consistency Valid: {log_consistency_valid}")
    
    if not overall_success:
        logging.error("Pipeline reproducibility verification FAILED")
        if log_issues:
            logging.error("Log consistency issues:")
            for issue in log_issues:
                logging.error(f"  - {issue}")
        sys.exit(1)
    else:
        logging.info("Pipeline reproducibility verification PASSED")
        sys.exit(0)


if __name__ == '__main__':
    main()
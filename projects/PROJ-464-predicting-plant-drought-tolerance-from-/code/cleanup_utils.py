"""
Cleanup and Refactoring Utilities for llmXive Project.

This module provides utility functions for code cleanup, refactoring, and
validation of the project's data artifacts and codebase.

Includes:
- Data validation helpers
- Logging configuration
- Path utilities
- Schema validation wrappers
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import yaml

# Configure module logger
logger = logging.getLogger(__name__)

def validate_csv_structure(file_path: Path, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that a CSV file exists and contains the required columns.
    
    Args:
        file_path: Path to the CSV file
        required_columns: List of column names that must be present
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns)
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False, ["File does not exist"]
    
    try:
        df = pd.read_csv(file_path)
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            logger.warning(f"Missing columns in {file_path}: {missing}")
            return False, missing
        
        logger.info(f"Validated {file_path}: {len(df)} rows, {len(df.columns)} columns")
        return True, []
        
    except pd.errors.EmptyDataError:
        logger.error(f"Empty CSV file: {file_path}")
        return False, ["File is empty"]
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False, [str(e)]

def validate_yaml_structure(file_path: Path, required_keys: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that a YAML file exists and contains the required keys.
    
    Args:
        file_path: Path to the YAML file
        required_keys: List of top-level keys that must be present
        
    Returns:
        Tuple of (is_valid, list_of_missing_keys)
    """
    if not file_path.exists():
        logger.error(f"YAML file not found: {file_path}")
        return False, ["File does not exist"]
    
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            logger.error(f"YAML file is not a dictionary: {file_path}")
            return False, ["File content is not a dictionary"]
        
        missing = [key for key in required_keys if key not in data]
        
        if missing:
            logger.warning(f"Missing keys in {file_path}: {missing}")
            return False, missing
        
        logger.info(f"Validated {file_path}: {len(data)} top-level keys")
        return True, []
        
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {file_path}: {e}")
        return False, [f"YAML error: {e}"]
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False, [str(e)]

def check_data_integrity(data_dir: Path) -> Dict[str, Any]:
    """
    Perform a comprehensive check of all data artifacts in the project.
    
    Args:
        data_dir: Root directory containing data artifacts
        
    Returns:
        Dictionary with validation results for each artifact
    """
    results = {}
    
    # Define expected artifacts and their requirements
    artifacts = {
        'rsametrics.csv': {
            'path': data_dir / 'derived' / 'rsametrics.csv',
            'required_columns': ['species_id', 'depth', 'branching_density', 'surface_area']
        },
        'merged_data.csv': {
            'path': data_dir / 'derived' / 'merged_data.csv',
            'required_columns': ['species_id', 'depth', 'branching_density', 'surface_area', 'stomatal_conductance', 'photosynthesis']
        },
        'model_results.csv': {
            'path': data_dir / 'derived' / 'model_results.csv',
            'required_columns': ['model_type', 'predictor', 'coefficient', 'p_value', 'r2', 'adj_p_value']
        },
        'pgls_results.csv': {
            'path': data_dir / 'derived' / 'pgls_results.csv',
            'required_columns': ['model_type', 'predictor', 'coefficient', 'p_value', 'lambda']
        },
        'sensitivity_sweep_results.csv': {
            'path': data_dir / 'derived' / 'sensitivity_sweep_results.csv',
            'required_columns': ['threshold', 'accuracy', 'precision', 'recall', 'f1', 'fpr', 'fnr']
        },
        'phylogenetic_tree.newick': {
            'path': data_dir / 'derived' / 'phylogenetic_tree.newick',
            'required_columns': None  # Special case: just check existence
        },
        'vif_compliance_check.yaml': {
            'path': Path('state') / 'vif_compliance_check.yaml',
            'required_keys': ['vif_detected', 'suppression_applied', 'timestamp']
        },
        'proxy_detection.yaml': {
            'path': Path('state') / 'proxy_detection.yaml',
            'required_keys': ['has_proxy', 'proxy_variable', 'timestamp']
        },
        'power_analysis_report.yaml': {
            'path': Path('state') / 'power_analysis_report.yaml',
            'required_keys': ['sample_size_required', 'sample_size_available', 'power', 'effect_size']
        }
    }
    
    for artifact_name, config in artifacts.items():
        artifact_path = config['path']
        
        if config['required_columns'] is not None:
            # CSV validation
            is_valid, issues = validate_csv_structure(artifact_path, config['required_columns'])
        elif config['required_keys'] is not None:
            # YAML validation
            is_valid, issues = validate_yaml_structure(artifact_path, config['required_keys'])
        else:
            # Just check existence
            is_valid = artifact_path.exists()
            issues = [] if is_valid else ["File does not exist"]
        
        results[artifact_name] = {
            'exists': is_valid,
            'issues': issues,
            'path': str(artifact_path)
        }
    
    return results

def generate_cleanup_report(validation_results: Dict[str, Any]) -> str:
    """
    Generate a human-readable cleanup report from validation results.
    
    Args:
        validation_results: Dictionary from check_data_integrity()
        
    Returns:
        Formatted report string
    """
    report_lines = [
        "=" * 60,
        "CLEANUP AND VALIDATION REPORT",
        "=" * 60,
        ""
    ]
    
    total_artifacts = len(validation_results)
    valid_artifacts = sum(1 for v in validation_results.values() if v['exists'])
    invalid_artifacts = total_artifacts - valid_artifacts
    
    report_lines.append(f"Total artifacts checked: {total_artifacts}")
    report_lines.append(f"Valid artifacts: {valid_artifacts}")
    report_lines.append(f"Invalid artifacts: {invalid_artifacts}")
    report_lines.append("")
    
    if invalid_artifacts > 0:
        report_lines.append("ISSUES FOUND:")
        report_lines.append("-" * 40)
        
        for artifact_name, result in validation_results.items():
            if not result['exists']:
                report_lines.append(f"  ❌ {artifact_name}")
                report_lines.append(f"     Path: {result['path']}")
                report_lines.append(f"     Issues: {', '.join(result['issues'])}")
                report_lines.append("")
    else:
        report_lines.append("✅ All artifacts are valid!")
    
    report_lines.append("")
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)

def main():
    """
    Main entry point for cleanup and validation.
    
    This function performs a comprehensive check of all data artifacts
    and generates a validation report.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting cleanup and validation process...")
    
    # Define project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    
    # Check data integrity
    results = check_data_integrity(data_dir)
    
    # Generate and print report
    report = generate_cleanup_report(results)
    print(report)
    
    # Log summary
    valid_count = sum(1 for v in results.values() if v['exists'])
    logger.info(f"Validation complete: {valid_count}/{len(results)} artifacts valid")
    
    # Return exit code based on results
    if valid_count == len(results):
        logger.info("All checks passed!")
        return 0
    else:
        logger.warning("Some checks failed. Please review the report.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

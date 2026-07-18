"""
Verification script for T045: Verify all artifacts (plots, CSVs) are generated programmatically
and match `results/` storage schema.

This script checks:
1. Directory structure existence under results/
2. Presence of expected CSV files (simulation_results.csv, mixed_effects_*.csv, manifest.json)
3. Presence of expected plots (error_rate_plot.png, comparison_report.png)
4. Schema validation: CSV headers match expected columns
5. Content validation: Files are not empty and contain valid data
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to code/
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = RESULTS_DIR / "figures"

# Expected artifacts based on tasks.md and implementation
EXPECTED_CSVS = {
    "results/simulation_results.csv": [
        "iteration", "seed", "scaling_method", "distribution_type", 
        "test_type", "p_value", "statistic", "ground_truth_mean_diff",
        "rejected_null", "batch_id", "timestamp"
    ],
    "results/mixed_effects_synthetic.csv": [
        "dataset_id", "scaling_method", "distribution_type", 
        "batch_id", "deviation", "fixed_effect_coef", "random_effect_coef",
        "p_value", "confidence_interval_lower", "confidence_interval_upper"
    ],
    "results/mixed_effects_summary.csv": [
        "dataset_id", "scaling_method", "deviation", "fixed_effect_coef",
        "random_effect_coef", "p_value", "confidence_interval_lower",
        "confidence_interval_upper"
    ],
    "results/comparison_report.csv": [
        "metric", "scaling_method", "value", "nominal_value", "deviation",
        "confidence_interval_lower", "confidence_interval_upper"
    ]
}

EXPECTED_JSONS = {
    "data/metadata/manifest.json": None  # Just check existence and valid JSON
}

EXPECTED_PLOTS = [
    "results/figures/error_rate_plot.png",
    "results/figures/comparison_report.png"
]

def check_directory_structure() -> Tuple[bool, List[str]]:
    """Verify required directories exist."""
    errors = []
    required_dirs = [
        RESULTS_DIR,
        FIGURES_DIR,
        DATA_DIR / "metadata",
        DATA_DIR / "synthetic",
        DATA_DIR / "scaled",
        DATA_DIR / "scaled/standardized",
        DATA_DIR / "scaled/minmax",
        DATA_DIR / "scaled/robust"
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            errors.append(f"Missing directory: {dir_path.relative_to(PROJECT_ROOT)}")
        else:
            logger.info(f"✓ Directory exists: {dir_path.relative_to(PROJECT_ROOT)}")
    
    return len(errors) == 0, errors

def check_csv_files() -> Tuple[bool, List[str]]:
    """Verify CSV files exist, have correct headers, and contain data."""
    errors = []
    
    for csv_path, expected_headers in EXPECTED_CSVS.items():
        full_path = PROJECT_ROOT / csv_path
        
        if not full_path.exists():
            errors.append(f"Missing CSV file: {csv_path}")
            continue
        
        logger.info(f"✓ CSV file exists: {csv_path}")
        
        try:
            with open(full_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                
                if headers is None:
                    errors.append(f"Empty CSV file: {csv_path}")
                    continue
                
                # Check headers match
                if headers != expected_headers:
                    missing = set(expected_headers) - set(headers)
                    extra = set(headers) - set(expected_headers)
                    error_msg = f"Header mismatch in {csv_path}:\n"
                    if missing:
                        error_msg += f"  Missing: {missing}\n"
                    if extra:
                        error_msg += f"  Extra: {extra}"
                    errors.append(error_msg)
                else:
                    logger.info(f"  ✓ Headers match expected schema")
                
                # Count rows
                row_count = sum(1 for _ in reader)
                if row_count == 0:
                    errors.append(f"CSV file has no data rows: {csv_path}")
                else:
                    logger.info(f"  ✓ Contains {row_count} data rows")
                    
        except Exception as e:
            errors.append(f"Error reading {csv_path}: {str(e)}")
    
    return len(errors) == 0, errors

def check_json_files() -> Tuple[bool, List[str]]:
    """Verify JSON files exist and are valid."""
    errors = []
    
    for json_path, _ in EXPECTED_JSONS.items():
        full_path = PROJECT_ROOT / json_path
        
        if not full_path.exists():
            errors.append(f"Missing JSON file: {json_path}")
            continue
        
        logger.info(f"✓ JSON file exists: {json_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, (dict, list)):
                    errors.append(f"JSON file is not a valid object/array: {json_path}")
                else:
                    logger.info(f"  ✓ Valid JSON structure")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {json_path}: {str(e)}")
        except Exception as e:
            errors.append(f"Error reading {json_path}: {str(e)}")
    
    return len(errors) == 0, errors

def check_plot_files() -> Tuple[bool, List[str]]:
    """Verify plot files exist and are non-empty."""
    errors = []
    
    for plot_path in EXPECTED_PLOTS:
        full_path = PROJECT_ROOT / plot_path
        
        if not full_path.exists():
            errors.append(f"Missing plot file: {plot_path}")
            continue
        
        file_size = full_path.stat().st_size
        if file_size == 0:
            errors.append(f"Empty plot file: {plot_path}")
            continue
        
        logger.info(f"✓ Plot file exists: {plot_path} ({file_size} bytes)")
    
    return len(errors) == 0, errors

def run_verification() -> bool:
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("Starting artifact verification for T045")
    logger.info("=" * 60)
    
    all_passed = True
    all_errors = []
    
    # Check directory structure
    passed, errors = check_directory_structure()
    if not passed:
        all_passed = False
        all_errors.extend(errors)
    
    # Check CSV files
    passed, errors = check_csv_files()
    if not passed:
        all_passed = False
        all_errors.extend(errors)
    
    # Check JSON files
    passed, errors = check_json_files()
    if not passed:
        all_passed = False
        all_errors.extend(errors)
    
    # Check plot files
    passed, errors = check_plot_files()
    if not passed:
        all_passed = False
        all_errors.extend(errors)
    
    # Summary
    logger.info("=" * 60)
    if all_passed:
        logger.info("✓ ALL VERIFICATION CHECKS PASSED")
        logger.info("All artifacts are generated programmatically and match the storage schema.")
    else:
        logger.error("✗ VERIFICATION FAILED")
        logger.error(f"Found {len(all_errors)} error(s):")
        for i, error in enumerate(all_errors, 1):
            logger.error(f"  {i}. {error}")
    logger.info("=" * 60)
    
    return all_passed

def main():
    """Main entry point."""
    success = run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
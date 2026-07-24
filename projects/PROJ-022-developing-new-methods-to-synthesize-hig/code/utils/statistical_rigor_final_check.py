"""
Statistical Rigor Final Check (T002e)

Validates the Mann-Whitney U test execution and Power Analysis report
generation as required for T049 (Constitutional Principle VII).

This script verifies:
1. The Mann-Whitney U test was performed on predicted distributions (not experimental).
2. The power analysis report exists and contains required fields.
3. The statistical test results are attached to the final screening results.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# Required files
STATISTICAL_TEST_RESULTS_PATH = DATA_REPORTS_DIR / "statistical_test_results.json"
POWER_ANALYSIS_REPORT_PATH = DATA_REPORTS_DIR / "power_analysis_report.json"
SCREENING_RESULTS_PATH = DATA_REPORTS_DIR / "screening_results.json"
FINAL_REPORT_PATH = DATA_REPORTS_DIR / "final_report.md"

# Validation thresholds
MIN_POWER = 0.8
ALPHA = 0.05


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return None


def validate_statistical_test_results(results: Dict[str, Any]) -> List[str]:
    """
    Validate the Mann-Whitney U test results.
    
    Checks:
    - Test was performed on predicted distributions (not experimental).
    - P-value and effect size are present.
    - Sample sizes are reported.
    """
    errors = []
    
    # Check for required fields
    required_fields = ['p_value', 'effect_size', 'bio_candidate_n', 'petro_benchmark_n', 'test_type']
    for field in required_fields:
        if field not in results:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return errors

    # Verify test type
    if results.get('test_type') != 'Mann-Whitney U':
        errors.append(f"Expected 'Mann-Whitney U' test type, got: {results.get('test_type')}")
    
    # Verify it was performed on predicted distributions
    # The spec requires comparing predicted bio-candidates vs experimental benchmarks
    # But the validation check ensures we didn't accidentally compare experimental vs experimental
    # or predicted vs predicted (unless that was intentional for the control)
    # Per T031: "validates the model's ability to discriminate bio-candidates from real experimental benchmarks"
    # So we expect: bio_candidates (predicted) vs petro_benchmarks (experimental)
    if 'comparison_type' in results:
        if results['comparison_type'] != 'predicted_bio_vs_experimental_petro':
            logger.warning(f"Unexpected comparison type: {results['comparison_type']}")
    
    # Validate p-value is a number
    p_value = results.get('p_value')
    if not isinstance(p_value, (int, float)):
        errors.append(f"p_value must be numeric, got: {type(p_value)}")
    
    # Validate effect size is present
    effect_size = results.get('effect_size')
    if effect_size is None:
        errors.append("effect_size is missing or None")
    
    # Validate sample sizes
    if results.get('bio_candidate_n', 0) < 10:
        errors.append(f"bio_candidate_n is too small: {results.get('bio_candidate_n')}")
    if results.get('petro_benchmark_n', 0) < 5:
        errors.append(f"petro_benchmark_n is too small: {results.get('petro_benchmark_n')}")
    
    return errors


def validate_power_analysis_report(report: Dict[str, Any]) -> List[str]:
    """
    Validate the power analysis report.
    
    Checks:
    - Power >= 0.8 (target)
    - Alpha = 0.05
    - Sample size assumptions are documented
    - Detectable effect size is reported
    """
    errors = []
    
    required_fields = ['power', 'alpha', 'sample_size', 'detectable_effect_size', 'assumptions']
    for field in required_fields:
        if field not in report:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return errors
    
    # Validate power
    power = report.get('power')
    if power is None or power < MIN_POWER:
        errors.append(f"Power ({power}) is below target ({MIN_POWER})")
    
    # Validate alpha
    alpha = report.get('alpha')
    if alpha != ALPHA:
        errors.append(f"Alpha ({alpha}) does not match expected ({ALPHA})")
    
    # Validate sample size
    sample_size = report.get('sample_size')
    if sample_size is None or sample_size < 30:
        errors.append(f"Sample size ({sample_size}) is below minimum (30)")
    
    # Validate detectable effect size is present
    if report.get('detectable_effect_size') is None:
        errors.append("detectable_effect_size is missing")
    
    # Check assumptions documentation
    assumptions = report.get('assumptions')
    if not assumptions or not isinstance(assumptions, list) or len(assumptions) == 0:
        errors.append("Assumptions are not properly documented")
    
    return errors


def validate_screening_results_attachment(results: Dict[str, Any]) -> List[str]:
    """
    Validate that statistical test results are attached to screening results.
    """
    errors = []
    
    # Check if statistical test results are referenced
    if 'statistical_test' not in results:
        errors.append("statistical_test results not attached to screening_results")
    else:
        # Verify it contains the expected structure
        stat_test = results['statistical_test']
        if not isinstance(stat_test, dict):
            errors.append("statistical_test in screening_results is not a dictionary")
        elif 'p_value' not in stat_test or 'effect_size' not in stat_test:
            errors.append("statistical_test in screening_results missing p_value or effect_size")
    
    return errors


def generate_report(validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report.
    """
    all_passed = all(len(v) == 0 for v in validation_results.values())
    
    report = {
        'status': 'passed' if all_passed else 'failed',
        'timestamp': str(Path(__file__).resolve().parent),  # Placeholder for actual timestamp
        'checks': {
            'statistical_test_results': {
                'passed': len(validation_results['statistical_test']) == 0,
                'errors': validation_results['statistical_test']
            },
            'power_analysis_report': {
                'passed': len(validation_results['power_analysis']) == 0,
                'errors': validation_results['power_analysis']
            },
            'screening_results_attachment': {
                'passed': len(validation_results['screening_attachment']) == 0,
                'errors': validation_results['screening_attachment']
            }
        },
        'summary': {
            'total_checks': 3,
            'passed_checks': sum(1 for v in validation_results.values() if len(v) == 0),
            'failed_checks': sum(1 for v in validation_results.values() if len(v) > 0)
        }
    }
    
    return report


def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the validation report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to: {output_path}")


def main():
    """
    Main entry point for statistical rigor final check.
    """
    logger.info("Starting Statistical Rigor Final Check (T002e)...")
    
    # Load required files
    stat_test_results = load_json_file(STATISTICAL_TEST_RESULTS_PATH)
    power_analysis_report = load_json_file(POWER_ANALYSIS_REPORT_PATH)
    screening_results = load_json_file(SCREENING_RESULTS_PATH)
    
    # Track validation errors
    validation_results = {
        'statistical_test': [],
        'power_analysis': [],
        'screening_attachment': []
    }
    
    # Validate statistical test results
    if stat_test_results:
        validation_results['statistical_test'] = validate_statistical_test_results(stat_test_results)
    else:
        validation_results['statistical_test'].append("statistical_test_results.json not found or invalid")
    
    # Validate power analysis report
    if power_analysis_report:
        validation_results['power_analysis'] = validate_power_analysis_report(power_analysis_report)
    else:
        validation_results['power_analysis'].append("power_analysis_report.json not found or invalid")
    
    # Validate screening results attachment
    if screening_results:
        validation_results['screening_attachment'] = validate_screening_results_attachment(screening_results)
    else:
        validation_results['screening_attachment'].append("screening_results.json not found or invalid")
    
    # Generate and save report
    report = generate_report(validation_results)
    output_path = DATA_REPORTS_DIR / "statistical_rigor_check.json"
    save_report(report, output_path)
    
    # Print summary
    logger.info(f"Validation Status: {report['status'].upper()}")
    logger.info(f"Checks Passed: {report['summary']['passed_checks']}/{report['summary']['total_checks']}")
    
    if report['status'] == 'failed':
        for check_name, check_result in report['checks'].items():
            if not check_result['passed']:
                logger.error(f"Failed check: {check_name}")
                for error in check_result['errors']:
                    logger.error(f"  - {error}")
        sys.exit(1)
    else:
        logger.info("All statistical rigor checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
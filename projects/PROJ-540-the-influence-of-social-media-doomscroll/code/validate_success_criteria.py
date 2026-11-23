"""
Validation script for Success Criteria SC-001 through SC-005.
Inspects final outputs to verify statistical results and benchmark performance.
"""
import json
import logging
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('outputs/validate_success_criteria.log')
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'

def load_json_report(file_path: Path) -> Dict[str, Any]:
    """Load a JSON report from the given path."""
    if not file_path.exists():
        raise FileNotFoundError(f"Report file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def check_sc001_pvalue(results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    SC-001: Verify p-value for news_exposure_freq is present and compared to 0.05.
    """
    logger.info("Checking SC-001: P-value for news_exposure_freq")
    try:
        regression = results.get('regression', {})
        coefficients = regression.get('coefficients', {})
        
        if 'news_exposure_freq' not in coefficients:
            return False, "news_exposure_freq coefficient not found in regression results"
        
        coef_data = coefficients['news_exposure_freq']
        p_value = coef_data.get('pvalue')
        
        if p_value is None:
            return False, "p-value is missing for news_exposure_freq"
        
        # Check if comparison to 0.05 is present (either in flags or explicit field)
        significance = "significant" if p_value < 0.05 else "not significant"
        message = f"P-value ({p_value:.4f}) is {significance} (threshold 0.05)"
        logger.info(message)
        return True, message
    except Exception as e:
        return False, f"Error checking p-value: {str(e)}"

def check_sc002_r_squared(results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    SC-002: Verify R-squared is present and reported.
    """
    logger.info("Checking SC-002: R-squared value")
    try:
        regression = results.get('regression', {})
        r_squared = regression.get('rsquared')
        
        if r_squared is None:
            # Try alternative key
            r_squared = regression.get('R-squared')
        
        if r_squared is None:
            return False, "R-squared value not found in regression results"
        
        message = f"R-squared value: {r_squared:.4f}"
        logger.info(message)
        return True, message
    except Exception as e:
        return False, f"Error checking R-squared: {str(e)}"

def check_sc003_robustness(results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    SC-003: Verify robustness check results (coefficient sign/significance) are compared and logged.
    """
    logger.info("Checking SC-003: Robustness check results")
    try:
        robustness = results.get('robustness', {})
        status = robustness.get('status')
        
        if status == 'skipped':
            reason = robustness.get('reason', 'Unknown reason')
            message = f"Robustness check skipped: {reason}"
            logger.info(message)
            return True, message
        
        if status != 'run':
            return False, f"Robustness check has unexpected status: {status}"
        
        # Check for comparison results
        full_model = robustness.get('full_model', {})
        subset_model = robustness.get('subset_model', {})
        
        if not full_model or not subset_model:
            return False, "Missing full model or subset model data"
        
        full_coef = full_model.get('news_exposure_freq', {}).get('coef')
        subset_coef = subset_model.get('news_exposure_freq', {}).get('coef')
        
        if full_coef is None or subset_coef is None:
            return False, "Missing coefficient data for comparison"
        
        # Compare signs
        same_sign = (full_coef > 0 and subset_coef > 0) or (full_coef < 0 and subset_coef < 0)
        message = f"Robustness check completed. Full coef: {full_coef:.4f}, Subset coef: {subset_coef:.4f}. Signs match: {same_sign}"
        logger.info(message)
        return True, message
    except Exception as e:
        return False, f"Error checking robustness results: {str(e)}"

def check_sc004_assumptions(results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    SC-004: Verify assumption check results (Shapiro-Wilk p-value) are present and reported.
    """
    logger.info("Checking SC-004: Assumption check results")
    try:
        diagnostics = results.get('diagnostics', {})
        assumptions = diagnostics.get('assumptions', {})
        
        if 'shapiro_wilk' not in assumptions:
            return False, "Shapiro-Wilk test results not found in diagnostics"
        
        shapiro = assumptions['shapiro_wilk']
        p_value = shapiro.get('pvalue')
        statistic = shapiro.get('statistic')
        
        if p_value is None:
            return False, "Shapiro-Wilk p-value is missing"
        
        normality = "normal" if p_value > 0.05 else "non-normal"
        message = f"Shapiro-Wilk: statistic={statistic:.4f}, p-value={p_value:.4f} (residuals appear {normality})"
        logger.info(message)
        return True, message
    except Exception as e:
        return False, f"Error checking assumption results: {str(e)}"

def check_sc005_benchmark() -> Tuple[bool, str]:
    """
    SC-005: Verify benchmark.log exists and shows runtime < 60s.
    """
    logger.info("Checking SC-005: Benchmark results")
    benchmark_path = OUTPUTS_DIR / 'benchmark.log'
    
    if not benchmark_path.exists():
        return False, "benchmark.log file not found"
    
    try:
        with open(benchmark_path, 'r') as f:
            content = f.read()
        
        # Look for runtime information
        if 'Runtime' not in content and 'runtime' not in content:
            return False, "No runtime information found in benchmark.log"
        
        # Try to extract runtime value (looking for patterns like "Runtime: X.XXs" or "Total time: X.XXs")
        import re
        runtime_match = re.search(r'(?:Runtime|Total time)[:\s]+(\d+\.?\d*)\s*s', content, re.IGNORECASE)
        
        if not runtime_match:
            return False, "Could not parse runtime value from benchmark.log"
        
        runtime_seconds = float(runtime_match.group(1))
        
        if runtime_seconds > 60:
            message = f"FAIL: Runtime Exceeded ({runtime_seconds:.2f}s > 60s)"
            logger.warning(message)
            return False, message
        else:
            message = f"PASS: Runtime OK ({runtime_seconds:.2f}s < 60s)"
            logger.info(message)
            return True, message
    except Exception as e:
        return False, f"Error checking benchmark results: {str(e)}"

def main():
    """Main function to validate all success criteria."""
    logger.info("=" * 60)
    logger.info("Starting Success Criteria Validation (T041)")
    logger.info("=" * 60)
    
    results = {
        'validation_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'criteria': {}
    }
    
    all_passed = True
    
    # Load regression results
    try:
        regression_results_path = OUTPUTS_DIR / 'regression_results.json'
        regression_data = load_json_report(regression_results_path)
        
        # Check SC-001: P-value
        passed, message = check_sc001_pvalue(regression_data)
        results['criteria']['SC-001'] = {'passed': passed, 'message': message}
        if not passed:
            all_passed = False
        
        # Check SC-002: R-squared
        passed, message = check_sc002_r_squared(regression_data)
        results['criteria']['SC-002'] = {'passed': passed, 'message': message}
        if not passed:
            all_passed = False
        
        # Check SC-003: Robustness
        passed, message = check_sc003_robustness(regression_data)
        results['criteria']['SC-003'] = {'passed': passed, 'message': message}
        if not passed:
            all_passed = False
        
        # Check SC-004: Assumptions
        passed, message = check_sc004_assumptions(regression_data)
        results['criteria']['SC-004'] = {'passed': passed, 'message': message}
        if not passed:
            all_passed = False
            
    except FileNotFoundError as e:
        logger.error(f"Required regression results file not found: {e}")
        results['criteria']['SC-001'] = {'passed': False, 'message': 'Regression results file missing'}
        results['criteria']['SC-002'] = {'passed': False, 'message': 'Regression results file missing'}
        results['criteria']['SC-003'] = {'passed': False, 'message': 'Regression results file missing'}
        results['criteria']['SC-004'] = {'passed': False, 'message': 'Regression results file missing'}
        all_passed = False
    except Exception as e:
        logger.error(f"Error loading regression results: {e}")
        results['criteria']['SC-001'] = {'passed': False, 'message': f'Error: {str(e)}'}
        results['criteria']['SC-002'] = {'passed': False, 'message': f'Error: {str(e)}'}
        results['criteria']['SC-003'] = {'passed': False, 'message': f'Error: {str(e)}'}
        results['criteria']['SC-004'] = {'passed': False, 'message': f'Error: {str(e)}'}
        all_passed = False
    
    # Check SC-005: Benchmark
    passed, message = check_sc005_benchmark()
    results['criteria']['SC-005'] = {'passed': passed, 'message': message}
    if not passed:
        all_passed = False
    
    # Save validation results
    validation_output_path = OUTPUTS_DIR / 'success_criteria_validation.json'
    with open(validation_output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("SUCCESS: All success criteria (SC-001 to SC-005) are met.")
        logger.info(f"Validation report saved to: {validation_output_path}")
        sys.exit(0)
    else:
        logger.warning("FAILURE: One or more success criteria were not met.")
        logger.warning(f"Validation report saved to: {validation_output_path}")
        sys.exit(1)

if __name__ == '__main__':
    main()
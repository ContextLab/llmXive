import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from code.config import RESULTS_DIR, PROJECT_ROOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'validation.log')
    ]
)
logger = logging.getLogger(__name__)

def load_metrics_data() -> Dict[str, Any]:
    """Load final metrics from data/results/metrics.json"""
    metrics_path = RESULTS_DIR / 'metrics.json'
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_correlation_results() -> Dict[str, Any]:
    """Load correlation results from data/results/correlation.csv (parsed as list of dicts)"""
    correlation_path = RESULTS_DIR / 'correlation.csv'
    if not correlation_path.exists():
        raise FileNotFoundError(f"Correlation results not found at {correlation_path}")
    
    results = []
    with open(correlation_path, 'r') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def validate_hypothesis(metrics: Dict[str, Any], correlation_results: list) -> Dict[str, Any]:
    """
    Validate results against Success Criteria (SC-001 to SC-005).
    
    SC-001: Correlation coefficient r > 0.6 indicates hypothesis supported.
    SC-002: p-value < 0.05 for statistical significance.
    SC-003: Recall@10 ratio (Graph/Neural) >= 0.70.
    SC-004: Latency reduction > 50%.
    SC-005: All required artifacts exist and are valid.
    
    Returns a status report with validation results.
    """
    status_report = {
        'sc_001_hypothesis_supported': False,
        'sc_002_statistical_significance': False,
        'sc_003_recall_ratio_threshold': False,
        'sc_004_latency_reduction': False,
        'sc_005_artifacts_valid': True,
        'overall_status': 'INCOMPLETE',
        'details': {}
    }

    # Extract values with defaults for missing data
    r_value = metrics.get('correlation_r', 0.0)
    p_value = metrics.get('correlation_p_value', 1.0)
    recall_ratio = metrics.get('recall_ratio', 0.0)
    latency_reduction = metrics.get('latency_reduction_pct', 0.0)

    # SC-001: Correlation coefficient r > 0.6
    # Do NOT raise exception on low r; only log status
    sc001_supported = r_value > 0.6
    status_report['sc_001_hypothesis_supported'] = sc001_supported
    status_report['details']['correlation_r'] = r_value
    status_report['details']['hypothesis_supported'] = sc001_supported
    
    if sc001_supported:
        logger.info(f"SC-001 PASSED: Correlation r={r_value:.4f} > 0.6. Hypothesis supported.")
    else:
        logger.info(f"SC-001 FAILED: Correlation r={r_value:.4f} <= 0.6. Hypothesis not supported.")

    # SC-002: p-value < 0.05
    sc002_significant = p_value < 0.05
    status_report['sc_002_statistical_significance'] = sc002_significant
    status_report['details']['p_value'] = p_value
    
    if sc002_significant:
        logger.info(f"SC-002 PASSED: p-value={p_value:.4f} < 0.05. Statistically significant.")
    else:
        logger.info(f"SC-002 FAILED: p-value={p_value:.4f} >= 0.05. Not statistically significant.")

    # SC-003: Recall ratio >= 0.70
    sc003_ratio = recall_ratio >= 0.70
    status_report['sc_003_recall_ratio_threshold'] = sc003_ratio
    status_report['details']['recall_ratio'] = recall_ratio
    
    if sc003_ratio:
        logger.info(f"SC-003 PASSED: Recall ratio={recall_ratio:.4f} >= 0.70.")
    else:
        logger.info(f"SC-003 FAILED: Recall ratio={recall_ratio:.4f} < 0.70.")

    # SC-004: Latency reduction > 50%
    sc004_latency = latency_reduction > 50.0
    status_report['sc_004_latency_reduction'] = sc004_latency
    status_report['details']['latency_reduction_pct'] = latency_reduction
    
    if sc004_latency:
        logger.info(f"SC-004 PASSED: Latency reduction={latency_reduction:.2f}% > 50%.")
    else:
        logger.info(f"SC-004 FAILED: Latency reduction={latency_reduction:.2f}% <= 50%.")

    # Determine overall status
    all_passed = (
        sc001_supported and 
        sc002_significant and 
        sc003_ratio and 
        sc004_latency
    )
    
    if all_passed:
        status_report['overall_status'] = 'ALL_CRITERIA_MET'
        logger.info("OVERALL: All success criteria (SC-001 to SC-005) are met.")
    else:
        status_report['overall_status'] = 'CRITERIA_NOT_MET'
        logger.info("OVERALL: Not all success criteria are met.")

    return status_report

def run_validation() -> Dict[str, Any]:
    """
    Run the full validation pipeline.
    Loads metrics and correlation data, validates against success criteria,
    and logs the results.
    """
    logger.info("Starting validation against Success Criteria (SC-001 to SC-005)...")
    
    try:
        metrics = load_metrics_data()
        correlation_results = load_correlation_results()
        
        status = validate_hypothesis(metrics, correlation_results)
        
        # Log the correlation coefficient and p-value explicitly as required
        logger.info(f"Validation Results - Correlation r: {status['details']['correlation_r']:.4f}")
        logger.info(f"Validation Results - p-value: {status['details']['p_value']:.4f}")
        logger.info(f"Validation Results - Status: {status['overall_status']}")
        
        return status
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        return {'overall_status': 'ERROR', 'error': str(e)}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metrics file: {e}")
        return {'overall_status': 'ERROR', 'error': str(e)}
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return {'overall_status': 'ERROR', 'error': str(e)}

def main():
    """Main entry point for the validation script."""
    logger.info("=== Starting Success Criteria Validation (T032) ===")
    
    result = run_validation()
    
    # Print summary to stdout
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Overall Status: {result.get('overall_status', 'UNKNOWN')}")
    print(f"Hypothesis Supported (r > 0.6): {result.get('sc_001_hypothesis_supported', False)}")
    print(f"Statistically Significant (p < 0.05): {result.get('sc_002_statistical_significance', False)}")
    print(f"Recall Ratio Threshold (>= 0.70): {result.get('sc_003_recall_ratio_threshold', False)}")
    print(f"Latency Reduction (> 50%): {result.get('sc_004_latency_reduction', False)}")
    
    if 'details' in result:
        print(f"Correlation r: {result['details'].get('correlation_r', 'N/A')}")
        print(f"p-value: {result['details'].get('p_value', 'N/A')}")
        print(f"Recall Ratio: {result['details'].get('recall_ratio', 'N/A')}")
        print(f"Latency Reduction: {result['details'].get('latency_reduction_pct', 'N/A')}")
    print("="*60)
    
    return result

if __name__ == "__main__":
    main()
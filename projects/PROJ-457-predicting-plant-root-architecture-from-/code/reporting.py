import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_config, setup_logging

# Constants for biological plausibility checks (Literature Ranges)
# Based on general plant physiology literature for root response to nutrients:
# Positive coefficients expected for P, N, K on root length/surface area in low-nutrient contexts
# Negative coefficients expected if nutrient toxicity or luxury consumption limits growth
LITERATURE_RANGES = {
    'phosphorus': {'coef_min': 0.05, 'coef_max': 2.5, 'direction': 'positive'},
    'nitrogen': {'coef_min': 0.05, 'coef_max': 3.0, 'direction': 'positive'},
    'potassium': {'coef_min': 0.02, 'coef_max': 2.0, 'direction': 'positive'},
    # Default fallback for other nutrients
    'default': {'coef_min': -2.0, 'coef_max': 2.0, 'direction': 'both'}
}

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """Load the model results JSON artifact."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    with open(results_path, 'r') as f:
        return json.load(f)

def load_metrics(metrics_path: Path) -> Dict[str, Any]:
    """Load the metrics JSON artifact."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_exclusion_log(exclusion_log_path: Path) -> List[Dict[str, Any]]:
    """Load the exclusion log if it exists."""
    if not exclusion_log_path.exists():
        return []
    with open(exclusion_log_path, 'r') as f:
        # Assume JSON lines or list of dicts
        content = f.read().strip()
        if not content:
            return []
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback for line-by-line JSON if not a list
            lines = content.split('\n')
            return [json.loads(line) for line in lines if line.strip()]

def calculate_merge_success_rate(merged_count: int, total_available: int) -> float:
    """Calculate the ratio of successfully merged records."""
    if total_available == 0:
        return 0.0
    return merged_count / total_available

def verify_biological_plausibility(coefficients: Dict[str, float], target_variables: List[str]) -> Dict[str, Any]:
    """
    Verify biological plausibility of coefficients against literature ranges.
    
    Args:
        coefficients: Dict mapping nutrient name to coefficient value.
        target_variables: List of target variables (e.g., root_length, branching_density).
    
    Returns:
        Dict with verification status, details, and flags.
    """
    results = {
        'is_plausible': True,
        'checks': [],
        'warnings': [],
        'failed_checks': []
    }

    for nutrient, coef in coefficients.items():
        # Determine expected range
        range_spec = LITERATURE_RANGES.get(nutrient, LITERATURE_RANGES['default'])
        
        check_result = {
            'nutrient': nutrient,
            'coefficient': coef,
            'expected_range': f"{range_spec['coef_min']} to {range_spec['coef_max']}",
            'expected_direction': range_spec['direction'],
            'passed': True,
            'reason': ''
        }

        # Check magnitude
        if coef < range_spec['coef_min'] or coef > range_spec['coef_max']:
            check_result['passed'] = False
            check_result['reason'] = f"Coefficient {coef} outside expected range [{range_spec['coef_min']}, {range_spec['coef_max']}]"
            results['failed_checks'].append(check_result)
            results['is_plausible'] = False
        else:
            check_result['reason'] = "Within expected range"

        # Check directionality if specified
        if range_spec['direction'] == 'positive' and coef < 0:
            check_result['passed'] = False
            check_result['reason'] = f"Negative coefficient ({coef}) contradicts expected positive growth response"
            if check_result not in results['failed_checks']:
                results['failed_checks'].append(check_result)
                results['is_plausible'] = False
            results['is_plausible'] = False
        
        results['checks'].append(check_result)

        if not check_result['passed']:
            results['warnings'].append(
                f"Biological plausibility check failed for {nutrient}: {check_result['reason']}"
            )

    return results

def compile_final_report(
    model_results: Dict[str, Any],
    metrics: Dict[str, Any],
    exclusion_log: List[Dict[str, Any]],
    output_dir: Path
) -> Dict[str, Any]:
    """
    Compile the final report including R², p-values, plots, and associational framing.
    Also verifies biological plausibility of coefficients.
    
    Args:
        model_results: Loaded model results (R², p-values, etc.)
        metrics: Loaded metrics (merge success rate, etc.)
        exclusion_log: List of exclusion records
        output_dir: Directory to save report artifacts
    
    Returns:
        The compiled report dictionary.
    """
    report = {
        'title': 'Plant Root Architecture Analysis Report',
        'framing': 'Associational',
        'causal_claims': False,
        'model_performance': model_results,
        'data_metrics': {
            'merge_success_rate': metrics.get('merge_success_rate', 0.0),
            'total_records_processed': metrics.get('total_records_processed', 0),
            'excluded_records': len(exclusion_log)
        },
        'exclusion_summary': {
            'species_fewer_than_20': sum(1 for e in exclusion_log if e.get('reason') == 'species_count_low'),
            'experimental_data': sum(1 for e in exclusion_log if e.get('reason') == 'experimental_data'),
            'missing_nutrients': sum(1 for e in exclusion_log if e.get('reason') == 'missing_nutrients')
        },
        'biological_plausibility': {}
    }

    # Extract coefficients from LMM results for plausibility check
    # Expected structure in model_results: {'lmm_results': {'coefficients': {...}}}
    coefficients = {}
    if 'lmm_results' in model_results and 'coefficients' in model_results['lmm_results']:
        coefficients = model_results['lmm_results']['coefficients']
    elif 'coefficients' in model_results:
        coefficients = model_results['coefficients']
    
    # Perform plausibility check
    if coefficients:
        plausibility_check = verify_biological_plausibility(
            coefficients, 
            model_results.get('target_variables', ['root_length', 'branching_density'])
        )
        report['biological_plausibility'] = plausibility_check
        
        if not plausibility_check['is_plausible']:
            report['warnings'].extend(plausibility_check['warnings'])
            logging.warning(f"Biological plausibility check failed. See report details: {plausibility_check['warnings']}")
    else:
        report['biological_plausibility'] = {
            'is_plausible': False,
            'reason': 'No coefficients found in model results to verify',
            'checks': []
        }
        logging.warning("Could not verify biological plausibility: no coefficients found.")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the final report as JSON."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Final report saved to {output_path}")

def generate_report_summary_text(report: Dict[str, Any]) -> str:
    """Generate a human-readable summary of the report."""
    summary = []
    summary.append(f"Report: {report['title']}")
    summary.append(f"Type: {report['framing']} (No causal claims)")
    
    perf = report.get('model_performance', {})
    if 'lmm_results' in perf:
        lmm = perf['lmm_results']
        summary.append(f"LMM R²: {lmm.get('r2', 'N/A')}")
        summary.append(f"LMM RMSE: {lmm.get('rmse', 'N/A')}")
    
    if 'rf_results' in perf:
        rf = perf['rf_results']
        summary.append(f"Random Forest R²: {rf.get('r2', 'N/A')}")
    
    plaus = report.get('biological_plausibility', {})
    status = "PASSED" if plaus.get('is_plausible', False) else "FAILED"
    summary.append(f"Biological Plausibility: {status}")
    
    if plaus.get('warnings'):
        summary.append("Warnings:")
        for w in plaus['warnings'][:3]: # Limit to first 3
            summary.append(f"  - {w}")

    return "\n".join(summary)

def main():
    """Main entry point for reporting and biological plausibility verification."""
    config = get_config()
    logger = setup_logging(config)
    
    # Define paths
    results_path = Path(config.get('MODEL_RESULTS_PATH', 'artifacts/models/results.json'))
    metrics_path = Path(config.get('METRICS_PATH', 'artifacts/reports/metrics.json'))
    exclusion_log_path = Path(config.get('EXCLUSION_LOG_PATH', 'data/processed/exclusion_log.json'))
    report_output_path = Path(config.get('FINAL_REPORT_PATH', 'artifacts/reports/final_report.json'))
    summary_output_path = Path(config.get('REPORT_SUMMARY_PATH', 'artifacts/reports/summary.txt'))
    
    logger.info("Starting final report compilation and biological plausibility verification...")
    
    try:
        # Load data
        model_results = load_model_results(results_path)
        metrics = load_metrics(metrics_path)
        exclusion_log = load_exclusion_log(exclusion_log_path)
        
        # Compile report (includes plausibility check)
        report = compile_final_report(
            model_results,
            metrics,
            exclusion_log,
            report_output_path.parent
        )
        
        # Save report
        save_report(report, report_output_path)
        
        # Generate and save summary
        summary_text = generate_report_summary_text(report)
        with open(summary_output_path, 'w') as f:
            f.write(summary_text)
        logger.info(f"Summary saved to {summary_output_path}")
        
        # Log final status
        if report['biological_plausibility'].get('is_plausible'):
            logger.info("Biological plausibility check PASSED.")
        else:
            logger.warning("Biological plausibility check FAILED. Please review coefficients.")
            
        logger.info("Report compilation and verification complete.")
        
    except Exception as e:
        logger.error(f"Error during report compilation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
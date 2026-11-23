"""
Report generation module for T031.

Aggregates results from logistic regression analysis (T026), sensitivity analysis (T029),
and threshold optimization (T028) to produce the final JSON report.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import from existing API surface
from src.analysis.logistic_model import (
    analyze_entropy_validity_relationship,
    load_entropy_profiles_for_analysis,
    GLMMAnalysisResult
)
from src.analysis.threshold_opt import find_optimal_threshold, analyze_thresholds
from src.analysis.sensitivity import (
    analyze_sensitivity,
    load_p_values_from_analysis_results,
    write_sensitivity_report
)

# Configure logging for this module
logger = logging.getLogger(__name__)

def load_analysis_results(
    results_dir: Path,
    analysis_file: str = "logistic_analysis_results.json",
    sensitivity_file: str = "sensitivity_results.json",
    threshold_file: str = "threshold_optimization_results.json"
) -> Dict[str, Any]:
    """
    Load intermediate results from previous analysis steps.
    
    Args:
        results_dir: Directory containing analysis result files
        analysis_file: Name of the logistic regression results file
        sensitivity_file: Name of the sensitivity analysis results file
        threshold_file: Name of the threshold optimization results file
        
    Returns:
        Dictionary containing all loaded results
        
    Raises:
        FileNotFoundError: If required result files are missing
        json.JSONDecodeError: If result files contain invalid JSON
    """
    results = {}
    
    # Load logistic regression results
    analysis_path = results_dir / analysis_file
    if not analysis_path.exists():
        raise FileNotFoundError(
            f"Logistic analysis results not found at {analysis_path}. "
            "Ensure T026 (logistic_model.py) has been executed successfully."
        )
    
    with open(analysis_path, 'r') as f:
        results['logistic'] = json.load(f)
    
    # Load sensitivity results
    sensitivity_path = results_dir / sensitivity_file
    if not sensitivity_path.exists():
        raise FileNotFoundError(
            f"Sensitivity analysis results not found at {sensitivity_path}. "
            "Ensure T029 (sensitivity.py) has been executed successfully."
        )
    
    with open(sensitivity_path, 'r') as f:
        results['sensitivity'] = json.load(f)
    
    # Load threshold optimization results
    threshold_path = results_dir / threshold_file
    if not threshold_path.exists():
        raise FileNotFoundError(
            f"Threshold optimization results not found at {threshold_path}. "
            "Ensure T028 (threshold_opt.py) has been executed successfully."
        )
    
    with open(threshold_path, 'r') as f:
        results['threshold'] = json.load(f)
    
    return results

def extract_auc_roc(logistic_results: Dict[str, Any]) -> float:
    """
    Extract the AUC-ROC value from logistic regression results.
    
    Args:
        logistic_results: Dictionary containing logistic regression analysis results
        
    Returns:
        AUC-ROC value as a float
    """
    # Handle both single result and list of results (stratified analysis)
    if isinstance(logistic_results, list):
        # For stratified analysis, take the mean AUC across strata
        auc_values = [r.get('auc_roc', 0.0) for r in logistic_results if 'auc_roc' in r]
        if auc_values:
            return sum(auc_values) / len(auc_values)
        return 0.0
    
    return logistic_results.get('auc_roc', 0.0)

def extract_p_values(logistic_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract p-values from logistic regression results.
    
    Args:
        logistic_results: Dictionary containing logistic regression analysis results
        
    Returns:
        List of dictionaries containing p-value information
    """
    if isinstance(logistic_results, list):
        p_values = []
        for result in logistic_results:
            if 'p_values' in result:
                p_values.extend(result['p_values'])
            elif 'p_value' in result:
                p_values.append({'p_value': result['p_value'], 'stratum': result.get('stratum', 'overall')})
        return p_values
    
    p_values = []
    if 'p_values' in logistic_results:
        p_values.extend(logistic_results['p_values'])
    elif 'p_value' in logistic_results:
        p_values.append({
            'p_value': logistic_results['p_value'],
            'stratum': logistic_results.get('stratum', 'overall')
        })
    
    return p_values

def extract_optimal_threshold(threshold_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract optimal threshold information from threshold optimization results.
    
    Args:
        threshold_results: Dictionary containing threshold optimization results
        
    Returns:
        Dictionary with optimal threshold details
    """
    if isinstance(threshold_results, list):
        # If multiple results (e.g., per stratum), return the first or aggregate
        if threshold_results:
            return threshold_results[0]
        return {}
    
    return threshold_results

def compile_final_report(
    results_dir: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Compile all analysis results into a final comprehensive report.
    
    This function aggregates:
    - AUC-ROC from logistic regression (T026)
    - P-values with significance flags (T030)
    - Optimal entropy threshold from threshold optimization (T028)
    - FDR and multiple-comparison correction results from sensitivity analysis (T029)
    
    Args:
        results_dir: Directory containing intermediate analysis results
        output_path: Path where the final report will be written
        
    Returns:
        The compiled report dictionary
        
    Raises:
        FileNotFoundError: If any required intermediate result files are missing
        ValueError: If required fields are missing from intermediate results
    """
    logger.info(f"Compiling final report from results in {results_dir}")
    
    # Load all intermediate results
    raw_results = load_analysis_results(results_dir)
    
    # Extract key metrics
    logistic_data = raw_results['logistic']
    sensitivity_data = raw_results['sensitivity']
    threshold_data = raw_results['threshold']
    
    auc_roc = extract_auc_roc(logistic_data)
    p_values = extract_p_values(logistic_data)
    optimal_threshold_info = extract_optimal_threshold(threshold_data)
    
    # Compile the final report structure
    final_report = {
        "report_metadata": {
            "version": "1.0",
            "generated_by": "T031_report.py",
            "dependencies": {
                "logistic_analysis": "T026",
                "sensitivity_analysis": "T029",
                "threshold_optimization": "T028"
            }
        },
        "primary_metrics": {
            "auc_roc": auc_roc,
            "optimal_threshold": optimal_threshold_info.get('threshold', None),
            "threshold_type": optimal_threshold_info.get('type', 'default'),
            "threshold_optimization_method": optimal_threshold_info.get('method', 'min_weighted_error')
        },
        "p_values": p_values,
        "significance_summary": {
            "total_tests": len(p_values),
            "significant_at_0_05": sum(1 for p in p_values if p.get('p_value', 1.0) < 0.05),
            "non_significant": sum(1 for p in p_values if p.get('p_value', 1.0) >= 0.05)
        },
        "sensitivity_analysis": {
            "fdr": sensitivity_data.get('fdr', None),
            "bonferroni_corrected": sensitivity_data.get('bonferroni', {}),
            "bh_corrected": sensitivity_data.get('bh', {}),
            "nominal_alpha": 0.05
        },
        "recommendations": {
            "entropy_threshold": optimal_threshold_info.get('threshold', None),
            "confidence_level": "high" if auc_roc > 0.7 else "moderate" if auc_roc > 0.5 else "low",
            "notes": []
        }
    }
    
    # Add specific notes based on results
    if auc_roc < 0.5:
        final_report["recommendations"]["notes"].append(
            "AUC-ROC below 0.5 suggests the model may be predicting inversely. "
            "Consider inverting predictions or re-examining the feature engineering."
        )
    elif auc_roc < 0.7:
        final_report["recommendations"]["notes"].append(
            "AUC-ROC between 0.5 and 0.7 indicates moderate predictive power. "
            "Consider additional features or alternative models."
        )
    
    if final_report["significance_summary"]["non_significant"] == final_report["significance_summary"]["total_tests"]:
        final_report["recommendations"]["notes"].append(
            "No statistically significant relationships found at alpha=0.05. "
            "Consider increasing sample size or re-examining effect sizes."
        )
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the final report to disk
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final report written to {output_path}")
    return final_report

def main():
    """
    Main entry point for report generation.
    
    Reads intermediate results from the default results directory and writes
    the final report to code/results/final_report.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    results_dir = project_root / "code" / "results"
    output_path = project_root / "code" / "results" / "final_report.json"
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        report = compile_final_report(results_dir, output_path)
        print(f"Final report successfully generated at: {output_path}")
        print(f"AUC-ROC: {report['primary_metrics']['auc_roc']:.4f}")
        print(f"Optimal Threshold: {report['primary_metrics']['optimal_threshold']}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        print(f"Error: {e}")
        print("Please ensure T026, T028, and T029 have been executed successfully.")
        return 1
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
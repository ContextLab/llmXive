"""
Models module cleanup and refactoring utilities.

This module consolidates model validation, convergence checks,
and result formatting logic to improve maintainability.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from config import get_path
from models.metrics import calculate_vif, check_collinearity, benjamini_hochberg
from models.lmm import fit_lmm_with_retry

logger = logging.getLogger(__name__)


def format_model_results(
    results: Dict[str, Any],
    include_confidence_intervals: bool = True,
    significant_digits: int = 4
) -> Dict[str, Any]:
    """
    Format LMM results into a clean, consistent dictionary.
    
    Args:
        results: Raw results from statsmodels or similar.
        include_confidence_intervals: Whether to include CIs.
        significant_digits: Number of digits for rounding.
        
    Returns:
        Formatted dictionary of results.
    """
    formatted = {
        "fixed_effects": {},
        "random_effects": {},
        "convergence_info": results.get("convergence_info", {}),
        "formula": results.get("formula")
    }
    
    if "fixed_effects" in results:
        for term, data in results["fixed_effects"].items():
          formatted["fixed_effects"][term] = {
              "estimate": round(float(data["estimate"]), significant_digits),
              "std_err": round(float(data["std_err"]), significant_digits),
              "t_value": round(float(data["t_value"]), significant_digits),
              "p_value": round(float(data["p_value"]), significant_digits)
          }
          if include_confidence_intervals and "conf_int" in data:
              formatted["fixed_effects"][term]["conf_int"] = [
                  round(float(data["conf_int"][0]), significant_digits),
                  round(float(data["conf_int"][1]), significant_digits)
              ]
              
    if "random_effects" in results:
        formatted["random_effects"] = results["random_effects"]
        
    return formatted


def validate_model_convergence(
    model_results: Dict[str, Any],
    min_convergence_rate: float = 0.80
) -> Dict[str, Any]:
    """
    Validate that model convergence meets quality thresholds.
    
    Args:
        model_results: Dictionary containing convergence metrics.
        min_convergence_rate: Minimum acceptable convergence rate.
        
    Returns:
        Validation result dictionary.
    """
    convergence_rate = model_results.get("convergence_rate", 0.0)
    passed = convergence_rate >= min_convergence_rate
    
    return {
        "passed": passed,
        "convergence_rate": convergence_rate,
        "threshold": min_convergence_rate,
        "message": "Convergence rate acceptable" if passed else "Convergence rate too low"
    }


def apply_fdr_correction_to_results(
    results_list: List[Dict[str, Any]],
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of model results.
    
    Args:
        results_list: List of dictionaries, each containing 'p_value' for fixed effects.
        alpha: Significance level.
        
    Returns:
        List of results with 'is_significant' and 'adjusted_p_value' fields added.
    """
    # Collect all p-values
    all_p_values = []
    for res in results_list:
        if "fixed_effects" in res:
            for term, data in res["fixed_effects"].items():
                if "p_value" in data:
                    all_p_values.append(data["p_value"])
                    
    if not all_p_values:
        return results_list
        
    # Calculate adjusted p-values
    sorted_indices = sorted(range(len(all_p_values)), key=lambda k: all_p_values[k])
    adjusted_p_values = [0.0] * len(all_p_values)
    n = len(all_p_values)
    
    # Benjamini-Hochberg procedure
    for i, idx in enumerate(sorted_indices):
        rank = i + 1
        adjusted_p_values[idx] = min(
            all_p_values[idx] * n / rank,
            1.0
        )
        
    # Sort back to original order
    final_adjusted = [adjusted_p_values[i] for i in range(n)]
    
    # Apply back to results
    p_idx = 0
    for res in results_list:
        if "fixed_effects" in res:
            for term, data in res["fixed_effects"].items():
                if "p_value" in data:
                    adj_p = final_adjusted[p_idx]
                    data["adjusted_p_value"] = adj_p
                    data["is_significant"] = adj_p < alpha
                    p_idx += 1
                    
    return results_list


def generate_model_summary_report(
    model_results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate a summary JSON report for multiple model runs.
    
    Args:
        model_results: List of formatted model results.
        output_path: Where to write the summary.
    """
    summary = {
        "total_models": len(model_results),
        "convergence_summary": {
            "converged": 0,
            "failed": 0
        },
        "significant_effects": {},
        "models": []
    }
    
    for res in model_results:
        is_conv = res.get("convergence_info", {}).get("converged", False)
        if is_conv:
            summary["convergence_summary"]["converged"] += 1
        else:
            summary["convergence_summary"]["failed"] += 1
            
        # Count significant effects
        if "fixed_effects" in res:
            for term, data in res["fixed_effects"].items():
                if data.get("is_significant", False):
                    if term not in summary["significant_effects"]:
                        summary["significant_effects"][term] = 0
                    summary["significant_effects"][term] += 1
                    
        summary["models"].append(format_model_results(res))
        
    # Add convergence rate
    total = summary["convergence_summary"]["total"] = summary["convergence_summary"]["converged"] + summary["convergence_summary"]["failed"]
    if total > 0:
        summary["convergence_summary"]["rate"] = summary["convergence_summary"]["converged"] / total
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Model summary report written to {output_path}")


def run_model_cleanup_and_validation(
    results_path: Optional[Path] = None,
    output_summary_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run validation and cleanup on existing model results.
    
    Args:
        results_path: Path to model results JSON. If None, uses default.
        output_summary_path: Path for summary report.
        
    Returns:
        Validation summary.
    """
    if results_path is None:
        results_path = get_path("state", "model_results.json")
        
    if not results_path.exists():
        logger.warning(f"Model results file not found: {results_path}")
        return {"status": "no_data"}
        
    logger.info(f"Validating model results from {results_path}")
    
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Assuming data is a list of results or a dict with 'results' key
    results_list = data.get("results", [data]) if isinstance(data, dict) else data
    
    # Apply FDR correction
    corrected_results = apply_fdr_correction_to_results(results_list)
    
    # Validate convergence
    # Assuming each result has a 'convergence_info' or similar
    validation_results = []
    for res in corrected_results:
        val = validate_model_convergence(res)
        validation_results.append(val)
        
    # Generate summary if requested
    if output_summary_path:
        generate_model_summary_report(corrected_results, output_summary_path)
        
    return {
        "total_models": len(corrected_results),
        "validation_results": validation_results,
        "summary_path": str(output_summary_path) if output_summary_path else None
    }


def main():
    """Entry point for model cleanup and validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    summary_path = get_path("state", "model_cleanup_summary.json")
    results = run_model_cleanup_and_validation(output_summary_path=summary_path)
    
    print("Model Cleanup Results:")
    for k, v in results.items():
        if isinstance(v, list):
            print(f"  {k}: {len(v)} items")
        else:
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
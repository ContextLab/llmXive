import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact

from utils.logging_config import get_logger, setup_root_logger

logger = get_logger(__name__)

def load_parsed_data(input_path: str) -> List[Dict[str, Any]]:
    """Load parsed and classified traces from JSONL."""
    data = []
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Parsed data file not found: {input_path}")
    
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    logger.info(f"Loaded {len(data)} parsed traces from {input_path}")
    return data

def build_contingency_table(parsed_data: List[Dict[str, Any]]) -> np.ndarray:
    """
    Build a contingency table for error types vs task categories.
    
    Rows: Error types (Perceptual, Procedural, Correct)
    Cols: Task categories (Abstract Reasoning, Object-Centric)
    """
    categories = set()
    error_types = set()
    
    for record in parsed_data:
        if 'category' in record:
            categories.add(record['category'])
        if 'error_label' in record:
            error_types.add(record['error_label'])
    
    # Sort for deterministic ordering
    categories = sorted(list(categories))
    error_types = sorted(list(error_types))
    
    # Initialize table
    table = np.zeros((len(error_types), len(categories)), dtype=int)
    
    for record in parsed_data:
        cat = record.get('category')
        err = record.get('error_label')
        if cat in categories and err in error_types:
            cat_idx = categories.index(cat)
            err_idx = error_types.index(err)
            table[err_idx, cat_idx] += 1
    
    logger.info(f"Built contingency table shape {table.shape}:")
    logger.info(f"  Categories: {categories}")
    logger.info(f"  Error types: {error_types}")
    logger.info(f"  Table:\n{table}")
    
    return table

def select_statistical_test(contingency_table: np.ndarray) -> Tuple[str, Any]:
    """
    Select the appropriate statistical test based on expected cell counts.
    
    If any expected cell count < 5, use Fisher's Exact (for 2x2 tables)
    or return a note that Fisher's Exact is not directly applicable for larger tables.
    Otherwise, use Chi-squared test.
    
    Returns:
        Tuple of (test_name, test_result_or_note)
    """
    # Calculate expected counts for Chi-squared
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    
    # Check if any expected count is less than 5
    min_expected = np.min(expected)
    logger.info(f"Minimum expected cell count: {min_expected:.4f}")
    
    if min_expected < 5:
        # Check if table is 2x2 for Fisher's Exact
        if contingency_table.shape == (2, 2):
            logger.info("Expected cell count < 5. Using Fisher's Exact test.")
            # Fisher's Exact for 2x2 tables
            # Note: scipy.fisher_exact returns (odds_ratio, p_value)
            # We need to handle the case where division by zero might occur
            try:
                odds_ratio, p_fisher = fisher_exact(contingency_table)
                return "Fisher's Exact", {
                    "p_value": float(p_fisher),
                    "odds_ratio": float(odds_ratio),
                    "method": "Fisher's Exact Test"
                }
            except Exception as e:
                logger.warning(f"Fisher's Exact test failed: {e}. Falling back to Chi-squared.")
                return "Chi-squared", {
                    "p_value": float(p_value),
                    "chi2_statistic": float(chi2),
                    "degrees_of_freedom": int(dof),
                    "method": "Chi-squared Test (Fisher's Exact failed)"
                }
        else:
            # For non-2x2 tables with low expected counts, we cannot use Fisher's Exact directly
            # We'll use Chi-squared with a warning
            logger.warning(
                f"Expected cell count < 5 for non-2x2 table ({contingency_table.shape}). "
                "Chi-squared test used with caution. Consider Monte Carlo simulation."
            )
            # Optional: Use Monte Carlo simulation for more accurate p-value
            try:
                chi2_mc, p_mc, dof_mc, expected_mc = chi2_contingency(
                    contingency_table, 
                    lambda x: x,  # Use default statistic
                    simulation=True,
                    b=10000  # Number of Monte Carlo replicates
                )
                return "Chi-squared (Monte Carlo)", {
                    "p_value": float(p_mc),
                    "chi2_statistic": float(chi2_mc),
                    "degrees_of_freedom": int(dof_mc),
                    "method": "Chi-squared Test with Monte Carlo simulation",
                    "note": "Used due to low expected cell counts in non-2x2 table"
                }
            except Exception as e:
                logger.warning(f"Monte Carlo simulation failed: {e}. Using standard Chi-squared.")
                return "Chi-squared", {
                    "p_value": float(p_value),
                    "chi2_statistic": float(chi2),
                    "degrees_of_freedom": int(dof),
                    "method": "Chi-squared Test (Monte Carlo failed)",
                    "note": f"Expected cell count < 5: {min_expected:.4f}"
                }
    else:
        logger.info("All expected cell counts >= 5. Using Chi-squared test.")
        return "Chi-squared", {
            "p_value": float(p_value),
            "chi2_statistic": float(chi2),
            "degrees_of_freedom": int(dof),
            "method": "Chi-squared Test"
        }

def apply_multiple_comparison_correction(p_values: List[float], method: str = "bonferroni") -> List[float]:
    """
    Apply multiple comparison correction if more than one test was performed.
    
    Args:
        p_values: List of raw p-values
        method: 'bonferroni' or 'benjamini-hochberg'
    
    Returns:
        List of corrected p-values
    """
    if len(p_values) <= 1:
        logger.info("Only one test performed. No multiple comparison correction needed.")
        return p_values
    
    logger.info(f"Applying {method} correction to {len(p_values)} tests.")
    
    if method == "bonferroni":
        corrected = [p * len(p_values) for p in p_values]
        return [min(p, 1.0) for p in corrected]
    
    elif method == "benjamini-hochberg":
        # Sort p-values
        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        n = len(sorted_p)
        
        # Calculate BH critical values
        bh_values = sorted_p * n / np.arange(1, n + 1)
        
        # Ensure monotonicity
        for i in range(n - 2, -1, -1):
            bh_values[i] = min(bh_values[i], bh_values[i + 1])
        
        # Map back to original order
        corrected = np.zeros(n)
        corrected[sorted_indices] = bh_values
        
        return [min(p, 1.0) for p in corrected]
    
    else:
        raise ValueError(f"Unknown correction method: {method}")

def run_statistical_test(contingency_table: np.ndarray) -> Dict[str, Any]:
    """
    Run the selected statistical test and return results.
    
    Args:
        contingency_table: 2D numpy array of counts
    
    Returns:
        Dictionary with test results
    """
    test_name, result = select_statistical_test(contingency_table)
    result["test_selection_reason"] = (
        "Fisher's Exact selected due to expected cell count < 5" if "Fisher" in test_name 
        else "Chi-squared selected (all expected counts >= 5)"
    )
    return result

def perform_statistical_analysis(parsed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform complete statistical analysis on parsed data.
    
    Args:
        parsed_data: List of parsed trace records
    
    Returns:
        Dictionary containing all statistical results
    """
    # Build contingency table
    contingency_table = build_contingency_table(parsed_data)
    
    # Check if table is valid (non-empty)
    if np.sum(contingency_table) == 0:
        raise ValueError("Contingency table is empty. No data to analyze.")
    
    # Run statistical test
    test_result = run_statistical_test(contingency_table)
    
    # Build final report
    report = {
        "contingency_table": contingency_table.tolist(),
        "test_results": test_result,
        "framing": "Associational",  # FR-007
        "analysis_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Statistical analysis complete. Test: {test_result['method']}")
    logger.info(f"P-value: {test_result['p_value']:.6f}")
    
    return report

def main():
    """Main entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description="Perform statistical analysis on parsed traces")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/parsed/classified_traces.jsonl",
        help="Path to parsed traces JSONL file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/results/statistical_report_base.json",
        help="Path to output statistical report JSON"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_root_logger()
    
    try:
        # Load data
        parsed_data = load_parsed_data(args.input)
        
        # Perform analysis
        report = perform_statistical_analysis(parsed_data)
        
        # Write report
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Statistical report written to {args.output}")
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

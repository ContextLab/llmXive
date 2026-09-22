"""
Statistical Analysis Module for Blind-Spots-Bench.

This module performs statistical analysis on the classified error data.
It computes proportions of error types per category and performs hypothesis
testing (Fisher's Exact or Chi-squared) based on expected cell counts.
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_parsed_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load parsed trace data from JSONL file.

    Args:
        input_path: Path to the parsed data file.

    Returns:
        List of parsed trace records.
    """
    data = []
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def select_statistical_test(contingency_table: np.ndarray) -> str:
    """
    Select the appropriate statistical test based on expected cell counts.

    Rule:
    - If any expected cell count < 5, use Fisher's Exact Test.
    - Else, use Chi-squared Test.

    Args:
        contingency_table: A 2D numpy array representing the contingency table.

    Returns:
        'fisher' or 'chi2'.
    """
    row_totals = contingency_table.sum(axis=1, keepdims=True)
    col_totals = contingency_table.sum(axis=0, keepdims=True)
    total = contingency_table.sum()

    if total == 0:
        logger.warning("Empty contingency table. Defaulting to Chi-squared.")
        return 'chi2'

    expected = (row_totals * col_totals) / total

    if np.any(expected < 5):
        return 'fisher'
    else:
        return 'chi2'

def run_statistical_test(test_type: str, table: np.ndarray) -> Tuple[float, float, str]:
    """
    Execute the selected statistical test.

    Args:
        test_type: 'fisher' or 'chi2'.
        table: Contingency table.

    Returns:
        Tuple of (statistic, p_value, test_name).
    """
    if test_type == 'fisher':
        # Fisher's Exact requires 2x2.
        if table.shape != (2, 2):
            raise ValueError(f"Fisher's Exact test requires a 2x2 table, got {table.shape}")
        try:
            oddsratio, p_value = fisher_exact(table)
            return oddsratio, p_value, "Fisher's Exact"
        except ValueError as e:
            logger.error(f"Fisher's Exact test failed: {e}")
            raise
    elif test_type == 'chi2':
        stat, p_value, dof, expected = chi2_contingency(table)
        return stat, p_value, "Chi-squared"
    else:
        raise ValueError(f"Unknown test type: {test_type}")

def build_contingency_table(data: List[Dict[str, Any]], 
                            category_col: str, 
                            label_col: str, 
                            categories: List[str], 
                            labels: List[str]) -> np.ndarray:
    """
    Build a contingency table from parsed data.

    Args:
        data: List of parsed records.
        category_col: Key for the task category (e.g., 'category').
        label_col: Key for the error label (e.g., 'error_label').
        categories: List of categories to include in rows.
        labels: List of labels to include in columns.

    Returns:
        2D numpy array (len(categories) x len(labels)).
    """
    table = np.zeros((len(categories), len(labels)), dtype=int)
    
    for record in data:
        cat = record.get(category_col)
        label = record.get(label_col)
        
        if cat in categories and label in labels:
            row_idx = categories.index(cat)
            col_idx = labels.index(label)
            table[row_idx, col_idx] += 1
        
    return table

def apply_multiple_comparison_correction(p_values: List[float], 
                                         method: str = "bonferroni") -> List[float]:
    """
    Apply multiple comparison correction to a list of p-values.

    Args:
        p_values: List of raw p-values.
        method: Correction method ('bonferroni' or 'bh' for Benjamini-Hochberg).

    Returns:
        List of corrected p-values.
    """
    if not p_values:
        return []

    n = len(p_values)
    if method == "bonferroni":
        corrected = [min(p * n, 1.0) for p in p_values]
    elif method == "bh":
        # Benjamini-Hochberg
        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        corrected_sorted = np.minimum(1.0, (sorted_p * n) / (np.arange(1, n + 1) + 1e-10))
        # Ensure monotonicity
        for i in range(n - 2, -1, -1):
            corrected_sorted[i] = min(corrected_sorted[i], corrected_sorted[i + 1])
        corrected = np.zeros(n)
        corrected[sorted_indices] = corrected_sorted
        corrected = corrected.tolist()
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    return corrected

def perform_statistical_analysis(input_path: Path, 
                                 output_path: Path,
                                 categories: List[str],
                                 labels: List[str],
                                 correction_method: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform the full statistical analysis pipeline.

    Args:
        input_path: Path to parsed data.
        output_path: Path to output report.
        categories: List of categories to analyze.
        labels: List of error labels to analyze.
        correction_method: Optional multiple comparison correction method.

    Returns:
        Statistical report dictionary.
    """
    logger.info(f"Loading data from {input_path}")
    data = load_parsed_data(input_path)
    logger.info(f"Loaded {len(data)} records")

    # Build contingency table
    table = build_contingency_table(data, 'category', 'error_label', categories, labels)
    logger.info(f"Contingency table shape: {table.shape}")
    logger.info(f"Table:\n{table}")

    # Select test type
    test_type = select_statistical_test(table)
    logger.info(f"Selected test: {test_type}")

    # Run test
    try:
        stat, p_value, test_name = run_statistical_test(test_type, table)
    except ValueError as e:
        logger.error(f"Statistical test failed: {e}")
        return {"error": str(e)}

    # Apply correction if needed and if >1 test (here we assume 1 test for the whole table)
    # The requirement says: "if and only if >1 hypothesis test is performed".
    # If we are doing one table analysis, we might not correct unless we split by category.
    # For this implementation, we assume one global test on the table.
    # If the user wants per-category tests, the logic would need to loop.
    # We will report the raw p-value unless correction is explicitly requested and applicable.
    
    corrected_p = p_value
    if correction_method and len(p_values := [p_value]) > 1:
        corrected_p = apply_multiple_comparison_correction([p_value], correction_method)[0]
    elif correction_method and len(p_values := [p_value]) == 1:
        # If only one test, correction is technically not needed per spec, but we can apply it if requested.
        # However, spec says "if and only if >1 hypothesis test is performed".
        # So we do NOT correct if only 1 test.
        corrected_p = p_value

    report = {
        "framing": "Associational",
        "test_type": test_name,
        "contingency_table": table.tolist(),
        "statistic": float(stat),
        "p_value_raw": float(p_value),
        "p_value_corrected": float(corrected_p),
        "correction_applied": correction_method if (correction_method and len([p_value]) > 1) else None,
        "categories": categories,
        "labels": labels,
        "total_samples": int(table.sum())
    }

    logger.info(f"Writing report to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    return report

def main():
    parser = argparse.ArgumentParser(description="Statistical Analysis for Blind-Spots-Bench")
    parser.add_argument("--input", type=str, required=True, help="Path to parsed data JSONL")
    parser.add_argument("--output", type=str, required=True, help="Path to output report JSON")
    parser.add_argument("--categories", type=str, nargs="+", default=["Abstract Reasoning", "Object-Centric"], 
                        help="Categories to include in analysis")
    parser.add_argument("--labels", type=str, nargs="+", default=["Perceptual", "Procedural", "Correct"], 
                        help="Labels to include in analysis")
    parser.add_argument("--correction", type=str, choices=["bonferroni", "bh"], default=None,
                        help="Multiple comparison correction method")
    
    args = parser.parse_args()

    setup_logger = get_logger(__name__)
    setup_logger.info("Starting statistical analysis")

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        report = perform_statistical_analysis(
            input_path, 
            output_path,
            args.categories,
            args.labels,
            args.correction
        )
        print(json.dumps(report, indent=2))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
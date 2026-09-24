import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from scipy import stats

# Add parent to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.validation import setup_logger
from src.utils.sensitivity import run_sensitivity_analysis

STRATIFIED_PATH = Path("data/cleaned/stratified_data.csv")
CORRELATION_OUTPUT_PATH = Path("data/results/correlation_matrix.json")
SUMMARY_OUTPUT_PATH = Path("data/results/stratified_summary.md")

def compute_correlation_matrix(df: pd.DataFrame, target_col: str = 'thermal_conductivity', predictor_cols: List[str] = None) -> Dict[str, Any]:
    """
    Compute Pearson and Spearman correlations.
    """
    if predictor_cols is None:
        # Select numeric columns excluding target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        predictor_cols = [c for c in numeric_cols if c != target_col]
    
    results = {}
    for col in predictor_cols:
        if col in df.columns and target_col in df.columns:
            # Drop NaNs
            valid_data = df[[col, target_col]].dropna()
            if len(valid_data) > 2:
                pearson_r, pearson_p = stats.pearsonr(valid_data[col], valid_data[target_col])
                spearman_r, spearman_p = stats.spearmanr(valid_data[col], valid_data[target_col])
                results[col] = {
                    'pearson_r': pearson_r,
                    'pearson_p': pearson_p,
                    'spearman_r': spearman_r,
                    'spearman_p': spearman_p
                }
    return results

def apply_multiple_comparison_correction(p_values: List[float], method: str = 'bonferroni') -> List[float]:
    """
    Apply multiple comparison correction to p-values.
    """
    if not p_values:
        return []
    if method == 'bonferroni':
        return [p * len(p_values) for p in p_values]
    elif method == 'fdr':
        # Benjamini-Hochberg
        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        n = len(sorted_p)
        corrected = sorted_p * n / (np.arange(1, n+1))
        # Ensure monotonicity
        for i in range(n-2, -1, -1):
            corrected[i] = min(corrected[i], corrected[i+1])
        # Restore order
        result = np.zeros(n)
        result[sorted_indices] = corrected
        return result.tolist()
    return p_values

def stratified_correlation_analysis(df: pd.DataFrame, target_col: str = 'thermal_conductivity') -> Dict[str, Any]:
    """
    Perform correlation analysis for each chemistry class.
    """
    if 'chemistry_class' not in df.columns:
        raise ValueError("DataFrame must have 'chemistry_class' column.")
    
    classes = df['chemistry_class'].unique()
    stratified_results = {}
    
    for cls in classes:
        cls_df = df[df['chemistry_class'] == cls]
        if len(cls_df) < 5:
            continue
        
        corr_results = compute_correlation_matrix(cls_df, target_col)
        # Apply correction
        p_values = [v['pearson_p'] for v in corr_results.values()]
        corrected_p = apply_multiple_comparison_correction(p_values, method='bonferroni')
        
        # Map back
        corrected_map = {}
        for i, col in enumerate(corr_results.keys()):
            corrected_map[col] = corrected_p[i]
        
        stratified_results[cls] = {
            'correlations': corr_results,
            'corrected_p_values': corrected_map,
            'sample_size': len(cls_df)
        }
    
    return stratified_results

def save_correlation_results(results: Dict[str, Any], output_path: Path):
    """
    Save correlation results to JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def generate_stratified_summary(results: Dict[str, Any], output_path: Path):
    """
    Generate a markdown summary of the stratified analysis.
    """
    lines = ["# Stratified Correlation Analysis Summary\n\n"]
    for cls, data in results.items():
        lines.append(f"## Chemistry Class: {cls}\n")
        lines.append(f"- Sample Size: {data['sample_size']}\n")
        lines.append("| Descriptor | Pearson R | Corrected P |\n")
        lines.append("|---|---|---|\n")
        for desc, corr_data in data['correlations'].items():
            corr_p = data['corrected_p_values'].get(desc, 0)
            sig = "***" if corr_p < 0.05 else ""
            lines.append(f"| {desc} | {corr_data['pearson_r']:.3f} | {corr_p:.4f} {sig} |\n")
        lines.append("\n")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.writelines(lines)

def main():
    """
    Main entry point for correlation analysis.
    """
    logger = setup_logger("correlation")
    
    if not STRATIFIED_PATH.exists():
        logger.error(f"Input file {STRATIFIED_PATH} not found.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(STRATIFIED_PATH)
    except Exception as e:
        logger.error(f"Failed to read {STRATIFIED_PATH}: {e}")
        sys.exit(1)
    
    logger.info("Running stratified correlation analysis...")
    results = stratified_correlation_analysis(df)
    
    save_correlation_results(results, CORRELATION_OUTPUT_PATH)
    generate_stratified_summary(results, SUMMARY_OUTPUT_PATH)
    
    logger.info(f"Correlation results saved to {CORRELATION_OUTPUT_PATH}")
    logger.info(f"Summary saved to {SUMMARY_OUTPUT_PATH}")

if __name__ == "__main__":
    main()

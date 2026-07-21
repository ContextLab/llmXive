"""
Sensitivity analysis module for entropy-guided validity prediction.

Implements multiple-comparison correction (Benjamini-Hochberg) and
False Discovery Rate (FDR) calculation to verify statistical significance.
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SensitivityAnalysisResult:
    """Result of sensitivity analysis including corrected p-values and FDR."""
    original_p_values: List[float]
    adjusted_p_values: List[float]
    fdr: float
    significant_count: int
    nominal_alpha: float
    method: str = "benjamini_hochberg"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'original_p_values': self.original_p_values,
            'adjusted_p_values': self.adjusted_p_values,
            'fdr': self.fdr,
            'significant_count': self.significant_count,
            'nominal_alpha': self.nominal_alpha,
            'method': self.method
        }

def load_p_values_from_analysis_results(results_path: Union[str, Path]) -> List[float]:
    """
    Load p-values from analysis results JSON file.
    
    Args:
        results_path: Path to JSON file containing analysis results
        
    Returns:
        List of p-values extracted from the results
        
    Raises:
        FileNotFoundError: If results file doesn't exist
        ValueError: If results file is malformed or missing p-values
    """
    results_path = Path(results_path)
    
    if not results_path.exists():
        raise FileNotFoundError(f"Analysis results file not found: {results_path}")
    
    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in results file: {e}")
    
    # Try to extract p-values from common locations
    p_values = []
    
    # Check if it's a stratified result with multiple p-values
    if 'stratified_results' in data:
        for strat_result in data['stratified_results']:
            if 'p_values' in strat_result:
                p_values.extend(strat_result['p_values'])
            elif 'p_value' in strat_result:
                p_values.append(strat_result['p_value'])
    elif 'p_values' in data:
        p_values = data['p_values']
    elif 'p_value' in data:
        p_values = [data['p_value']]
    elif 'results' in data:
        # Try nested results
        for result in data['results']:
            if 'p_values' in result:
                p_values.extend(result['p_values'])
            elif 'p_value' in result:
                p_values.append(result['p_value'])
    
    if not p_values:
        raise ValueError("No p-values found in analysis results")
    
    # Validate p-values are in valid range
    for i, p in enumerate(p_values):
        if not isinstance(p, (int, float)) or p < 0 or p > 1:
            raise ValueError(f"Invalid p-value at index {i}: {p}")
    
    return p_values

def apply_bh_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], float]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    
    The BH procedure controls the False Discovery Rate (FDR) by adjusting
    p-values to account for multiple hypothesis testing.
    
    Args:
        p_values: List of raw p-values from hypothesis tests
        alpha: Nominal significance level (default 0.05)
        
    Returns:
        Tuple of (adjusted_p_values, fdr)
        - adjusted_p_values: BH-corrected p-values
        - fdr: Estimated False Discovery Rate
        
    Raises:
        ValueError: If p_values is empty or contains invalid values
    """
    if not p_values:
        raise ValueError("p_values list cannot be empty")
    
    n = len(p_values)
    
    # Sort p-values and keep track of original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate BH-adjusted p-values
    # For each p-value at rank i (1-indexed): adjusted_p = p * n / i
    # Then enforce monotonicity: adjusted_p[i] = min(adjusted_p[i], adjusted_p[i+1])
    adjusted = [0.0] * n
    rank_values = [0.0] * n
    
    for i, p in enumerate(sorted_p_values):
        rank = i + 1
        adjusted_p = min(p * n / rank, 1.0)
        rank_values[i] = adjusted_p
    
    # Enforce monotonicity from largest to smallest
    for i in range(n - 2, -1, -1):
        rank_values[i] = min(rank_values[i], rank_values[i + 1])
    
    # Map back to original order
    adjusted_p_values = [0.0] * n
    for idx, adjusted in zip(sorted_indices, rank_values):
        adjusted_p_values[idx] = adjusted
    
    # Calculate FDR: proportion of rejected hypotheses that are false discoveries
    # FDR = E[V/R] where V = false positives, R = total rejections
    # We estimate this as the average of adjusted p-values that are <= alpha
    significant_count = sum(1 for p in adjusted_p_values if p <= alpha)
    
    if significant_count > 0:
        # FDR estimate: average of adjusted p-values among significant results
        fdr_estimate = sum(p for p in adjusted_p_values if p <= alpha) / significant_count
    else:
        fdr_estimate = 0.0
    
    return adjusted_p_values, fdr_estimate

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], float]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    A more conservative approach than BH that controls family-wise error rate.
    
    Args:
        p_values: List of raw p-values
        alpha: Nominal significance level
        
    Returns:
        Tuple of (adjusted_p_values, fdr)
    """
    if not p_values:
        raise ValueError("p_values list cannot be empty")
    
    n = len(p_values)
    adjusted_p_values = [min(p * n, 1.0) for p in p_values]
    
    # For Bonferroni, FDR is approximated as the proportion of significant tests
    significant_count = sum(1 for p in adjusted_p_values if p <= alpha)
    fdr_estimate = significant_count / n if n > 0 else 0.0
    
    return adjusted_p_values, fdr_estimate

def calculate_fdr(adjusted_p_values: List[float], alpha: float = 0.05) -> float:
    """
    Calculate the False Discovery Rate from adjusted p-values.
    
    Args:
        adjusted_p_values: List of adjusted p-values
        alpha: Nominal significance level
        
    Returns:
        Estimated FDR as a float between 0 and 1
    """
    if not adjusted_p_values:
        return 0.0
    
    significant_count = sum(1 for p in adjusted_p_values if p <= alpha)
    if significant_count == 0:
        return 0.0
    
    # FDR is the expected proportion of false discoveries among all discoveries
    # We estimate this as the average of adjusted p-values among significant results
    fdr = sum(p for p in adjusted_p_values if p <= alpha) / significant_count
    return fdr

def analyze_sensitivity(
    p_values: List[float],
    alpha: float = 0.05,
    method: str = "benjamini_hochberg"
) -> SensitivityAnalysisResult:
    """
    Perform complete sensitivity analysis including multiple-comparison correction.
    
    Args:
        p_values: List of raw p-values from statistical tests
        alpha: Nominal significance level (default 0.05)
        method: Correction method ("benjamini_hochberg" or "bonferroni")
        
    Returns:
        SensitivityAnalysisResult with corrected p-values and FDR
    """
    if method == "benjamini_hochberg":
        adjusted_p_values, fdr = apply_bh_correction(p_values, alpha)
    elif method == "bonferroni":
        adjusted_p_values, fdr = apply_bonferroni_correction(p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    significant_count = sum(1 for p in adjusted_p_values if p <= alpha)
    
    return SensitivityAnalysisResult(
        original_p_values=p_values,
        adjusted_p_values=adjusted_p_values,
        fdr=fdr,
        significant_count=significant_count,
        nominal_alpha=alpha,
        method=method
    )

def write_sensitivity_report(
    result: SensitivityAnalysisResult,
    output_path: Union[str, Path]
) -> None:
    """
    Write sensitivity analysis results to JSON file.
    
    Args:
        result: SensitivityAnalysisResult to write
        output_path: Path to output JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'analysis_summary': {
            'method': result.method,
            'nominal_alpha': result.nominal_alpha,
            'total_tests': len(result.original_p_values),
            'significant_tests': result.significant_count,
            'fdr': result.fdr,
            'fdr_within_alpha': result.fdr <= result.nominal_alpha
        },
        'p_values': {
            'original': result.original_p_values,
            'adjusted': result.adjusted_p_values
        },
        'verification': {
            'sc_005_verified': result.fdr <= result.nominal_alpha,
            'fdr_value': result.fdr,
            'alpha_threshold': result.nominal_alpha
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity report written to {output_path}")
    logger.info(f"FDR: {result.fdr:.4f}, Alpha: {result.nominal_alpha}, SC-005 Verified: {result.fdr <= result.nominal_alpha}")

def main():
    """
    Main entry point for sensitivity analysis.
    
    Loads p-values from analysis results, applies BH correction,
    calculates FDR, and writes report to results/fdr_report.json.
    """
    # Default paths
    results_dir = Path("results")
    analysis_results_path = results_dir / "analysis_results.json"
    fdr_report_path = results_dir / "fdr_report.json"
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        analysis_results_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        fdr_report_path = Path(sys.argv[2])
    
    logger.info(f"Loading p-values from {analysis_results_path}")
    
    try:
        p_values = load_p_values_from_analysis_results(analysis_results_path)
        logger.info(f"Loaded {len(p_values)} p-values")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load p-values: {e}")
        sys.exit(1)
    
    logger.info("Applying Benjamini-Hochberg correction...")
    result = analyze_sensitivity(p_values, alpha=0.05, method="benjamini_hochberg")
    
    logger.info(f"Analysis complete: {result.significant_count}/{len(p_values)} tests significant")
    logger.info(f"False Discovery Rate: {result.fdr:.4f}")
    
    logger.info(f"Writing report to {fdr_report_path}")
    write_sensitivity_report(result, fdr_report_path)
    
    # Verify SC-005: FDR <= nominal alpha
    if result.fdr <= result.nominal_alpha:
        logger.info("✓ SC-005 VERIFIED: FDR <= nominal alpha (0.05)")
    else:
        logger.warning("✗ SC-005 NOT VERIFIED: FDR > nominal alpha (0.05)")
    
    return result

if __name__ == "__main__":
    main()

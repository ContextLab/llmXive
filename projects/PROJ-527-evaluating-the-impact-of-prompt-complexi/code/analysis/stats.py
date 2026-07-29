"""
Statistical analysis module for prompt complexity evaluation.

Implements Linear Mixed Models (LMM), pairwise comparisons, effect size calculations,
and comprehensive analysis reporting.
"""
import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.regression.mixed_linear_model import MixedLM
import warnings

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def load_execution_results() -> pd.DataFrame:
    """
    Load execution results from CSV.
    
    Returns:
        DataFrame with columns: problem_id, complexity_label, pass_rate, 
        token_count, structural_element_count, etc.
    """
    results_path = Paths().data_results / "execution_outcomes.csv"
    if not results_path.exists():
        raise FileNotFoundError(f"Execution results not found at {results_path}")
    
    df = pd.read_csv(results_path)
    logger.info(f"Loaded {len(df)} execution results from {results_path}")
    return df


def fit_lmm_with_covariate(
    df: pd.DataFrame,
    dependent_var: str = "pass_rate",
    fixed_effects: List[str] = ["complexity_label"],
    covariate: str = "token_count",
    random_effect: str = "problem_id"
) -> Tuple[MixedLM, Dict[str, Any]]:
    """
    Fit a Linear Mixed Model with covariate adjustment.
    
    Model: dependent_var ~ fixed_effects + covariate + (1 | random_effect)
    
    Args:
        df: DataFrame with execution results
        dependent_var: Name of dependent variable column
        fixed_effects: List of fixed effect column names
        covariate: Name of covariate column (e.g., token_count)
        random_effect: Name of random effect grouping column
        
    Returns:
        Tuple of (fitted model, results dictionary with statistics)
    """
    # Prepare data
    data = df[[dependent_var, random_effect, covariate] + fixed_effects].dropna()
    
    if len(data) == 0:
        raise ValueError("No valid data points after dropping NaN values")
    
    # Encode categorical variables
    for col in fixed_effects:
        if data[col].dtype == 'object':
            data[col] = data[col].astype('category').cat.codes
    
    # Build formula
    fixed_formula = f"{dependent_var} ~ {' + '.join(fixed_effects)} + {covariate}"
    random_formula = f"1 | {random_effect}"
    
    # Fit LMM
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = MixedLM.from_formula(fixed_formula, groups=data[random_effect], 
                                   re_formula="1", data=data)
        result = model.fit()
    
    return result, {
        "model": result,
        "fixed_effects": result.params.to_dict(),
        "random_effects_variance": result.cov_re.iloc[0, 0] if hasattr(result, 'cov_re') else None,
        "log_likelihood": result.llf,
        "aic": result.aic,
        "bic": result.bic,
        "p_values": result.pvalues.to_dict()
    }


def pairwise_comparisons(
    df: pd.DataFrame,
    complexity_levels: List[str],
    dependent_var: str = "pass_rate",
    method: str = "holm"
) -> Dict[str, Any]:
    """
    Perform pairwise comparisons between complexity levels with multiple testing correction.
    
    Args:
        df: DataFrame with execution results
        complexity_levels: List of complexity level labels to compare
        dependent_var: Name of dependent variable column
        method: Correction method ('bonferroni', 'holm', 'fdr_bh')
        
    Returns:
        Dictionary with comparison results including p-values and corrected p-values
    """
    results = []
    p_values = []
    comparisons = []
    
    # Group by complexity level
    groups = {level: df[df['complexity_label'] == level][dependent_var].values 
             for level in complexity_levels if level in df['complexity_label'].unique()}
    
    # Perform pairwise t-tests
    for i, level1 in enumerate(complexity_levels):
        for level2 in complexity_levels[i+1:]:
            if level1 in groups and level2 in groups:
                stat, p_val = stats.ttest_ind(groups[level1], groups[level2], equal_var=False)
                p_values.append(p_val)
                comparisons.append((level1, level2))
                results.append({
                    "comparison": f"{level1}_vs_{level2}",
                    "statistic": stat,
                    "p_value": p_val,
                    "mean_diff": np.mean(groups[level1]) - np.mean(groups[level2])
                })
    
    if not p_values:
        logger.warning("No valid pairwise comparisons found")
        return {"comparisons": [], "corrected_p_values": [], "method": method}
    
    # Apply multiple testing correction
    corrected_p_values = stats.multipletests(p_values, method=method)[1]
    
    # Update results with corrected p-values
    for i, result in enumerate(results):
        result["corrected_p_value"] = corrected_p_values[i]
        result["significant"] = corrected_p_values[i] < 0.05
    
    return {
        "comparisons": results,
        "corrected_p_values": corrected_p_values.tolist(),
        "method": method,
        "num_tests": len(p_values)
    }


def calculate_effect_sizes(
    df: pd.DataFrame,
    group_col: str = "complexity_label",
    value_col: str = "pass_rate",
    reference_group: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate effect sizes (Cohen's d, eta-squared) with standard interpretation.
    
    Args:
        df: DataFrame with execution results
        group_col: Column name for grouping variable
        value_col: Column name for numeric values
        reference_group: Optional reference group for Cohen's d calculations
        
    Returns:
        Dictionary with effect sizes and interpretations
    """
    results = {
        "cohen_d": {},
        "eta_squared": {},
        "interpretation": {}
    }
    
    # Get unique groups
    groups = df[group_col].unique()
    group_data = {g: df[df[group_col] == g][value_col].dropna().values 
                 for g in groups}
    
    # Calculate Cohen's d for each pair
    if reference_group and reference_group in group_data:
        ref_data = group_data[reference_group]
        for group in groups:
            if group != reference_group and group in group_data:
                group_data_vals = group_data[group]
                if len(ref_data) > 1 and len(group_data_vals) > 1:
                    # Pooled standard deviation
                    n1, n2 = len(ref_data), len(group_data_vals)
                    var1, var2 = np.var(ref_data, ddof=1), np.var(group_data_vals, ddof=1)
                    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
                    
                    if pooled_std > 0:
                        cohen_d = (np.mean(group_data_vals) - np.mean(ref_data)) / pooled_std
                        results["cohen_d"][f"{group}_vs_{reference_group}"] = cohen_d
                        
                        # Interpretation
                        abs_d = abs(cohen_d)
                        if abs_d < 0.2:
                            interpretation = "negligible"
                        elif abs_d < 0.5:
                            interpretation = "small"
                        elif abs_d < 0.8:
                            interpretation = "medium"
                        else:
                            interpretation = "large"
                        results["interpretation"][f"{group}_vs_{reference_group}"] = interpretation
    
    # Calculate eta-squared (one-way ANOVA style)
    if len(groups) > 1:
        all_values = df[value_col].dropna()
        grand_mean = np.mean(all_values)
        
        ss_between = 0
        ss_within = 0
        
        for group in groups:
            group_vals = group_data[group]
            if len(group_vals) > 0:
                n_group = len(group_vals)
                ss_between += n_group * (np.mean(group_vals) - grand_mean) ** 2
                ss_within += np.sum((group_vals - np.mean(group_vals)) ** 2)
        
        ss_total = ss_between + ss_within
        
        if ss_total > 0:
            eta_squared = ss_between / ss_total
            results["eta_squared"]["overall"] = eta_squared
            
            # Interpretation for eta-squared
            if eta_squared < 0.01:
                interpretation = "negligible"
            elif eta_squared < 0.06:
                interpretation = "small"
            elif eta_squared < 0.14:
                interpretation = "medium"
            else:
                interpretation = "large"
            results["interpretation"]["overall"] = interpretation
    
    return results


def run_full_analysis(
    df: pd.DataFrame,
    complexity_levels: List[str],
    dependent_var: str = "pass_rate",
    covariate: str = "token_count"
) -> Dict[str, Any]:
    """
    Run complete statistical analysis pipeline.
    
    Args:
        df: DataFrame with execution results
        complexity_levels: List of complexity level labels
        dependent_var: Name of dependent variable
        covariate: Name of covariate for LMM
        
    Returns:
        Comprehensive analysis results dictionary
    """
    logger.info("Starting full statistical analysis")
    
    # Fit LMM
    lmm_result, lmm_stats = fit_lmm_with_covariate(
        df, dependent_var=dependent_var, covariate=covariate
    )
    
    # Pairwise comparisons
    pairwise_results = pairwise_comparisons(
        df, complexity_levels, dependent_var=dependent_var
    )
    
    # Effect sizes
    effect_size_results = calculate_effect_sizes(
        df, group_col="complexity_label", value_col=dependent_var,
        reference_group=complexity_levels[0] if complexity_levels else None
    )
    
    return {
        "lmm": lmm_stats,
        "pairwise_comparisons": pairwise_results,
        "effect_sizes": effect_size_results,
        "summary": {
            "num_observations": len(df),
            "num_complexity_levels": len(complexity_levels),
            "covariate": covariate,
            "dependent_variable": dependent_var
        }
    }


def write_analysis_summary_to_csv(
    analysis_results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write analysis summary to CSV including effect sizes and interpretations.
    
    Args:
        analysis_results: Dictionary from run_full_analysis
        output_path: Optional output path (defaults to data/results/analysis_summary.csv)
        
    Returns:
        Path to written file
    """
    if output_path is None:
        output_path = Paths().data_results / "analysis_summary.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    
    # LMM results
    lmm_stats = analysis_results["lmm"]
    for effect, value in lmm_stats["fixed_effects"].items():
        p_value = lmm_stats["p_values"].get(effect, np.nan)
        rows.append({
            "analysis_type": "lmm_fixed_effect",
            "parameter": effect,
            "estimate": value,
            "p_value": p_value,
            "effect_size": np.nan,
            "interpretation": np.nan
        })
    
    # Pairwise comparisons
    for comp in analysis_results["pairwise_comparisons"]["comparisons"]:
        rows.append({
            "analysis_type": "pairwise_comparison",
            "parameter": comp["comparison"],
            "estimate": comp["mean_diff"],
            "p_value": comp["p_value"],
            "corrected_p_value": comp["corrected_p_value"],
            "effect_size": np.nan,
            "interpretation": "significant" if comp["significant"] else "not_significant"
        })
    
    # Effect sizes
    for comparison, cohen_d in analysis_results["effect_sizes"]["cohen_d"].items():
        interpretation = analysis_results["effect_sizes"]["interpretation"].get(comparison, "unknown")
        rows.append({
            "analysis_type": "cohen_d",
            "parameter": comparison,
            "estimate": np.nan,
            "p_value": np.nan,
            "corrected_p_value": np.nan,
            "effect_size": cohen_d,
            "interpretation": interpretation
        })
    
    # Eta-squared
    for metric, eta_sq in analysis_results["effect_sizes"]["eta_squared"].items():
        interpretation = analysis_results["effect_sizes"]["interpretation"].get(metric, "unknown")
        rows.append({
            "analysis_type": "eta_squared",
            "parameter": f"overall_{metric}" if metric != "overall" else "overall",
            "estimate": np.nan,
            "p_value": np.nan,
            "corrected_p_value": np.nan,
            "effect_size": eta_sq,
            "interpretation": interpretation
        })
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    logger.info(f"Analysis summary written to {output_path}")
    return output_path


def main():
    """Main entry point for statistical analysis."""
    logger.info("Running statistical analysis pipeline")
    
    # Load data
    df = load_execution_results()
    
    # Define complexity levels
    complexity_levels = ['simple', 'moderate', 'complex', 'very_complex', 'degenerate']
    
    # Run full analysis
    results = run_full_analysis(df, complexity_levels)
    
    # Write summary
    output_path = write_analysis_summary_to_csv(results)
    
    logger.info(f"Analysis complete. Results written to {output_path}")
    
    return results


if __name__ == "__main__":
    main()
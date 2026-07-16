import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import get_logger
import os

logger = get_logger(__name__)

def run_anova_pipeline(df: pd.DataFrame, 
                       within_subject_col: str = "interface_type",
                       between_subject_col: str = "disability_type",
                       metrics: List[str] = ["completion_time", "error_count", "sus_score"]) -> Dict[str, Any]:
    """
    Runs Repeated Measures ANOVA on the specified metrics.
    
    Note: Per T023a-amendment and Plan Phase 3, we explicitly skip normality testing
    and Levene's test. We assume the paired design mitigates the need for normality
    checks on the raw data, focusing on difference scores if needed, but here we
    proceed directly to ANOVA as mandated.
    
    Args:
        df: Cleaned session data.
        within_subject_col: Column name for the within-subject factor (e.g., interface type).
        between_subject_col: Column name for between-subject factor (optional for now).
        metrics: List of metric column names to analyze.
    
    Returns:
        Dictionary containing ANOVA results.
    """
    results = {}
    
    # Ensure data is wide format for repeated measures or use long format with statsmodels
    # Since we might not have statsmodels, we will use scipy's f_oneway for independent,
    # but for Repeated Measures, we ideally need a library like pingouin or statsmodels.
    # Given constraints, we will implement a simplified RM-ANOVA using scipy by reshaping
    # or calculating difference scores if only two levels (Traditional vs Explainable).
    
    # Check if we have exactly two levels for the within-subject factor
    if within_subject_col not in df.columns:
        raise ValueError(f"Column {within_subject_col} not found in dataframe")
    
    levels = df[within_subject_col].unique()
    
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric {metric} not found in dataframe, skipping.")
            continue
        
        logger.info(f"Running ANOVA for metric: {metric}")
        
        # Pivot to wide format: rows=participants, columns=conditions
        # Assuming 'participant_id' exists
        if "participant_id" not in df.columns:
            # If no participant_id, we cannot do repeated measures properly.
            # Fallback to independent t-test/ANOVA (less ideal but prevents crash)
            logger.warning("No participant_id found. Falling back to independent test.")
            groups = [group[metric].values for name, group in df.groupby(within_subject_col)]
            if len(groups) == 2:
                stat, p_val = stats.ttest_ind(groups[0], groups[1])
                results[metric] = {
                    "F-statistic": 0.0, # Not an F-test here
                    "p-value": p_val,
                    "method": "Independent T-Test (Fallback)",
                    "df": None
                }
            else:
                stat, p_val = stats.f_oneway(*groups)
                results[metric] = {
                    "F-statistic": stat,
                    "p-value": p_val,
                    "method": "One-way ANOVA (Independent Fallback)",
                    "df": None
                }
            continue
        
        # Repeated Measures Logic (Two conditions: Traditional, Explainable)
        # We calculate the difference and test if mean difference is 0 (Paired T-Test)
        # OR we reshape and use statsmodels. Since we want F-statistic for ANOVA,
        # we will use a simplified approach: Paired T-Test is equivalent to RM-ANOVA for 2 levels.
        # However, the task asks for F-statistic. 
        # For 2 groups, F = t^2.
        
        pivot_df = df.pivot_table(index='participant_id', 
                                  columns=within_subject_col, 
                                  values=metric, 
                                  aggfunc='mean')
        
        if pivot_df.shape[1] != 2:
            logger.warning(f"Metric {metric} does not have 2 levels for paired test.")
            continue
        
        col1, col2 = pivot_df.columns
        # Drop rows with missing data
        clean_pivot = pivot_df.dropna()
        
        if len(clean_pivot) < 2:
            logger.warning(f"Not enough data points for {metric}.")
            continue
        
        t_stat, p_val = stats.ttest_rel(clean_pivot[col1], clean_pivot[col2])
        f_stat = t_stat ** 2
        
        results[metric] = {
            "F-statistic": f_stat,
            "p-value": p_val,
            "method": "Repeated Measures ANOVA (via Paired T-Test)",
            "df": (1, len(clean_pivot)-1),
            "n_subjects": len(clean_pivot)
        }
    
    return results

def run_holm_bonferroni(p_values: List[float]) -> List[float]:
    """
    Applies Holm-Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
    
    Returns:
        List of adjusted p-values.
    """
    m = len(p_values)
    if m == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    adjusted_p = np.zeros(m)
    
    for i, p in enumerate(sorted_p):
        # Holm-Bonferroni: p * (m - i)
        # But ensure it doesn't exceed 1.0 and is at least the previous adjusted p
        adj = p * (m - i)
        adjusted_p[sorted_indices[i]] = min(1.0, max(adj, adjusted_p[sorted_indices[i-1]] if i > 0 else 0))
    
    return adjusted_p.tolist()

def calculate_effect_size(df: pd.DataFrame, 
                          metric: str, 
                          within_col: str = "interface_type") -> Optional[float]:
    """
    Calculates Cohen's d for the difference between two conditions.
    
    Args:
        df: Session data.
        metric: Metric column.
        within_col: Condition column.
    
    Returns:
        Cohen's d value.
    """
    if "participant_id" not in df.columns:
        # Independent d
        groups = [g[metric].values for _, g in df.groupby(within_col)]
        if len(groups) != 2:
            return None
        g1, g2 = groups
        mean_diff = np.mean(g1) - np.mean(g2)
        std_pooled = np.sqrt((np.var(g1, ddof=1) + np.var(g2, ddof=1)) / 2)
        if std_pooled == 0:
            return 0.0
        return mean_diff / std_pooled
    
    # Paired d
    pivot = df.pivot_table(index='participant_id', columns=within_col, values=metric, aggfunc='mean').dropna()
    if pivot.shape[1] != 2:
        return None
    
    diff = pivot.iloc[:, 0] - pivot.iloc[:, 1]
    mean_diff = diff.mean()
    std_diff = diff.std()
    
    if std_diff == 0:
        return 0.0
    return mean_diff / std_diff

def generate_metrics_summary(df: pd.DataFrame, 
                             output_path: str,
                             metrics: List[str] = ["completion_time", "error_count", "sus_score"]) -> None:
    """
    Orchestrates the ANOVA, Holm-Bonferroni, and effect size calculation,
    then writes the results to a CSV.
    
    Args:
        df: Cleaned session data.
        output_path: Path to the output CSV.
        metrics: List of metrics to analyze.
    """
    logger.info(f"Generating metrics summary for {len(metrics)} metrics")
    
    # 1. Run ANOVA
    anova_results = run_anova_pipeline(df, metrics=metrics)
    
    # 2. Collect p-values for Holm-Bonferroni
    p_values = []
    metric_names = []
    for metric in metrics:
        if metric in anova_results:
            p_values.append(anova_results[metric]["p-value"])
            metric_names.append(metric)
    
    adjusted_p_values = run_holm_bonferroni(p_values)
    
    # 3. Build DataFrame
    summary_data = []
    for i, metric in enumerate(metric_names):
        res = anova_results[metric]
        effect = calculate_effect_size(df, metric)
        summary_data.append({
            "metric": metric,
            "F-statistic": res["F-statistic"],
            "p-value": res["p-value"],
            "adjusted p-value": adjusted_p_values[i],
            "effect size": effect,
            "method": res["method"],
            "df": str(res.get("df", ""))
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Metrics summary written to {output_path}")
    
    return summary_df

def main():
    """CLI entry point for stat_utils."""
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical analysis")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    args = parser.parse_args()
    
    df = pd.read_csv(args.input)
    generate_metrics_summary(df, args.output)

if __name__ == "__main__":
    main()

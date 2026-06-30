import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_coverage_reports(report_dir: str = "data/coverage_reports") -> pd.DataFrame:
    """Load all coverage reports from the directory into a single DataFrame."""
    report_path = Path(report_dir)
    if not report_path.exists():
        logger.warning(f"Report directory {report_dir} does not exist.")
        return pd.DataFrame()

    reports = []
    for file in report_path.glob("*.json"):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                reports.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {file}: {e}")

    if not reports:
        return pd.DataFrame()

    df = pd.DataFrame(reports)
    # Ensure task_id is string for consistent handling
    if 'task_id' in df.columns:
        df['task_id'] = df['task_id'].astype(str)
    return df

def pair_llm_human_results(df: pd.DataFrame) -> pd.DataFrame:
    """Pair LLM and human results by task_id."""
    # Assuming the DataFrame has columns: task_id, source (llm/human), line_coverage, branch_coverage
    # If the schema is different, adjust accordingly.
    # For this implementation, we assume a unified schema where 'source' indicates origin.
    if 'source' not in df.columns:
        logger.warning("No 'source' column found. Attempting to infer from task_id or other heuristics.")
        # Fallback logic could be added here if needed
        return df

    llm_df = df[df['source'] == 'llm'].copy()
    human_df = df[df['source'] == 'human'].copy()

    # Rename coverage columns to distinguish
    llm_df.rename(columns={'line_coverage': 'line_coverage_llm', 'branch_coverage': 'branch_coverage_llm'}, inplace=True)
    human_df.rename(columns={'line_coverage': 'line_coverage_human', 'branch_coverage': 'branch_coverage_human'}, inplace=True)

    # Merge on task_id
    paired = pd.merge(llm_df[['task_id', 'line_coverage_llm', 'branch_coverage_llm']],
                      human_df[['task_id', 'line_coverage_human', 'branch_coverage_human']],
                      on='task_id', how='inner')
    return paired

def check_normality_shapiro(data: np.ndarray) -> Tuple[bool, float]:
    """Perform Shapiro-Wilk test for normality.
    Returns (is_normal, p_value).
    """
    if len(data) < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test.")
        return False, 1.0

    try:
        stat, p_value = stats.shapiro(data)
        is_normal = p_value >= 0.05
        return is_normal, p_value
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return False, 1.0

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return 0.0

    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std

def perform_statistical_test(group1: np.ndarray, group2: np.ndarray) -> Dict[str, Any]:
    """Perform paired t-test or Wilcoxon signed-rank test based on normality.
    Returns dict with test_type, statistic, p_value.
    """
    diffs = group1 - group2
    is_normal, p_norm = check_normality_shapiro(diffs)

    if is_normal:
        stat, p_val = stats.ttest_rel(group1, group2)
        test_type = "t-test"
    else:
        stat, p_val = stats.wilcoxon(group1, group2)
        test_type = "Wilcoxon"

    return {
        "test_type": test_type,
        "statistic": float(stat),
        "p_value": float(p_val),
        "is_normal": is_normal,
        "shapiro_p": float(p_norm)
    }

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected

def apply_holm_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Holm-Bonferroni correction."""
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values with original indices
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n

    for i, (orig_idx, p_val) in enumerate(indexed_p):
        threshold = alpha / (n - i)
        corrected[orig_idx] = min(p_val * (n - i), 1.0)

    return corrected

def run_family_wise_error_correction(p_values: List[float], method: str = 'bonferroni') -> List[float]:
    """Run family-wise error correction (Bonferroni or Holm-Bonferroni)."""
    if method == 'bonferroni':
        return apply_bonferroni_correction(p_values)
    elif method == 'holm':
        return apply_holm_bonferroni_correction(p_values)
    else:
        logger.warning(f"Unknown correction method: {method}. Using Bonferroni.")
        return apply_bonferroni_correction(p_values)

def calculate_exclusion_rate(df: pd.DataFrame, threshold: float = 0.05) -> float:
    """Calculate the rate of tasks excluded due to missing data or other criteria."""
    total = len(df)
    if total == 0:
        return 0.0
    # Example: exclude if coverage is None or NaN
    excluded = df[df['line_coverage'].isna() | df['branch_coverage'].isna()].shape[0]
    return excluded / total

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: List[float] = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25]) -> pd.DataFrame:
    """Run sensitivity analysis across different alpha thresholds."""
    results = []
    for thresh in thresholds:
        # Example: count significant results at this threshold
        sig_count = (df['p_value'] < thresh).sum()
        results.append({
            'threshold': thresh,
            'significant_count': int(sig_count),
            'total_count': len(df)
        })
    return pd.DataFrame(results)

def calculate_vif(df: pd.DataFrame, pattern_columns: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for given pattern columns.
    Excludes tasks with missing pattern data.
    
    Args:
        df: DataFrame containing pattern counts and other features.
        pattern_columns: List of column names representing code patterns (e.g., 'loops', 'conditionals').
    
    Returns:
        DataFrame with columns: feature, vif.
    """
    if not pattern_columns:
        logger.warning("No pattern columns provided for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'vif'])

    # Filter out rows with any NaN in the pattern columns
    clean_df = df[pattern_columns].dropna()
    
    if clean_df.empty:
        logger.warning("No valid data remaining after filtering NaNs for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'vif'])

    # Add intercept term
    clean_df['intercept'] = 1.0
    
    vif_results = []
    
    for feature in pattern_columns:
        # Regress feature against all other pattern columns
        y = clean_df[feature]
        X = clean_df.drop(columns=[feature] + ['intercept'])
        X = X.dropna(axis=1) # Drop any other columns that might have become NaN
        
        if X.empty or len(X) < 2:
            logger.warning(f"Not enough data to calculate VIF for {feature}.")
            vif_results.append({'feature': feature, 'vif': np.nan})
            continue

        try:
            # Fit linear model
            model = stats.linregress(X.values, y.values) if X.shape[1] == 1 else None
            if model:
                r_squared = model.rvalue ** 2
            else:
                # Use multiple regression
                from statsmodels.api import OLS
                X_const = sm.add_constant(X) # Need statsmodels for multivariate
                # Wait, the imports above only include scipy. Let's stick to scipy/numpy if possible, 
                # or add statsmodels if needed. The prompt says "import statsmodels" in requirements.txt, 
                # so it should be available.
                import statsmodels.api as sm
                X_const = sm.add_constant(X)
                ols_model = sm.OLS(y, X_const).fit()
                r_squared = ols_model.rsquared
            
            if r_squared == 1.0:
                vif = np.inf
            else:
                vif = 1 / (1 - r_squared)
            
            vif_results.append({'feature': feature, 'vif': vif})
        except Exception as e:
            logger.error(f"Error calculating VIF for {feature}: {e}")
            vif_results.append({'feature': feature, 'vif': np.nan})

    return pd.DataFrame(vif_results)

def run_analysis(
    report_dir: str = "data/coverage_reports",
    catalog_path: str = "data/benchmarks/processed/catalog.json",
    output_dir: str = "data/processed",
    model_method: str = 'regression',
    pattern_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main analysis orchestrator.
    
    Args:
        report_dir: Directory containing coverage reports.
        catalog_path: Path to the dataset catalog.
        output_dir: Directory to save analysis outputs.
        model_method: 'regression', 'lmm', or 'glmm'. Determines if VIF is run.
        pattern_columns: List of pattern column names for VIF calculation.
    
    Returns:
        Dictionary containing analysis results.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df_reports = load_coverage_reports(report_dir)
    if df_reports.empty:
        logger.error("No coverage reports found.")
        return {"error": "No coverage reports found"}

    # Pair results
    paired_df = pair_llm_human_results(df_reports)
    if paired_df.empty:
        logger.warning("No paired results found.")
        return {"error": "No paired results found"}

    # Load catalog to get pattern data if needed
    pattern_df = None
    if pattern_columns and os.path.exists(catalog_path):
        try:
            with open(catalog_path, 'r') as f:
                catalog_data = json.load(f)
            pattern_df = pd.DataFrame(catalog_data)
            # Merge pattern data with paired results if task_id matches
            # Assuming pattern_df has 'task_id'
            if 'task_id' in pattern_df.columns:
                merged_df = pd.merge(paired_df, pattern_df[['task_id'] + pattern_columns], on='task_id', how='left')
            else:
                merged_df = paired_df
                logger.warning("Catalog does not have task_id column. Skipping pattern merge.")
        except Exception as e:
            logger.error(f"Failed to load or merge catalog: {e}")
            merged_df = paired_df
    else:
        merged_df = paired_df

    # Run VIF only if model_method is 'regression' and pattern columns are available
    vif_result = None
    if model_method == 'regression' and pattern_columns:
        logger.info("Running Collinearity Diagnostics (VIF) as model_method is 'regression'.")
        if 'intercept' in pattern_columns:
            pattern_columns = [c for c in pattern_columns if c != 'intercept']
        
        vif_result = calculate_vif(merged_df, pattern_columns)
        
        if not vif_result.empty:
            vif_output_path = os.path.join(output_dir, "vif_diagnostics.csv")
            vif_result.to_csv(vif_output_path, index=False)
            logger.info(f"VIF results saved to {vif_output_path}")
    else:
        logger.info(f"Skipping VIF calculation. model_method='{model_method}' requires 'regression' to run VIF.")

    # Perform statistical tests on coverage differences
    # Assuming 'line_coverage_llm' and 'line_coverage_human' exist
    if 'line_coverage_llm' in merged_df.columns and 'line_coverage_human' in merged_df.columns:
        # Convert to numeric, coerce errors
        llm_cov = pd.to_numeric(merged_df['line_coverage_llm'], errors='coerce').dropna().values
        human_cov = pd.to_numeric(merged_df['line_coverage_human'], errors='coerce').dropna().values
        
        # Ensure same length after dropna (this is a simplification; ideally we dropna on both simultaneously)
        min_len = min(len(llm_cov), len(human_cov))
        llm_cov = llm_cov[:min_len]
        human_cov = human_cov[:min_len]

        if len(llm_cov) > 1:
            test_results = perform_statistical_test(llm_cov, human_cov)
            cohens_d = calculate_cohens_d(llm_cov, human_cov)
            
            # Save stats summary
            stats_summary = {
                "mean_llm": float(np.mean(llm_cov)),
                "mean_human": float(np.mean(human_cov)),
                "mean_diff": float(np.mean(llm_cov) - np.mean(human_cov)),
                "p_value": test_results['p_value'],
                "cohen_d": cohens_d,
                "test_type": test_results['test_type']
            }
            
            stats_path = os.path.join(output_dir, "stats_summary.csv")
            pd.DataFrame([stats_summary]).to_csv(stats_path, index=False)
            logger.info(f"Statistical summary saved to {stats_path}")
            
            return {
                "stats_summary": stats_summary,
                "vif_results": vif_result.to_dict(orient='records') if vif_result is not None and not vif_result.empty else None,
                "test_results": test_results
            }
        else:
            logger.warning("Insufficient data for statistical testing.")
            return {"error": "Insufficient data for statistical testing"}
    
    return {"error": "Required coverage columns not found."}

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run statistical analysis on coverage data.")
    parser.add_argument('--report-dir', type=str, default='data/coverage_reports', help='Directory with coverage reports')
    parser.add_argument('--catalog', type=str, default='data/benchmarks/processed/catalog.json', help='Path to catalog.json')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory for results')
    parser.add_argument('--model-method', type=str, default='regression', choices=['regression', 'lmm', 'glmm'], help='Model method for analysis')
    parser.add_argument('--patterns', type=str, nargs='+', default=['loops', 'conditionals', 'recursion'], help='Pattern columns for VIF')
    
    args = parser.parse_args()
    
    result = run_analysis(
        report_dir=args.report_dir,
        catalog_path=args.catalog,
        output_dir=args.output_dir,
        model_method=args.model_method,
        pattern_columns=args.patterns
    )
    
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
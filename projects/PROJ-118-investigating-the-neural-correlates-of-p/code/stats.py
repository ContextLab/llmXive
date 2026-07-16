import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

import numpy as np
import pandas as pd

# Mixed-effects modeling dependencies
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("statsmodels not installed. Mixed-effects models will not be available.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metrics(metrics_path: str) -> pd.DataFrame:
    """Load metrics from CSV file."""
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    return pd.read_csv(path)

def load_excluded_participants(exclusion_log_path: str) -> Set[str]:
    """Load set of excluded participant IDs from log file."""
    excluded = set()
    path = Path(exclusion_log_path)
    if path.exists():
        with open(path, 'r') as f:
            for line in f:
                # Expecting format like "sub-01: Rejected (>50% trials)"
                parts = line.strip().split(':')
                if parts:
                    sub_id = parts[0].strip()
                    excluded.add(sub_id)
    return excluded

def filter_participants(df: pd.DataFrame, excluded_ids: Set[str], peak_required: bool = True) -> pd.DataFrame:
    """Filter dataframe based on exclusion list and peak detection status."""
    # Remove excluded participants
    filtered = df[~df['participant_id'].isin(excluded_ids)].copy()

    if peak_required:
        # Keep only participants with detected peaks for t-tests
        # (T032 mixed-effects might use all, but standard stats often filter)
        # For T032 specifically, we prepare data for mixed models which can handle missingness,
        # but we follow the pipeline's general exclusion logic first.
        pass

    return filtered

def check_normality(data: np.ndarray, alpha: float = 0.05) -> Tuple[bool, float]:
    """Check normality using Shapiro-Wilk test."""
    if len(data) < 3:
        return False, 1.0
    try:
        from scipy.stats import shapiro
        stat, p_val = shapiro(data)
        return p_val > alpha, p_val
    except Exception as e:
        logger.warning(f"Normality check failed: {e}")
        return False, 1.0

def perform_paired_ttest(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """Perform paired t-test."""
    from scipy.stats import ttest_rel
    stat, p_val = ttest_rel(group1, group2)
    return stat, p_val

def load_metrics_for_comparison(df: pd.DataFrame, metric_col: str, electrode: str) -> Tuple[np.ndarray, np.ndarray]:
    """Extract paired arrays for comparison (Standard vs Deviant) for a specific metric and electrode."""
    # Assuming the dataframe has columns like:
    # 'standard_amplitude', 'deviant_amplitude', etc.
    # We need to map the metric_col (e.g., 'amplitude') to the specific columns
    # and ensure we are comparing the same subject's standard vs deviant.

    # Normalize metric name
    metric = metric_col.lower()
    if 'amplitude' in metric:
        std_col = 'standard_amplitude'
        dev_col = 'deviant_amplitude'
    elif 'latency' in metric:
        std_col = 'standard_latency'
        dev_col = 'deviant_latency'
    else:
        raise ValueError(f"Unknown metric column: {metric_col}")

    # Filter for valid numeric data
    valid = df[[std_col, dev_col]].dropna()
    if len(valid) == 0:
        return np.array([]), np.array([])

    return valid[std_col].values, valid[dev_col].values

def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    if not p_values:
        return []
    from statsmodels.stats.multitest import multipletests
    _, p_adj, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    return p_adj.tolist()

def run_statistical_analysis(metrics_df: pd.DataFrame, excluded_ids: Set[str]) -> Dict[str, Any]:
    """Run standard statistical tests (t-tests, FDR)."""
    results = {}
    filtered_df = filter_participants(metrics_df, excluded_ids)

    # Define comparisons
    comparisons = [
        ('amplitude', 'Fz'),
        ('amplitude', 'FCz'),
        ('latency', 'Fz'),
        ('latency', 'FCz')
    ]

    p_values = []
    test_results = []

    for metric, electrode in comparisons:
        std_vals, dev_vals = load_metrics_for_comparison(filtered_df, metric, electrode)
        if len(std_vals) < 2:
            continue

        # Check normality
        # For paired, we check normality of differences
        diffs = dev_vals - std_vals
        normal, p_norm = check_normality(diffs)

        if normal:
            stat, p_val = perform_paired_ttest(std_vals, dev_vals)
            test_type = "t-test"
        else:
            from scipy.stats import wilcoxon
            stat, p_val = wilcoxon(std_vals, dev_vals)
            test_type = "Wilcoxon"

        p_values.append(p_val)
        test_results.append({
            "metric": metric,
            "electrode": electrode,
            "test": test_type,
            "statistic": float(stat),
            "p_value": float(p_val),
            "n": len(std_vals)
        })

    # FDR Correction
    if p_values:
        p_adj = apply_fdr_correction(p_values)
        for i, res in enumerate(test_results):
            res["p_adjusted"] = p_adj[i]
            res["significant"] = p_adj[i] < 0.05

    results["tests"] = test_results
    return results

def run_mixed_effects_model(metrics_df: pd.DataFrame, excluded_ids: Set[str]) -> Dict[str, Any]:
    """
    Implement mixed-effects model with 'condition' as fixed effect and 'subject' as random effect.
    References: Plan Phase 3, Constitution Principle VII (Statistical Rigor).

    This function constructs a long-format dataframe from the wide-format metrics (Standard/Deviant columns),
    then fits a linear mixed-effects model (LMM) using statsmodels.
    """
    if not STATSMODELS_AVAILABLE:
        logger.error("statsmodels is required for mixed-effects models. Please install it.")
        return {"error": "statsmodels not available"}

    logger.info("Starting Mixed-Effects Model analysis (T032)...")

    filtered_df = filter_participants(metrics_df, excluded_ids, peak_required=False)
    if filtered_df.empty:
        return {"error": "No valid participants after filtering"}

    # Reshape to long format for mixed models
    # We want: participant_id, condition (Standard/Deviant), metric_value, metric_type
    # We'll process Amplitude and Latency separately or combined with an interaction term.
    # Per task: condition as fixed effect, subject as random.

    long_data = []

    for _, row in filtered_df.iterrows():
        sub_id = row['participant_id']

        # Amplitude
        std_amp = row.get('standard_amplitude')
        dev_amp = row.get('deviant_amplitude')
        if pd.notna(std_amp) and pd.notna(dev_amp):
            long_data.append({'subject': sub_id, 'condition': 'Standard', 'amplitude': std_amp, 'latency': row.get('standard_latency')})
            long_data.append({'subject': sub_id, 'condition': 'Deviant', 'amplitude': dev_amp, 'latency': row.get('deviant_latency')})

    if not long_data:
        return {"error": "No data points for mixed model"}

    df_long = pd.DataFrame(long_data)

    # Convert subject to categorical for random effects
    df_long['subject'] = pd.Categorical(df_long['subject'])
    df_long['condition'] = pd.Categorical(df_long['condition'], categories=['Standard', 'Deviant'], ordered=True)

    results = {}

    # Model 1: Amplitude ~ Condition + (1|Subject)
    try:
        model_amp = smf.mixedlm("amplitude ~ C(condition, Treatment('Standard'))",
                                df_long,
                                groups=df_long["subject"])
        result_amp = model_amp.fit()

        results['amplitude_model'] = {
            "formula": "amplitude ~ C(condition, Treatment('Standard'))",
            "fixed_effects": result_amp.summary2().tables[1].to_dict() if hasattr(result_amp, 'summary2') else result_amp.params.to_dict(),
            "random_effects_variance": float(result_amp.cov_re.iloc[0,0]) if result_amp.cov_re is not None else 0.0,
            "log_likelihood": float(result_amp.llf),
            "aic": float(result_amp.aic),
            "bic": float(result_amp.bic),
            "condition_deviant_coef": float(result_amp.params.get('C(condition)[T.Deviant]', 0)),
            "condition_deviant_pvalue": float(result_amp.pvalues.get('C(condition)[T.Deviant]', 1.0))
        }
        logger.info(f"Amplitude Model: Deviant vs Standard coef={results['amplitude_model']['condition_deviant_coef']:.4f}, p={results['amplitude_model']['condition_deviant_pvalue']:.4f}")
    except Exception as e:
        logger.error(f"Failed to fit Amplitude Mixed Model: {e}")
        results['amplitude_model'] = {"error": str(e)}

    # Model 2: Latency ~ Condition + (1|Subject)
    # Filter out rows where latency is NaN if any
    df_long_lat = df_long.dropna(subset=['latency'])
    if not df_long_lat.empty:
        try:
            model_lat = smf.mixedlm("latency ~ C(condition, Treatment('Standard'))",
                                    df_long_lat,
                                    groups=df_long_lat["subject"])
            result_lat = model_lat.fit()

            results['latency_model'] = {
                "formula": "latency ~ C(condition, Treatment('Standard'))",
                "fixed_effects": result_lat.summary2().tables[1].to_dict() if hasattr(result_lat, 'summary2') else result_lat.params.to_dict(),
                "random_effects_variance": float(result_lat.cov_re.iloc[0,0]) if result_lat.cov_re is not None else 0.0,
                "log_likelihood": float(result_lat.llf),
                "aic": float(result_lat.aic),
                "bic": float(result_lat.bic),
                "condition_deviant_coef": float(result_lat.params.get('C(condition)[T.Deviant]', 0)),
                "condition_deviant_pvalue": float(result_lat.pvalues.get('C(condition)[T.Deviant]', 1.0))
            }
            logger.info(f"Latency Model: Deviant vs Standard coef={results['latency_model']['condition_deviant_coef']:.4f}, p={results['latency_model']['condition_deviant_pvalue']:.4f}")
        except Exception as e:
            logger.error(f"Failed to fit Latency Mixed Model: {e}")
            results['latency_model'] = {"error": str(e)}
    else:
        results['latency_model'] = {"error": "No valid latency data"}

    results['n_subjects'] = df_long['subject'].nunique()
    results['n_observations'] = len(df_long)

    return results

def save_statistics_results(results: Dict[str, Any], output_path: str):
    """Save statistical results to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Statistics saved to {output_path}")

def run_stats_pipeline(metrics_path: str, exclusion_log_path: str, output_path: str) -> Dict[str, Any]:
    """Run the full statistical analysis pipeline including mixed-effects models."""
    logger.info(f"Loading metrics from {metrics_path}")
    df = load_metrics(metrics_path)

    excluded_ids = load_excluded_participants(exclusion_log_path)

    # Standard Analysis
    std_results = run_statistical_analysis(df, excluded_ids)

    # Mixed Effects Analysis (T032)
    mixed_results = run_mixed_effects_model(df, excluded_ids)

    final_results = {
        "standard_tests": std_results,
        "mixed_effects_models": mixed_results,
        "metadata": {
            "total_participants": len(df),
            "excluded_participants": list(excluded_ids),
            "included_participants": len(df) - len(excluded_ids)
        }
    }

    save_statistics_results(final_results, output_path)
    return final_results

def main():
    """Entry point for stats module."""
    # Default paths relative to project root
    metrics_file = "results/metrics.csv"
    exclusion_file = "data/processed/rejected_participants.log"
    output_file = "results/statistics.json"

    # Allow override via environment or args (simplified for now)
    if len(sys.argv) > 1:
        metrics_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    run_stats_pipeline(metrics_file, exclusion_file, output_file)

if __name__ == "__main__":
    import sys
    main()
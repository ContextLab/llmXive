import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from config import get_path, ensure_dirs

logger = logging.getLogger(__name__)

def load_feature_matrix() -> pd.DataFrame:
    """Load the processed feature matrix from disk."""
    path = get_path("data/processed/features.csv")
    if not path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {path}")
    return pd.read_csv(path)

def prepare_group_data(df: pd.DataFrame, group_col: str = "label", target_label: str = "AD") -> Tuple[pd.Series, pd.Series]:
    """Separate data into target and control groups."""
    target = df[df[group_col] == target_label]
    control = df[df[group_col] == "Control"]
    return target, control

def run_mann_whitney_u(group1: pd.Series, group2: pd.Series) -> Tuple[float, float]:
    """Run Mann-Whitney U test and return statistic and p-value."""
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Need at least 2 samples in each group for Mann-Whitney U.")
    stat, pval = mannwhitneyu(group1, group2, alternative='two-sided')
    return float(stat), float(pval)

def calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """Calculate Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = group1.mean(), group2.mean()
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)
    
    if var1 is None or var2 is None or (var1 + var2) == 0:
        return 0.0
        
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((mean1 - mean2) / pooled_std)

def run_group_comparisons(df: pd.DataFrame, feature_cols: List[str], group_col: str = "label") -> List[Dict[str, Any]]:
    """Run statistical comparisons for all features between Control and AD groups."""
    target, control = prepare_group_data(df, group_col, "AD")
    results = []
    
    for col in feature_cols:
        try:
            stat, pval = run_mann_whitney_u(target[col], control[col])
            d = calculate_cohens_d(target[col], control[col])
            results.append({
                "feature": col,
                "statistic": stat,
                "p_value": pval,
                "cohens_d": d,
                "n_control": len(control),
                "n_target": len(target)
            })
        except ValueError as e:
            logger.warning(f"Skipped {col} due to insufficient data: {e}")
            results.append({
                "feature": col,
                "statistic": None,
                "p_value": None,
                "cohens_d": None,
                "n_control": len(control),
                "n_target": len(target),
                "error": str(e)
            })
    return results

def apply_bonferroni_correction(results: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """Apply Bonferroni correction to p-values."""
    n_tests = len([r for r in results if r["p_value"] is not None])
    if n_tests == 0:
        return results
        
    adjusted_alpha = alpha / n_tests
    for res in results:
        if res["p_value"] is not None:
            res["p_value_adjusted"] = min(res["p_value"] * n_tests, 1.0)
            res["is_significant_adjusted"] = res["p_value_adjusted"] < adjusted_alpha
        else:
            res["p_value_adjusted"] = None
            res["is_significant_adjusted"] = False
    return results

def check_sample_sizes(df: pd.DataFrame, group_col: str = "label", threshold: int = 10, metadata_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if any group has fewer than 'threshold' participants.
    Logs a WARNING and flags the dataset as 'low_power' in metadata if so.
    """
    counts = df[group_col].value_counts().to_dict()
    low_power_detected = False
    low_power_groups = []

    for group, count in counts.items():
        if count < threshold:
            low_power_detected = True
            low_power_groups.append({"group": group, "count": count})
            logger.warning(f"Low sample size detected for group '{group}': {count} < {threshold}")

    status_flag = {}
    if low_power_detected:
        status_flag["low_power"] = True
        status_flag["low_power_groups"] = low_power_groups
        logger.warning("Dataset flagged as 'low_power' due to insufficient sample sizes.")
    else:
        status_flag["low_power"] = False
        status_flag["group_counts"] = counts

    # Update metadata file
    if metadata_path is None:
        metadata_path = str(get_path("data/results/metadata.json"))
    
    ensure_dirs(Path(metadata_path).parent)
    
    existing_metadata = {}
    if Path(metadata_path).exists():
        try:
            with open(metadata_path, 'r') as f:
                existing_metadata = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not parse existing metadata.json, starting fresh.")

    existing_metadata.update(status_flag)
    
    with open(metadata_path, 'w') as f:
        json.dump(existing_metadata, f, indent=2)
    
    logger.info(f"Sample size check complete. Metadata updated at {metadata_path}")
    return status_flag

def save_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """Save statistical results to JSON."""
    if output_path is None:
        output_path = str(get_path("data/results/statistical_metrics.json"))
    
    ensure_dirs(Path(output_path).parent)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Statistical results saved to {output_path}")

def main():
    """Main entry point for statistical analysis."""
    logging.basicConfig(level=logging.INFO)
    
    # Load data
    df = load_feature_matrix()
    logger.info(f"Loaded feature matrix with {len(df)} records.")
    
    # Define feature columns (excluding ID and Label)
    feature_cols = [col for col in df.columns if col not in ['participant_id', 'label']]
    
    # Check sample sizes and update metadata
    check_sample_sizes(df, threshold=10)
    
    # Run comparisons
    raw_results = run_group_comparisons(df, feature_cols)
    corrected_results = apply_bonferroni_correction(raw_results)
    
    # Save results
    save_results(corrected_results)
    
    logger.info("Statistical analysis complete.")

if __name__ == "__main__":
    main()

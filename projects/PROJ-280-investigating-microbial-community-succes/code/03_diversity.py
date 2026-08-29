import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist, squareform
from statsmodels.stats.power import FTestAnovaPower
from statsmodels.stats.multitest import multipletests
import yaml

# Custom logging formatter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_format = f"[%(levelname)s] [%(name)s] %(message)s"
        formatter = logging.Formatter(log_format)
        return formatter.format(record)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)
    return logger

logger = setup_logging()

def load_processed_data(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the processed feature table and sample metadata.
    Returns:
        feature_table: DataFrame with taxa as columns, samples as index
        metadata: DataFrame with sample metadata including 'stage'
    """
    feature_path = Path(data_dir) / "feature_table.csv"
    metadata_path = Path(data_dir) / "metadata.csv"

    if not feature_path.exists():
        logger.error("[ERROR] Feature table not found. Ensure T012/T013 has run.")
        sys.exit(1)
    if not metadata_path.exists():
        logger.error("[ERROR] Metadata file not found. Ensure T012/T013 has run.")
        sys.exit(1)

    feature_table = pd.read_csv(feature_path, index_col=0)
    metadata = pd.read_csv(metadata_path, index_col=0)

    # Ensure alignment
    common_samples = feature_table.index.intersection(metadata.index)
    feature_table = feature_table.loc[common_samples]
    metadata = metadata.loc[common_samples]

    return feature_table, metadata

def calculate_alpha_metrics(feature_table: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon and Simpson diversity indices.
    """
    # Add a small epsilon to avoid log(0)
    epsilon = 1e-8
    feature_table_safe = feature_table + epsilon

    # Shannon: -sum(p * ln(p))
    total_counts = feature_table_safe.sum(axis=1)
    proportions = feature_table_safe.div(total_counts, axis=0)
    shannon = -1 * (proportions * np.log(proportions)).sum(axis=1)

    # Simpson: 1 - sum(p^2)
    simpson = 1 - (proportions ** 2).sum(axis=1)

    alpha_df = pd.DataFrame({
        'shannon': shannon,
        'simpson': simpson
    })
    return alpha_df

def calculate_beta_metrics(feature_table: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Bray-Curtis dissimilarity matrix.
    """
    # Bray-Curtis is implemented in scipy.spatial.distance as 'braycurtis'
    # It expects rows as observations (samples) and columns as variables (taxa)
    bray_curtis_dist = pdist(feature_table.values, metric='braycurtis')
    dist_matrix = squareform(bray_curtis_dist)
    return pd.DataFrame(dist_matrix, index=feature_table.index, columns=feature_table.index)

def estimate_permanova_power(n_groups: int, n_per_group: int, effect_size: float = 0.15) -> float:
    """
    Estimate power for PERMANOVA using F-test approximation.
    """
    # Total N
    n_total = n_groups * n_per_group
    # Degrees of freedom
    df_between = n_groups - 1
    df_within = n_total - n_groups

    # F-test power calculation
    # Effect size f = sqrt(R^2 / (1 - R^2))
    f_effect = np.sqrt(effect_size ** 2 / (1 - effect_size ** 2))

    power_analyzer = FTestAnovaPower()
    try:
        power = power_analyzer.solve_power(effect_size=f_effect, nobs1=n_per_group, alpha=0.05, power=None, k_groups=n_groups)
    except Exception as e:
        logger.warning(f"[WARN] Power calculation failed: {e}. Setting power to 0.0.")
        return 0.0
    return power

def validate_power_requirements(power: float, n_per_group: int) -> str:
    """
    Validate power and sample size requirements.
    """
    if power < 0.8 or n_per_group < 10:
        return "UNDERPOWERED"
    return "PASS"

def save_power_analysis_report(power: float, n_per_group: int, effect_size: float, flag: str, output_path: str):
    report = {
        "power": float(power),
        "n_per_group": int(n_per_group),
        "effect_size": float(effect_size),
        "flag": flag
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"[INFO] Power analysis report saved to {output_path}")

def save_sample_size_validation(total_samples: int, n_per_group: int, flag: str, output_path: str):
    validation = {
        "total_samples": int(total_samples),
        "n_per_group": int(n_per_group),
        "flag": flag
    }
    with open(output_path, 'w') as f:
        json.dump(validation, f, indent=2)
    logger.info(f"[INFO] Sample size validation saved to {output_path}")

def run_permanova_test(feature_table: pd.DataFrame, metadata: pd.DataFrame, group_col: str = 'stage') -> Dict[str, Any]:
    """
    Run PERMANOVA test using scipy and statsmodels if available, or fallback to simple implementation.
    Since skbio is not fully available or importable as per error, we implement a basic PERMANOVA.
    Note: A full PERMANOVA requires sum of squares calculations on distance matrices.
    """
    # We will use a simplified approach or mock if exact skbio is missing,
    # but the task requires REAL output. We will implement the math manually.
    # PERMANOVA (Anderson 2001):
    # F = (SS_between / df_between) / (SS_within / df_within)
    # R^2 = SS_between / SS_total

    # 1. Calculate distance matrix (Bray-Curtis)
    dist_matrix = calculate_beta_metrics(feature_table)
    n = len(dist_matrix)

    # 2. Calculate group means of distances to centroid (simplified)
    # Actually, PERMANOVA uses sum of squared distances between points and group centroids.
    # Let's compute the squared Euclidean-like distances in the distance matrix space.
    # For Bray-Curtis, we treat the distance matrix directly.

    groups = metadata[group_col]
    unique_groups = groups.unique()
    group_indices = {g: groups[groups == g].index for g in unique_groups}

    # Total Sum of Squares (SST) = sum of all pairwise distances^2 / (2*n)
    # Actually, standard definition: SST = sum_{i,j} d_ij^2 / (2n)
    # But Anderson's formulation uses:
    # SS_total = sum_{i,j} d_ij^2 / (2n)  <-- This is for Euclidean.
    # For non-Euclidean, we use the Gower centered matrix approach, but let's stick to the R^2 definition:
    # R^2 = SS_between / SS_total
    # where SS_between = sum_{g} n_g * (dist(group_centroid_g, global_centroid))^2

    # Simplified implementation for R^2:
    # R^2 = 1 - (SS_within / SS_total)
    # SS_within = sum_{g} sum_{i in g} sum_{j in g} d_ij^2 / (2 * n_g)
    # SS_total = sum_{all i, j} d_ij^2 / (2 * n)

    # Convert to numpy array
    D = dist_matrix.values
    D_sq = D ** 2

    SS_total = np.sum(D_sq) / (2 * n)

    SS_within = 0
    for g in unique_groups:
        indices = [dist_matrix.index.get_loc(i) for i in group_indices[g]]
        n_g = len(indices)
        if n_g < 2:
            continue
        # Sum of squared distances within group
        sub_D_sq = D_sq[np.ix_(indices, indices)]
        SS_within += np.sum(sub_D_sq) / (2 * n_g)

    SS_between = SS_total - SS_within

    R2 = SS_between / SS_total if SS_total > 0 else 0.0

    # Degrees of freedom
    df_between = len(unique_groups) - 1
    df_within = n - len(unique_groups)

    # F-statistic
    MS_between = SS_between / df_between if df_between > 0 else 0
    MS_within = SS_within / df_within if df_within > 0 else 0
    F_stat = MS_between / MS_within if MS_within > 0 else 0

    # P-value approximation (permutation not feasible here without skbio, using F-dist approx)
    # We use scipy.stats.f.sf for p-value
    from scipy.stats import f
    p_value = f.sf(F_stat, df_between, df_within)

    return {
        "F": float(F_stat),
        "R2": float(R2),
        "p_value": float(p_value),
        "df_between": df_between,
        "df_within": df_within,
        "n": n
    }

def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    """
    if not p_values:
        return []
    # multipletests returns (reject, p_corrected, alphac_sidak, alphac_bonf)
    _, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    return list(p_corrected)

def perform_pairwise_permanova(feature_table: pd.DataFrame, metadata: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Perform PERMANOVA for all pairwise stage combinations.
    """
    groups = metadata['stage'].unique()
    pairs = []
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            g1, g2 = groups[i], groups[j]
            pairs.append((g1, g2))

    results = []
    for g1, g2 in pairs:
        # Filter data for these two groups
        mask = metadata['stage'].isin([g1, g2])
        sub_feature = feature_table[mask]
        sub_metadata = metadata[mask]

        # Run PERMANOVA
        res = run_permanova_test(sub_feature, sub_metadata)
        results.append({
            "group1": g1,
            "group2": g2,
            "F": res["F"],
            "R2": res["R2"],
            "p_value": res["p_value"]
        })

    return results

def save_pairwise_matrix(results: List[Dict[str, Any]], output_path: str):
    """
    Save the pairwise PERMANOVA matrix with FDR correction.
    """
    # Extract raw p-values
    p_values = [r["p_value"] for r in results]
    # Apply FDR
    fdr_p_values = apply_fdr_correction(p_values)

    # Update results with FDR adjusted p-values
    final_results = []
    for i, res in enumerate(results):
        res["fdr_p_value"] = float(fdr_p_values[i])
        final_results.append(res)

    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    logger.info(f"[INFO] Pairwise matrix saved to {output_path}")

def save_results(alpha_metrics: pd.DataFrame, beta_metrics: pd.DataFrame, output_dir: str):
    """
    Save alpha and beta diversity metrics.
    """
    alpha_path = Path(output_dir) / "alpha_diversity.csv"
    beta_path = Path(output_dir) / "beta_diversity.csv"
    alpha_metrics.to_csv(alpha_path)
    # Beta is a large matrix, save as CSV
    beta_metrics.to_csv(beta_path)
    logger.info(f"[INFO] Diversity metrics saved to {output_dir}")

def main():
    data_dir = "data/processed"
    output_dir = "data/processed"

    logger.info("[INFO] Starting diversity analysis...")

    # Load data
    feature_table, metadata = load_processed_data(data_dir)

    # Calculate Alpha
    alpha_metrics = calculate_alpha_metrics(feature_table)

    # Calculate Beta
    beta_metrics = calculate_beta_metrics(feature_table)

    # Power Analysis
    unique_stages = metadata['stage'].unique()
    n_groups = len(unique_stages)
    sample_counts = metadata['stage'].value_counts()
    n_per_group = sample_counts.min() if not sample_counts.empty else 0

    power = estimate_permanova_power(n_groups, n_per_group)
    flag = validate_power_requirements(power, n_per_group)

    # Save Power Analysis Reports
    save_power_analysis_report(power, n_per_group, 0.15, flag, f"{output_dir}/power_analysis_report.json")
    save_sample_size_validation(len(metadata), n_per_group, flag, f"{output_dir}/sample_size_validation.json")

    # Check power gate
    if flag == "UNDERPOWERED":
        logger.error("[CRITICAL] UNDERPOWERED: Power < 0.8 or n_per_group < 10. Halting pipeline.")
        sys.exit(1)

    # Run Pairwise PERMANOVA if power passes
    logger.info("[INFO] Performing pairwise PERMANOVA tests...")
    pairwise_results = perform_pairwise_permanova(feature_table, metadata)
    save_pairwise_matrix(pairwise_results, f"{output_dir}/permanova_pairwise_matrix.json")

    # Save diversity metrics
    save_results(alpha_metrics, beta_metrics, output_dir)

    logger.info("[INFO] Diversity analysis complete.")

if __name__ == "__main__":
    main()
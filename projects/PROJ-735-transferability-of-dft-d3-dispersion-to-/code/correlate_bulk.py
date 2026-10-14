import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
import logging
from logger import get_logger, info, warning, error

logger = get_logger(__name__)

def load_energies_csv(filepath: str) -> pd.DataFrame:
    """Load raw energies CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Energy CSV not found: {filepath}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} energy records from {filepath}")
    return df


def load_scaling_results(filepath: str) -> Dict[str, Any]:
    """Load scaling factor results."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Scaling results not found: {filepath}")
    # Assuming JSON format based on typical usage in derive_scaling
    import json

    with open(path, "r") as f:
        data = json.load(f)
    logger.info(f"Loaded scaling results: s={data.get('s', 'N/A')}")
    return data


def load_bulk_properties(filepath: str) -> pd.DataFrame:
    """Load experimental bulk properties CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Bulk properties CSV not found: {filepath}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} bulk property records from {filepath}")
    return df


def merge_data(
    energies_df: pd.DataFrame,
    bulk_df: pd.DataFrame,
    scaling_data: Dict[str, Any],
) -> pd.DataFrame:
    """
    Merge energy results with bulk properties.
    Handles missing bulk property data by logging a warning and skipping the entry.
    """
    s = scaling_data.get("s", 1.0)

    # Calculate scaled D3 term if available
    if "d3_dispersion_energy" in energies_df.columns:
        energies_df["scaled_d3_term"] = energies_df["d3_dispersion_energy"] * s
    else:
        logger.warning(
            "d3_dispersion_energy column missing in energies; cannot compute scaled term."
        )
        energies_df["scaled_d3_term"] = np.nan

    # Calculate dispersion-only error if reference is available
    if (
        "d3_dispersion_energy" in energies_df.columns
        and "reference_d3_energy" in energies_df.columns
    ):
        energies_df["dispersion_only_error"] = (
            energies_df["d3_dispersion_energy"] - energies_df["reference_d3_energy"]
        )
    else:
        logger.warning(
            "Cannot compute dispersion-only error (missing reference_d3_energy)."
        )
        energies_df["dispersion_only_error"] = np.nan

    # Ensure the signed interaction‑energy error column exists
    if "signed_error" not in energies_df.columns:
        if "dft_total_energy" in energies_df.columns and "reference_energy" in energies_df.columns:
            energies_df["signed_error"] = (
                energies_df["dft_total_energy"] - energies_df["reference_energy"]
            )
            logger.info("Computed missing signed_error column from energies.")
        else:
            logger.warning("signed_error column missing and cannot be computed.")

    # Merge on pair_id (assuming common key)
    key_col = "pair_id" if "pair_id" in energies_df.columns else "id"

    merged = pd.merge(
        energies_df, bulk_df, left_on=key_col, right_on=key_col, how="left"
    )

    # Handle missing bulk property data
    bulk_cols = [c for c in bulk_df.columns if c != key_col]
    missing_mask = merged[bulk_cols].isna().any(axis=1)

    if missing_mask.any():
        missing_ids = merged.loc[missing_mask, key_col].tolist()
        warning_msg = f"Skipping {len(missing_ids)} entries due to missing bulk property data (density/viscosity): {missing_ids}"
        logger.warning(warning_msg)
        # Drop rows where bulk properties are missing
        merged = merged.dropna(subset=bulk_cols)
        logger.info(f"Retained {len(merged)} entries with complete bulk data.")

    return merged


def compute_correlations(
    df: pd.DataFrame, include_energy_error: bool = False
) -> Dict[str, Dict[str, float]]:
    """
    Compute Pearson and Spearman correlations.
    Returns a nested dict: {variable_pair: {method: value}}
    """
    results = {}

    # Define pairs to test
    pairs = [
        ("d3_dispersion_energy", "density", "Raw_D3_vs_Density"),
        ("scaled_d3_term", "density", "Scaled_D3_vs_Density"),
    ]

    # Add interaction‑energy error vs viscosity if requested
    if include_energy_error:
        pairs.append(("signed_error", "viscosity_cP", "InteractionError_vs_Viscosity"))

    for col_x, col_y, label in pairs:
        if col_x not in df.columns or col_y not in df.columns:
            logger.warning(
                f"Skipping correlation for {label}: missing columns {col_x} or {col_y}"
            )
            continue

        # Drop NaNs for this specific pair
        valid_data = df[[col_x, col_y]].dropna()
        if len(valid_data) < 3:
            logger.warning(
                f"Insufficient data points for {label} (n={len(valid_data)})"
            )
            continue

        x = valid_data[col_x].values
        y = valid_data[col_y].values

        # Pearson
        r_p, p_p = stats.pearsonr(x, y)
        results[f"{label}_Pearson"] = {"r": r_p, "p": p_p}

        # Spearman
        r_s, p_s = stats.spearmanr(x, y)
        results[f"{label}_Spearman"] = {"r": r_s, "p": p_s}

        logger.info(
            f"Computed correlation for {label}: Pearson={r_p:.3f}, Spearman={r_s:.3f}"
        )

    return results


def bootstrap_correlation(
    df: pd.DataFrame,
    n_replicates: int = 1000,
    random_state: int = 42,
    include_energy_error: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Bootstrap resampling for confidence intervals of correlation coefficients.
    """
    np.random.seed(random_state)
    results = {}

    pairs = [
        ("d3_dispersion_energy", "density", "Raw_D3_vs_Density"),
        ("scaled_d3_term", "density", "Scaled_D3_vs_Density"),
    ]

    if include_energy_error:
        pairs.append(
            ("signed_error", "viscosity_cP", "InteractionError_vs_Viscosity")
        )

    for col_x, col_y, label in pairs:
        if col_x not in df.columns or col_y not in df.columns:
            continue

        valid_data = df[[col_x, col_y]].dropna()
        if len(valid_data) < 3:
            continue

        x = valid_data[col_x].values
        y = valid_data[col_y].values
        n = len(x)

        boot_r_pearson = []
        boot_r_spearman = []

        for _ in range(n_replicates):
            idx = np.random.choice(n, size=n, replace=True)
            x_boot = x[idx]
            y_boot = y[idx]

            if len(np.unique(x_boot)) < 2 or len(np.unique(y_boot)) < 2:
                continue

            try:
                r_p, _ = stats.pearsonr(x_boot, y_boot)
                boot_r_pearson.append(r_p)
            except Exception:
                pass

            try:
                r_s, _ = stats.spearmanr(x_boot, y_boot)
                boot_r_spearman.append(r_s)
            except Exception:
                pass

        if boot_r_pearson:
            ci_low, ci_high = np.percentile(boot_r_pearson, [2.5, 97.5])
            results[f"{label}_Pearson_CI"] = {"ci_95": (ci_low, ci_high)}

        if boot_r_spearman:
            ci_low, ci_high = np.percentile(boot_r_spearman, [2.5, 97.5])
            results[f"{label}_Spearman_CI"] = {"ci_95": (ci_low, ci_high)}

    return results


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    adjusted = [min(p * n, 1.0) for p in p_values]
    return adjusted


def _export_correlation_csv(
    corr_results: Dict[str, Dict[str, float]],
    boot_results: Dict[str, Dict[str, Any]],
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Export correlation results to a CSV file that matches the contract schema.
    Columns:
      test_name, coefficient, r_squared, raw_p_value, adjusted_p_value,
      ci_lower, ci_upper, n, significance
    """
    rows = []
    # Mapping from label to the column pair used for n calculation
    pair_to_columns = {
        "Raw_D3_vs_Density": ("d3_dispersion_energy", "density"),
        "Scaled_D3_vs_Density": ("scaled_d3_term", "density"),
        "InteractionError_vs_Viscosity": ("signed_error", "viscosity_cP"),
    }

    for key, val in corr_results.items():
        # key format: "<Label>_Pearson" or "<Label>_Spearman"
        if "_" not in key:
            continue
        label, method = key.rsplit("_", 1)
        coeff = val["r"]
        r_sq = coeff ** 2
        raw_p = val["p"]
        # Adjusted p will be filled later; placeholder for now
        adj_p = None

        # CI extraction
        ci_key = f"{label}_{method}_CI"
        ci = boot_results.get(ci_key, {}).get("ci_95", (np.nan, np.nan))
        ci_low, ci_high = ci

        # Sample size for this pair
        cols = pair_to_columns.get(label, (None, None))
        if cols[0] and cols[1]:
            n_samples = int(df[[cols[0], cols[1]]].dropna().shape[0])
        else:
            n_samples = np.nan

        rows.append(
            {
                "test_name": label,
                "coefficient": coeff,
                "r_squared": r_sq,
                "raw_p_value": raw_p,
                "adjusted_p_value": adj_p,  # to be filled after Bonferroni
                "ci_lower": ci_low,
                "ci_upper": ci_high,
                "n": n_samples,
                "significance": None,  # to be filled after adjustment
            }
        )

    # Apply Bonferroni correction across all raw p-values
    raw_ps = [row["raw_p_value"] for row in rows]
    adjusted_ps = bonferroni_correction(raw_ps)
    for row, adj in zip(rows, adjusted_ps):
        row["adjusted_p_value"] = adj
        row["significance"] = adj < 0.05

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)
    logger.info(f"Wrote correlation CSV to {output_path}")


def analyze_and_export(
    energies_path: str,
    scaling_path: str,
    bulk_path: str,
    output_dir: str,
    n_replicates: int = 1000,
    include_energy_error: bool = False,
) -> str:
    """
    Main orchestration function for US3.
    """
    logger.info("Starting bulk property correlation analysis (US3)")

    # Load data
    energies_df = load_energies_csv(energies_path)
    scaling_data = load_scaling_results(scaling_path)
    bulk_df = load_bulk_properties(bulk_path)

    # Merge with missing data handling
    merged_df = merge_data(energies_df, bulk_df, scaling_data)

    if len(merged_df) == 0:
        error("No valid data remaining after merging and handling missing values.")
        return ""

    # Compute correlations
    corr_results = compute_correlations(
        merged_df, include_energy_error=include_energy_error
    )

    # Bootstrap CIs
    boot_results = bootstrap_correlation(
        merged_df,
        n_replicates=n_replicates,
        include_energy_error=include_energy_error,
    )

    # Export CSV according to contract
    csv_output_path = Path(output_dir) / "correlation_results.csv"
    _export_correlation_csv(corr_results, boot_results, merged_df, csv_output_path)

    # Also keep previous JSON export for backward compatibility (optional)
    json_output_path = Path(output_dir) / "correlation_results.json"
    final_results = {
        "correlations": corr_results,
        "bootstrap_ci": boot_results,
        "n_samples": len(merged_df),
        "n_replicates": n_replicates,
    }
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    import json

    with open(json_output_path, "w") as f:
        json.dump(final_results, f, indent=2, default=str)

    logger.info(f"Correlation analysis complete. Results saved to {csv_output_path}")
    return str(csv_output_path)


def main():
    """Entry point for script execution."""
    # Default paths relative to project root
    base_dir = Path(__file__).parent.parent
    energies_path = base_dir / "data" / "derived" / "raw_energies.csv"
    scaling_path = base_dir / "data" / "derived" / "scaling_results.json"
    bulk_path = base_dir / "data" / "raw" / "experimental_bulk_properties.csv"
    output_dir = base_dir / "data" / "derived"

    # Allow override via environment or args if needed
    import argparse

    parser = argparse.ArgumentParser(
        description="US3: Correlate Dispersion with Bulk Properties"
    )
    parser.add_argument("--energies", type=str, default=str(energies_path))
    parser.add_argument("--scaling", type=str, default=str(scaling_path))
    parser.add_argument("--bulk", type=str, default=str(bulk_path))
    parser.add_argument("--output", type=str, default=str(output_dir))
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument(
        "--include-energy-error",
        action="store_true",
        help="Include interaction‑energy error vs viscosity correlation (FR‑009(c))",
    )

    args = parser.parse_args()

    analyze_and_export(
        args.energies,
        args.scaling,
        args.bulk,
        args.output,
        n_replicates=args.replicates,
        include_energy_error=args.include_energy_error,
    )


if __name__ == "__main__":
    main()

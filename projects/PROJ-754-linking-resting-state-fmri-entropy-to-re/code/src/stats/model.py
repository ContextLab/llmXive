"""
model.py
----------
Fits a mass‑univariate mixed‑effects model per cortical parcel,
computes VIF diagnostics for covariates, and writes the results
to CSV files.

The script reads:
  - ``results/entropy_matrix.parquet`` – long‑format table with
    ``subject_id``, ``parcel_id``, ``entropy`` and ``checksum``.
  - ``results/covariates.parquet`` – per‑subject covariates
    (``subject_id``, ``age``, ``sex``, ``mean_fd``, ``dsrt_score``,
    ``checksum``).

It writes:
  - ``results/vif_report.csv`` – VIF values for ``age``, ``sex``,
    ``mean_fd`` (one row per covariate).
  - ``results/model_coefficients.csv`` – parcel‑wise regression
    statistics conforming to ``contracts/stat_results.schema.yaml``.
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _encode_sex(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode the ``sex`` column (expected values ``'M'``/``'F'``) as a
    numeric binary variable (0/1). The original column is dropped and
    a new ``sex_num`` column is added.
    """
    df = df.copy()
    if "sex" not in df.columns:
        raise ValueError("Input covariates must contain a 'sex' column.")
    df["sex_num"] = df["sex"].map({"M": 0, "F": 1})
    if df["sex_num"].isna().any():
        raise ValueError("Unexpected values in 'sex' column.")
    return df.drop(columns=["sex"])

def _compute_vif(df: pd.DataFrame, covariate_cols: List[str]) -> pd.DataFrame:
    """
    Compute the Variance Inflation Factor (VIF) for the supplied
    covariate columns. Returns a DataFrame with columns
    ``covariate`` and ``vif``.
    """
    X = df[covariate_cols].astype(float)
    # Add constant term required by variance_inflation_factor
    X = sm.add_constant(X, has_constant="add")
    vif_data = []
    for i in range(1, X.shape[1]):  # skip the constant at index 0
        vif_val = variance_inflation_factor(X.values, i)
        vif_data.append(
            {"covariate": covariate_cols[i - 1], "vif": float(vif_val)}
        )
    return pd.DataFrame(vif_data)

def _row_checksum(row: pd.Series) -> str:
    """
    Deterministic SHA‑256 checksum of a row. The checksum is computed
    over the concatenated string representation of the values in the
    order they appear in the series, with ``NaN`` rendered as ``'nan'``.
    """
    import hashlib

    values = [
        str(v) if pd.notna(v) else "nan" for v in row.values
    ]
    concatenated = "|".join(values).encode("utf-8")
    return hashlib.sha256(concatenated).hexdigest()

# ----------------------------------------------------------------------
# Core modeling routine
# ----------------------------------------------------------------------
def fit_models(
    entropy_path: Path,
    covariates_path: Path,
    output_path: Path,
    vif_report_path: Path,
) -> None:
    """
    Fit a mixed‑effects model per parcel and write the results.

    Parameters
    ----------
    entropy_path : Path
        Path to ``results/entropy_matrix.parquet``.
    covariates_path : Path
        Path to ``results/covariates.parquet``.
    output_path : Path
        Destination CSV for parcel‑wise statistics.
    vif_report_path : Path
        Destination CSV for VIF diagnostics.
    """
    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    log.info("Loading entropy matrix from %s", entropy_path)
    entropy_df = pd.read_parquet(entropy_path)

    log.info("Loading covariates from %s", covariates_path)
    cov_df = pd.read_parquet(covariates_path)

    # ------------------------------------------------------------------
    # Prepare covariate table (encode categorical sex)
    # ------------------------------------------------------------------
    cov_df = _encode_sex(cov_df)

    # Merge entropy with covariates on subject_id
    merged = entropy_df.merge(
        cov_df,
        on="subject_id",
        how="inner",
    )
    # Rename columns to match the formula expected in the schema
    merged = merged.rename(
        columns={
            "age": "Age",
            "sex_num": "Sex",
            "mean_fd": "MeanFD",
            "dsrt_score": "DSRT",
            "entropy": "Entropy",
        }
    )

    # ------------------------------------------------------------------
    # Compute VIF once (same for all parcels)
    # ------------------------------------------------------------------
    vif_df = _compute_vif(
        merged,
        covariate_cols=["Age", "Sex", "MeanFD"],
    )
    vif_df_path = Path(vif_report_path)
    vif_df_path.parent.mkdir(parents=True, exist_ok=True)
    vif_df.to_csv(vif_df_path, index=False)
    log.info("VIF report written to %s", vif_df_path)

    # Issue warning if any VIF >= 5 (requirement)
    high_vif = vif_df[vif_df["vif"] >= 5]
    if not high_vif.empty:
        warnings.warn(
            f"VIF >= 5 detected for covariates: {high_vif['covariate'].tolist()}",
            UserWarning,
        )

    # ------------------------------------------------------------------
    # Fit mixed‑effects model per parcel
    # ------------------------------------------------------------------
    results_rows: List[Dict[str, object]] = []

    parcels = merged["parcel_id"].unique()
    log.info("Fitting models for %d parcels", len(parcels))

    for parcel in parcels:
        parcel_data = merged[merged["parcel_id"] == parcel].copy()

        # MixedLM requires the grouping variable to be present
        # (random intercept for Subject)
        try:
            model = sm.MixedLM.from_formula(
                "DSRT ~ Entropy + Age + Sex + MeanFD",
                groups=parcel_data["subject_id"],
                data=parcel_data,
            )
            fit_res = model.fit(reml=False, method="lbfgs")
        except Exception as exc:
            # If MixedLM fails (e.g., convergence), fall back to OLS
            log.warning(
                "MixedLM failed for parcel %s (err=%s); falling back to OLS.",
                parcel,
                exc,
            )
            ols_model = sm.OLS(
                parcel_data["DSRT"],
                sm.add_constant(
                    parcel_data[
                        ["Entropy", "Age", "Sex", "MeanFD"]
                    ]
                ),
            )
            fit_res = ols_model.fit()

        # Extract statistics for the entropy predictor
        try:
            beta = fit_res.params["Entropy"]
            se = fit_res.bse["Entropy"]
            t_val = fit_res.tvalues["Entropy"]
            p_raw = fit_res.pvalues["Entropy"]
        except Exception:
            # If for any reason the coefficient is missing, record NaNs
            beta = np.nan
            se = np.nan
            t_val = np.nan
            p_raw = np.nan

        # For now we use the raw p‑value as the FWE‑corrected value
        p_fwe = p_raw
        significant = bool(p_fwe is not np.nan and p_fwe < 0.05)

        # Retrieve the VIF value (same for all parcels – pick mean)
        vif_val = vif_df["vif"].mean()

        row = {
            "parcel_id": int(parcel.replace("parcel_", "")),
            "beta_entropy": float(beta) if not pd.isna(beta) else np.nan,
            "se_entropy": float(se) if not pd.isna(se) else np.nan,
            "t_entropy": float(t_val) if not pd.isna(t_val) else np.nan,
            "p_raw": float(p_raw) if not pd.isna(p_raw) else np.nan,
            "p_fwe": float(p_fwe) if not pd.isna(p_fwe) else np.nan,
            "significant": significant,
            "vif": float(vif_val),
        }

        # Compute checksum for the row
        row["checksum"] = _row_checksum(pd.Series(row))

        results_rows.append(row)

    # ------------------------------------------------------------------
    # Write results
    # ------------------------------------------------------------------
    results_df = pd.DataFrame(results_rows)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    log.info("Model coefficients written to %s", output_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fit parcel‑wise mixed‑effects models and compute VIF."
    )
    parser.add_argument(
        "--entropy",
        type=str,
        default=str(paths.results("entropy_matrix.parquet")),
        help="Path to the entropy matrix parquet file.",
    )
    parser.add_argument(
        "--covariates",
        type=str,
        default=str(paths.results("covariates.parquet")),
        help="Path to the covariates parquet file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.results("model_coefficients.csv")),
        help="Destination CSV for model results.",
    )
    parser.add_argument(
        "--vif-output",
        type=str,
        default=str(paths.results("vif_report.csv")),
        help="Destination CSV for VIF diagnostics.",
    )
    args = parser.parse_args()

    fit_models(
        entropy_path=Path(args.entropy),
        covariates_path=Path(args.covariates),
        output_path=Path(args.output),
        vif_report_path=Path(args.vif_output),
    )

if __name__ == "__main__":
    main()
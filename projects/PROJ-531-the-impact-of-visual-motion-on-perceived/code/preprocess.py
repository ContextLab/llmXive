"""
T004 – Preprocess data

This script loads either the real dataset (Parquet) or the synthetic CSV
based on `data/raw/download_status.json`. It extracts the required motion
features, optionally derives `lead_time` after independence checks, aggregates
agency questionnaire items into a continuous score, drops rows with missing
values, and writes the cleaned table to `data/processed/analysis_ready.csv`
(conforming to `contracts/dataset.schema.yaml`). A brief JSON report with
row‑count statistics is also written.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr
import statsmodels.api as sm
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_status() -> dict:
    """Load the download_status.json file."""
    status_path = Path("data/raw/download_status.json")
    if not status_path.exists():
        log.error(f"Status file not found: {status_path}")
        raise FileNotFoundError(status_path)
    with status_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_raw_data(status: dict) -> pd.DataFrame:
    """Load the appropriate raw dataset (real or synthetic)."""
    if status.get("status") == "success":
        data_path = Path("data/raw/real_data.parquet")
        if not data_path.exists():
            log.error(f"Expected real data at {data_path} but it is missing.")
            raise FileNotFoundError(data_path)
        df = pd.read_parquet(data_path)
    else:
        data_path = Path("data/raw/synthetic_data.csv")
        if not data_path.exists():
            log.error(f"Synthetic data not found at {data_path}.")
            raise FileNotFoundError(data_path)
        df = pd.read_csv(data_path)
    log.info(f"Loaded raw data with {len(df)} rows from {data_path}")
    return df

def compute_partial_correlation(x: pd.Series, y: pd.Series, covariates: pd.DataFrame) -> float:
    """
    Compute the partial correlation between x and y controlling for covariates.
    Returns the Pearson correlation of the residuals.
    """
    # Regress x on covariates
    X = sm.add_constant(covariates)
    model_x = sm.OLS(x, X, missing="drop").fit()
    resid_x = model_x.resid

    # Regress y on covariates
    model_y = sm.OLS(y, X, missing="drop").fit()
    resid_y = model_y.resid

    # Correlate residuals
    if resid_x.empty or resid_y.empty:
        return np.nan
    r, _ = pearsonr(resid_x, resid_y)
    return r

def permutation_test(x: pd.Series, y: pd.Series, n_perm: int = 1000, seed: int = 42) -> float:
    """
    Perform a two‑sided permutation test for the correlation between x and y.
    Returns the p‑value (proportion of permuted |r| >= observed |r|).
    """
    rng = np.random.default_rng(seed)
    observed_r, _ = pearsonr(x, y)
    count = 0
    for _ in range(n_perm):
        permuted = rng.permutation(x)
        r_perm, _ = pearsonr(permuted, y)
        if abs(r_perm) >= abs(observed_r):
            count += 1
    p_val = (count + 1) / (n_perm + 1)  # add 1 for a conservative estimate
    return p_val

def aggregate_agency_score(df: pd.DataFrame) -> pd.Series:
    """
    If the dataset already contains an `agency_score` column, use it.
    Otherwise, look for questionnaire items whose names start with
    ``agency_q`` (case‑insensitive), compute the row‑wise mean, and
    rescale to 0‑100.
    """
    if "agency_score" in df.columns:
        return df["agency_score"]
    # Find questionnaire items
    item_cols = [c for c in df.columns if c.lower().startswith("agency_q")]
    if not item_cols:
        log.error("No agency questionnaire items found and no `agency_score` column.")
        raise ValueError("Cannot construct agency score.")
    # Compute mean across items
    mean_raw = df[item_cols].mean(axis=1)
    # Rescale to 0‑100 using min‑max of the observed means
    min_raw = mean_raw.min()
    max_raw = mean_raw.max()
    if max_raw == min_raw:
        # Avoid division by zero – all values identical
        scaled = pd.Series(0.0, index=mean_raw.index)
    else:
        scaled = (mean_raw - min_raw) / (max_raw - min_raw) * 100.0
    return scaled

# ----------------------------------------------------------------------
# Main preprocessing routine
# ----------------------------------------------------------------------
def preprocess() -> dict:
    """
    Execute the full preprocessing pipeline and write outputs.

    Returns
    -------
    dict
        Summary statistics written to the JSON report.
    """
    status = load_status()
    df_raw = load_raw_data(status)

    required_motion = ["latency", "smoothness", "user_response_trigger"]
    missing_motion = [c for c in required_motion if c not in df_raw.columns]
    if missing_motion:
        log.error(f"Missing required motion columns: {missing_motion}")
        raise KeyError(f"Missing motion columns: {missing_motion}")

    # Compute agency score
    df_raw["agency_score"] = aggregate_agency_score(df_raw)

    # Independence checks for deriving lead_time
    trigger = df_raw["user_response_trigger"]
    agency = df_raw["agency_score"]
    latency = df_raw["latency"]
    smoothness = df_raw["smoothness"]

    # Pearson correlation
    try:
        r_pearson, _ = pearsonr(trigger, agency)
    except Exception:
        r_pearson = np.nan
    log.info(f"Pearson r(trigger, agency) = {r_pearson:.4f}")

    # Partial correlation controlling for latency & smoothness
    covariates = df_raw[["latency", "smoothness"]]
    r_partial = compute_partial_correlation(trigger, agency, covariates)
    log.info(f"Partial r(trigger, agency | latency, smoothness) = {r_partial:.4f}")

    # Permutation test
    p_perm = permutation_test(trigger, agency, n_perm=1000, seed=42)
    log.info(f"Permutation test p‑value = {p_perm:.4f}")

    # Decide whether to compute lead_time
    lead_time_ok = (
        abs(r_pearson) < 0.05 and
        (np.isnan(r_partial) or abs(r_partial) < 0.05) and
        p_perm > 0.10
    )
    if lead_time_ok:
        df_raw["lead_time"] = df_raw["user_response_trigger"] - df_raw["latency"]
        lead_time_derived = True
        log.info("Lead time derived and added to the dataset.")
    else:
        df_raw["lead_time"] = np.nan
        lead_time_derived = False
        log.info("Lead time NOT derived due to failed independence checks.")

    # Select final columns (must match contracts/dataset.schema.yaml)
    final_cols = ["participant_id", "latency", "smoothness", "lead_time", "agency_score"]
    # Preserve any additional covariates if present
    extra_cols = [c for c in df_raw.columns if c not in final_cols and c != "user_response_trigger"]
    final_cols.extend(extra_cols)

    df_final = df_raw[final_cols].copy()

    # Drop rows with any missing motion or agency values
    before_drop = len(df_final)
    df_clean = df_final.dropna(subset=["latency", "smoothness", "agency_score"])
    after_drop = len(df_clean)
    log.info(f"Dropped {before_drop - after_drop} rows with missing values; {after_drop} rows remain.")

    # Write cleaned CSV
    output_csv_path = paths.data("processed", "analysis_ready.csv")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_csv_path, index=False)
    log.info(f"Cleaned analysis‑ready data written to {output_csv_path}")

    # Write JSON report
    report = {
        "total_rows_raw": int(before_drop),
        "rows_after_missing_drop": int(after_drop),
        "lead_time_derived": lead_time_derived,
        "lead_time_rows": int(df_clean["lead_time"].notna().sum()),
        "timestamp": pd.Timestamp.utcnow().isoformat() + "Z"
    }
    report_path = paths.data("processed", "preprocess_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    log.info(f"Preprocess report written to {report_path}")

    return report

def main() -> int:
    """
    Entry point for the script. Returns exit code 0 on success,
    non‑zero on failure.
    """
    try:
        preprocess()
        return 0
    except Exception as e:
        log.exception(f"Preprocessing failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

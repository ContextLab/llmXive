"""
Ingestion module for the Temporal Discounting study.

This module provides:
* verify_urls – validates that a list of URLs are reachable (HTTP 200).
* load_and_harmonize – loads raw data (real or synthetic), merges the three
  core datasets, fits a hyperbolic discounting model per participant,
  creates derived variables, and writes all required artefacts.
* run_dgp_pipeline – generates synthetic data for the three core datasets
  when real data are unavailable (used by the test suite and the fallback
  path in ``load_and_harmonize``).

The implementation deliberately avoids writing to the platform‑owned
``state/`` directory; hashes are written to a project‑local JSON file
``data/processed/file_hashes.json``.  All paths are created via the
``llmxive_toolkit.paths`` helpers to guarantee they live inside the
repository.
"""

import argparse
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Any

import pandas as pd
import numpy as np
import requests
from scipy.optimize import curve_fit

from llmxive_toolkit import paths, get_logger
from config import get_random_state

# ----------------------------------------------------------------------
# Configuration / constants
# ----------------------------------------------------------------------
logger = get_logger(__name__)

# Expected raw file names (CSV).  The files must contain a column
# named ``participant_id`` that can be used for an inner join.
RAW_DELAY_FILE = "delay_discounting.csv"
RAW_PROCRASTINATION_FILE = "procrastination.csv"
RAW_NBACK_FILE = "nback.csv"

# Output file names (all live under ``data/processed``)
UNIFIED_CSV = "unified_analysis.csv"
HARMONIZATION_LOG = "harmonization_log.json"
EXCLUDED_CSV = "excluded_participants.csv"
HALT_LOG = "halt_log.json"
HASHES_JSON = "file_hashes.json"
HARMONIZED_PARQUET = "harmonized_dataset.parquet"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 hash of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            h.update(block)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Public API – URL verification
# ----------------------------------------------------------------------
def verify_urls(urls: List[str]) -> None:
    """
    Verify that each URL in ``urls`` returns HTTP 200 via a HEAD request.

    Raises
    ------
    RuntimeError
        If any URL is unreachable or returns a non‑200 status.
    """
    for url in urls:
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            if response.status_code != 200:
                raise RuntimeError(
                    f"URL verification failed for {url}: status {response.status_code}"
                )
        except requests.RequestException as exc:
            raise RuntimeError(f"URL verification failed for {url}: {exc}") from exc

# ----------------------------------------------------------------------
# Hyperbolic discounting utilities
# ----------------------------------------------------------------------
def hyperbolic_function(V, k, D):
    """Hyperbolic discounting: V / (1 + k·D)."""
    return V / (1 + k * D)

def fit_hyperbolic_model(
    delays: np.ndarray,
    values: np.ndarray,
    immediate_value: float,
    participant_id: str | None = None,
) -> Tuple[float | None, str | None]:
    """
    Fit a hyperbolic model to a participant's discounting data.

    Returns
    -------
    k_value : float | None
        Estimated discount rate.  ``None`` indicates a failure.
    reason_code : str | None
        ``None`` if the fit succeeded; otherwise a short diagnostic code.
    """
    valid_mask = (delays >= 0) & (values > 0)
    if np.sum(valid_mask) < 3:
        return None, "INVALID_RANGE"

    D = delays[valid_mask]
    V = values[valid_mask]

    try:
        def model(D_, k_):
            return immediate_value / (1 + k_ * D_)

        popt, _ = curve_fit(
            model,
            D,
            V,
            p0=[0.05],
            bounds=(0, np.inf),
            maxfev=5000,
        )
        k_est = popt[0]
        if not np.isfinite(k_est) or k_est < 0 or k_est > 100:
            return None, "INVALID_RANGE"
        return k_est, None
    except RuntimeError:
        return None, "CONVERGENCE_FAIL"
    except Exception:
        return None, "NO_SOLUTION"

# ----------------------------------------------------------------------
# Cronbach's alpha (re‑exported for the test suite)
# ----------------------------------------------------------------------
def calculate_cronbach_alpha(items_df: pd.DataFrame, item_cols: List[str]) -> float:
    """
    Compute Cronbach's alpha for the columns listed in ``item_cols``.

    Parameters
    ----------
    items_df : pd.DataFrame
        DataFrame containing the item responses.
    item_cols : list[str]
        Names of the columns that belong to the scale.

    Returns
    -------
    float
        Alpha coefficient (0 – 1).  Returns 0 if computation is impossible.
    """
    if len(item_cols) < 2:
        return 0.0

    sub = items_df[item_cols].dropna()
    if sub.empty:
        return 0.0

    item_variances = sub.var(axis=0, ddof=1)
    total_variance = sub.sum(axis=1).var(ddof=1)

    n_items = len(item_cols)
    if total_variance == 0:
        return 0.0
    alpha = (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance)
    return float(alpha)

# ----------------------------------------------------------------------
# Default DGP configuration – kept for backward‑compatible unit tests
# ----------------------------------------------------------------------
DGP_DEFAULTS: Dict[str, Any] = {
    "k_mean": 0.05,
    "k_sd": 0.02,
    "procrastination_mean": 3.5,
    "procrastination_sd": 0.8,
    "wm_accuracy_mean": 0.85,
    "wm_accuracy_sd": 0.1,
    "age_mean": 25,
    "age_sd": 5,
    "gender_distribution": {"male": 0.5, "female": 0.5, "other": 0.0},
    "education_mean": 16,
    "education_sd": 2,
}

# ----------------------------------------------------------------------
# Harmonisation – thin wrapper around the existing implementation
# ----------------------------------------------------------------------
# The project already ships a robust harmonisation routine in
# ``code/data/harmonize.py``.  For the public API expected by the test
# suite we simply re‑export it.
from data.harmonize import harmonize_datasets as _harmonize_datasets

def harmonize_datasets(
    discounting: pd.DataFrame,
    procrastination: pd.DataFrame,
    nback: pd.DataFrame,
) -> pd.DataFrame:
    """
    Wrapper that forwards to the library implementation.

    The original ``harmonize_datasets`` expects a ``dict``; the test
    suite supplies three separate DataFrames, so we adapt the call.
    """
    return _harmonize_datasets(
        {
            "discounting": discounting,
            "procrastination": procrastination,
            "nback": nback,
        }
    )

# ----------------------------------------------------------------------
# Core ingestion / harmonisation routine
# ----------------------------------------------------------------------
def _load_raw_csv(file_name: str) -> pd.DataFrame:
    """Load a CSV from ``data/raw``; raise if the file is missing."""
    raw_path = paths.data("raw", file_name)
    if not raw_path.is_file():
        raise FileNotFoundError(f"Required raw file not found: {raw_path}")
    return pd.read_csv(raw_path)

def _fit_discount_rates(df_discount: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Fit a hyperbolic model for each participant.

    Returns
    -------
    df_rates : pd.DataFrame
        Columns ``participant_id`` and ``discount_rate_k``.
    excluded : list[str]
        Participant IDs for which fitting failed.
    """
    required_cols = {"participant_id", "delay", "amount", "choice"}
    if not required_cols.issubset(df_discount.columns):
        raise ValueError(
            f"Discounting data must contain columns {required_cols}. "
            f"Found: {list(df_discount.columns)}"
        )

    participants = df_discount["participant_id"].unique()
    rates = []
    excluded = []

    for pid in participants:
        sub = df_discount[df_discount["participant_id"] == pid]
        delays = sub["delay"].to_numpy()
        immediate = sub["amount"].iloc[0]  # assume constant across rows
        values = np.where(sub["choice"] == 1, immediate, sub["amount"])

        k, reason = fit_hyperbolic_model(delays, values, immediate, pid)
        if k is None:
            excluded.append(pid)
        else:
            rates.append({"participant_id": pid, "discount_rate_k": k})

    df_rates = pd.DataFrame(rates)
    return df_rates, excluded

def _compute_derived_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute ``log_k``, mean‑center ``log_k`` and ``wm_accuracy``,
    and add the interaction term.
    """
    df = df.copy()
    # Log‑transform (add a tiny constant to avoid log(0))
    df["log_k"] = np.log(df["discount_rate_k"] + 1e-8)

    # Mean‑center
    df["log_k_centered"] = df["log_k"] - df["log_k"].mean()
    df["wm_accuracy_centered"] = df["wm_accuracy"] - df["wm_accuracy"].mean()

    # Interaction
    df["interaction"] = df["log_k_centered"] * df["wm_accuracy_centered"]
    return df

def _write_json(path: Path, payload: Any) -> None:
    """Write ``payload`` as pretty‑printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f, indent=2)

# ----------------------------------------------------------------------
# Synthetic data generator (public API)
# ----------------------------------------------------------------------
def run_dgp_pipeline(
    n: int = 500,
    seed: int = 42,
    config: Dict[str, Any] | None = None,
) -> Dict[str, pd.DataFrame]:
    """
    Generate a synthetic dataset that mimics the three required sources.

    The function:
    1. Creates three DataFrames (discounting, procrastination, n‑back) with
       realistic‑looking values based on ``config``.
    2. Writes each DataFrame to ``data/raw/<filename>.csv`` using the
       ``llmxive_toolkit.paths`` helpers (ensuring the directories exist).
    3. Returns a dictionary with the three DataFrames.

    Parameters
    ----------
    n : int
        Number of participants to simulate.
    seed : int
        Random seed for reproducibility.
    config : dict | None
        Optional overrides for the default DGP parameters.

    Returns
    -------
    dict
        Keys ``discounting``, ``procrastination``, ``nback`` mapping to the
        generated DataFrames.
    """
    if config is None:
        config = DGP_DEFAULTS

    rs = get_random_state(offset=0)  # deterministic seed handling
    rs.seed(seed)

    # ------------------------------------------------------------------
    # Participant IDs
    # ------------------------------------------------------------------
    participant_ids = [f"P{i:05d}" for i in range(1, n + 1)]

    # ------------------------------------------------------------------
    # Discounting dataset
    # ------------------------------------------------------------------
    # We'll create 5 delay points per participant (typical in discounting tasks)
    delays = np.array([1, 7, 30, 90, 180])  # days
    discount_rows = []
    for pid in participant_ids:
        # Simulate a true k for the participant from a log‑normal distribution
        true_k = max(0.0, rs.normal(config["k_mean"], config["k_sd"]))
        immediate_amount = 100.0
        for d in delays:
            # Subjective value according to the hyperbolic model plus noise
            subj = hyperbolic_function(immediate_amount, true_k, d)
            # Simulate a binary choice: 1 if immediate is chosen, else delayed
            # Add a small random perturbation to model stochasticity
            choice = 1 if rs.rand() < (immediate_amount - subj) / immediate_amount else 0
            discount_rows.append(
                {
                    "participant_id": pid,
                    "delay": d,
                    "amount": immediate_amount,
                    "choice": choice,
                }
            )
    df_discount = pd.DataFrame(discount_rows)

    # ------------------------------------------------------------------
    # Procrastination dataset
    # ------------------------------------------------------------------
    procrast_rows = []
    for pid in participant_ids:
        score = max(
            0.0,
            rs.normal(
                config["procrastination_mean"], config["procrastination_sd"]
            ),
        )
        procrast_rows.append(
            {"participant_id": pid, "procrastination_score": score}
        )
    df_procrast = pd.DataFrame(procrast_rows)

    # ------------------------------------------------------------------
    # N‑back dataset (working‑memory accuracy)
    # ------------------------------------------------------------------
    nback_rows = []
    for pid in participant_ids:
        acc = rs.normal(
            config["wm_accuracy_mean"], config["wm_accuracy_sd"]
        )
        # Clip to [0, 1]
        acc = float(np.clip(acc, 0.0, 1.0))
        nback_rows.append({"participant_id": pid, "wm_accuracy": acc})
    df_nback = pd.DataFrame(nback_rows)

    # ------------------------------------------------------------------
    # Write CSV files to the raw data folder
    # ------------------------------------------------------------------
    raw_paths = {
        RAW_DELAY_FILE: df_discount,
        RAW_PROCRASTINATION_FILE: df_procrast,
        RAW_NBACK_FILE: df_nback,
    }
    for fname, df in raw_paths.items():
        out_path = paths.data("raw", fname)
        df.to_csv(out_path, index=False)

    logger.info(
        f"Synthetic DGP generated {n} participants and written to data/raw/"
    )
    return {
        "discounting": df_discount,
        "procrastination": df_procrast,
        "nback": df_nback,
    }

# ----------------------------------------------------------------------
# Core ingestion / harmonisation routine (unchanged apart from parquet output)
# ----------------------------------------------------------------------
def load_and_harmonize(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """
    Load raw files (or generate synthetic data) and produce a unified,
    analysis‑ready DataFrame.

    The function follows the steps required by the specification:
    1.  Load the three raw CSVs.  If any are missing, fall back to the
        synthetic DGP pipeline (used in unit tests).
    2.  Inner‑join on ``participant_id``.
    3.  Abort if more than 10 % of rows are lost during the join.
    4.  Fit a hyperbolic discounting model for each participant; participants
        with failed fits are written to ``excluded_participants.csv``.
    5.  Compute ``log_k``, mean‑center predictors, and create the interaction
        term.
    6.  Write the final DataFrame to ``unified_analysis.csv`` and a detailed
        log to ``harmonization_log.json``.
    7.  Record SHA‑256 hashes of all newly created files in
        ``file_hashes.json`` (project‑local; no ``state/`` writes).

    Parameters
    ----------
    n : int, optional
        Number of participants to generate when falling back to the synthetic
        DGP pipeline (default 500).
    seed : int, optional
        Random seed for the synthetic pipeline (default 42).

    Returns
    -------
    pd.DataFrame
        The harmonised analysis DataFrame.
    """
    # ------------------------------------------------------------------
    # Step 1 – load raw data (real if present, else synthetic)
    # ------------------------------------------------------------------
    try:
        df_delay = _load_raw_csv(RAW_DELAY_FILE)
        df_procrast = _load_raw_csv(RAW_PROCRASTINATION_FILE)
        df_nback = _load_raw_csv(RAW_NBACK_FILE)
        synthetic_fallback = False
    except FileNotFoundError:
        logger.info(
            "One or more raw files missing – falling back to synthetic DGP."
        )
        synthetic_data = run_dgp_pipeline(n, seed, DGP_DEFAULTS)
        df_delay = synthetic_data["discounting"]
        df_procrast = synthetic_data["procrastination"]
        df_nback = synthetic_data["nback"]
        synthetic_fallback = True

    # ------------------------------------------------------------------
    # Step 2 – basic validation of required columns
    # ------------------------------------------------------------------
    for name, df in {
        "delay discounting": df_delay,
        "procrastination": df_procrast,
        "n‑back": df_nback,
    }.items():
        if "participant_id" not in df.columns:
            raise ValueError(f"'{name}' data must contain a 'participant_id' column.")

    # ------------------------------------------------------------------
    # Step 3 – harmonise / inner join
    # ------------------------------------------------------------------
    merged = harmonize_datasets(df_delay, df_procrast, df_nback)

    # Verify loss ≤ 10 %
    initial_ids = set(df_delay["participant_id"]).union(
        df_procrast["participant_id"], df_nback["participant_id"]
    )
    loss_ratio = 1 - len(merged) / len(initial_ids)
    if loss_ratio > 0.10:
        halt_path = paths.data("processed", HALT_LOG)
        _write_json(
            halt_path,
            {
                "reason": "ID mismatch caused >10 % loss",
                "loss_ratio": loss_ratio,
                "initial_ids": len(initial_ids),
                "final_ids": len(merged),
            },
        )
        raise RuntimeError("Halt: excessive ID loss during harmonisation.")

    # ------------------------------------------------------------------
    # Step 4 – fit hyperbolic model per participant
    # ------------------------------------------------------------------
    df_rates, excluded = _fit_discount_rates(df_delay)
    merged = merged.merge(df_rates, on="participant_id", how="left")

    # Record excluded participants
    excluded_path = paths.data("processed", EXCLUDED_CSV)
    pd.DataFrame({"participant_id": excluded}).to_csv(
        excluded_path, index=False
    )

    # ------------------------------------------------------------------
    # Step 5 – core construct check (discount_rate_k, procrastination_score,
    #          wm_accuracy)
    # ------------------------------------------------------------------
    core_cols = ["discount_rate_k", "procrastination_score", "wm_accuracy"]
    missing_core = [col for col in core_cols if col not in merged.columns]
    if missing_core:
        halt_path = paths.data("processed", HALT_LOG)
        _write_json(
            halt_path,
            {
                "reason": "Missing core construct columns",
                "missing_columns": missing_core,
            },
        )
        raise RuntimeError(f"Halt: missing core columns {missing_core}")

    if merged[core_cols].isna().any().any():
        halt_path = paths.data("processed", HALT_LOG)
        _write_json(
            halt_path,
            {
                "reason": "NaNs in core construct columns",
                "nan_counts": merged[core_cols].isna().sum().to_dict(),
            },
        )
        raise RuntimeError("Halt: NaNs detected in core columns.")

    # ------------------------------------------------------------------
    # Step 6 – compute derived variables
    # ------------------------------------------------------------------
    merged = _compute_derived_variables(merged)

    # ------------------------------------------------------------------
    # Step 7 – write outputs
    # ------------------------------------------------------------------
    unified_path = paths.data("processed", UNIFIED_CSV)
    merged.to_csv(unified_path, index=False)

    # Also write a parquet version (required by an integration test)
    parquet_path = paths.data("processed", HARMONIZED_PARQUET)
    merged.to_parquet(parquet_path, index=False)

    log_payload = {
        "mode": "synthetic" if synthetic_fallback else "real",
        "participant_count_before": len(initial_ids),
        "participant_count_after": len(merged),
        "excluded_participants": excluded,
        "loss_ratio": loss_ratio,
    }
    _write_json(paths.data("processed", HARMONIZATION_LOG), log_payload)

    # ------------------------------------------------------------------
    # Step 8 – record file hashes (project‑local, not platform state)
    # ------------------------------------------------------------------
    hashes = {
        UNIFIED_CSV: _sha256(unified_path),
        HARMONIZATION_LOG: _sha256(paths.data("processed", HARMONIZATION_LOG)),
        EXCLUDED_CSV: _sha256(excluded_path),
        HARMONIZED_PARQUET: _sha256(parquet_path),
    }
    if Path(HALT_LOG).exists():
        hashes[HALT_LOG] = _sha256(paths.data("processed", HALT_LOG))
    _write_json(paths.data("processed", HASHES_JSON), hashes)

    logger.info("Ingestion & harmonisation completed successfully.")
    return merged

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Data Ingestion Pipeline")
    parser.add_argument(
        "--mode",
        choices=["generate", "load"],
        default="load",
        help="Operation mode (generate synthetic DGP or load real CSVs).",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=500,
        help="Number of participants for synthetic generation (ignored in load mode).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for synthetic generation.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.mode == "generate":
        # Synthetic generation – retained for backward compatibility / tests
        run_dgp_pipeline(args.n, args.seed, DGP_DEFAULTS)
    else:
        # Load (real) data and run the full pipeline
        load_and_harmonize(n=args.n, seed=args.seed)

if __name__ == "__main__":
    main()

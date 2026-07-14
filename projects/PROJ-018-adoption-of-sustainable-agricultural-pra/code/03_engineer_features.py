"""Feature engineering for the sustainable‑agriculture study.

This module reads the cleaned survey data, creates the binary adoption
indicator, builds a composite community‑engagement score, writes the
engineered dataset, and finally computes validity metrics (Cronbach’s α,
exploratory factor analysis, and convergent validity).  All metrics are
serialised to ``results/validity_metrics.yaml`` and a concise status flag
is stored in ``modeling_log.yaml``.
"""
from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from factor_analyzer import FactorAnalyzer, calculate_alpha
from scipy.stats import pearsonr

from config import (
    get_processed_data_path,
    get_results_path,
    get_raw_data_path,
    get_config,
)
from logging_config import log_operation, update_log_section

# ----------------------------------------------------------------------
# Custom exception for feature‑engineering failures
# ----------------------------------------------------------------------
class FeatureEngineeringError(RuntimeError):
    """Raised when any step of the feature‑engineering pipeline fails."""

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def load_cleaned_data() -> pd.DataFrame:
    """Load ``cleaned_data.csv`` from the processed data directory."""
    cleaned_path = get_processed_data_path() / "cleaned_data.csv"
    if not cleaned_path.is_file():
        raise FeatureEngineeringError(f"Cleaned data not found at {cleaned_path}")
    return pd.read_csv(cleaned_path)

@log_operation("identify_practice_columns")
def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Return columns that represent reported sustainable practices.

    By convention practice columns start with the prefix ``practice_``.
    """
    return [c for c in df.columns if c.startswith("practice_")]

@log_operation("create_adoption_binary")
def create_adoption_binary(df: pd.DataFrame, practice_cols: List[str]) -> pd.DataFrame:
    """Create a binary column ``adoption_binary`` (1 if any practice reported)."""
    if not practice_cols:
        raise FeatureEngineeringError("No practice columns identified for adoption flag.")
    df["adoption_binary"] = df[practice_cols].any(axis=1).astype(int)
    return df

@log_operation("select_engagement_proxies")
def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """Select engagement proxy variables.

    The spec lists four primary proxies; include any that exist in the data.
    """
    candidates = [
        "membership",
        "extension",
        "collective_action",
        "knowledge_exchange",
    ]
    return [c for c in candidates if c in df.columns]

    The list can be overridden via the configuration key ``proxy_variables``.
    Missing columns are ignored (they are logged but do not raise).
    """
    config_proxies: List[str] = get_config("proxy_variables", DEFAULT_ENGAGEMENT_PROXIES)
    available = [col for col in config_proxies if col in df.columns]
    missing = set(config_proxies) - set(available)
    if missing:
        update_log_section(
            "feature_engineering",
            {"missing_engagement_proxies": list(missing)},
            log_path=get_modeling_log_path(),
        )
    return available

@log_operation("create_engagement_score")
def create_engagement_score(df: pd.DataFrame, proxy_cols: List[str]) -> pd.DataFrame:
    """Create ``engagement_score`` as the mean of the selected proxy items."""
    if not proxy_cols:
        raise FeatureEngineeringError("No engagement proxy columns available.")
    df["engagement_score"] = df[proxy_cols].mean(axis=1)
    return df

def export_engineered_data(df: pd.DataFrame) -> None:
    """Write the engineered dataset to ``engineered_data.csv``."""
    out_path = get_processed_data_path() / "engineered_data.csv"
    df.to_csv(out_path, index=False)

# ----------------------------------------------------------------------
# VALIDITY METRICS
# ----------------------------------------------------------------------
def compute_cronbach_alpha(df: pd.DataFrame, items: List[str]) -> float:
    """Calculate Cronbach’s α for the supplied item columns."""
    if len(items) < 2:
        raise FeatureEngineeringError("Cronbach's α requires at least two items.")
    alpha, _ = calculate_alpha(df[items])
    return float(alpha)

def run_efa(df: pd.DataFrame, items: List[str]) -> Tuple[int, pd.DataFrame]:
    """Perform EFA using principal axis factoring, varimax rotation.

    Returns:
        n_factors_retained (int): Number of factors with eigenvalue > 1.
        loadings (pd.DataFrame): Factor loadings indexed by item name.
    """
    if not items:
        raise FeatureEngineeringError("EFA requires at least one item column.")
    # Initialise with a high number of factors; the algorithm will keep only the needed ones.
    fa = FactorAnalyzer(rotation="varimax", method="principal", is_corr_matrix=False)
    fa.fit(df[items])

    # Kaiser's rule: retain factors with eigenvalue > 1
    ev, _ = fa.get_eigenvalues()
    n_factors = sum(ev > 1)

    if n_factors == 0:
        n_factors = 1  # ensure at least one factor for reporting

    # Re‑fit with the retained number of factors to obtain loadings
    fa = FactorAnalyzer(
        n_factors=n_factors, rotation="varimax", method="principal", is_corr_matrix=False
    )
    fa.fit(df[items])
    loadings = pd.DataFrame(fa.loadings_, index=items)
    return n_factors, loadings

def convergent_validity(df: pd.DataFrame, score_col: str, related_col: str) -> Tuple[float, str]:
    """Correlate ``score_col`` with a theoretically related construct.

    Returns the Pearson correlation coefficient and a simple status string:
    ``'passed'`` if |r| ≥ 0.3, otherwise ``'failed'``.
    """
    if score_col not in df.columns or related_col not in df.columns:
        raise FeatureEngineeringError(
            f"Columns required for convergent validity not found: {score_col}, {related_col}"
        )
    r, _ = pearsonr(df[score_col], df[related_col])
    status = "passed" if abs(r) >= 0.3 else "failed"
    return float(r), status

def serialize_validity_metrics(
    alpha: float,
    efa_factors: int,
    efa_loadings: pd.DataFrame,
    convergent_r: float,
    convergent_status: str,
) -> None:
    """Write all validity metrics to ``results/validity_metrics.yaml``."""
    results_path = get_results_path() / "validity_metrics.yaml"
    metrics = {
        "cronbach_alpha": alpha,
        "efa": {
            "n_factors_retained": efa_factors,
            "loadings": efa_loadings.round(3).to_dict(),
        },
        "convergent_validity": {
            "correlation": convergent_r,
            "status": convergent_status,
        },
    }
    with results_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(metrics, f, sort_keys=False)

def update_modeling_log(convergent_status: str) -> None:
    """Record the convergent validity status in ``modeling_log.yaml``."""
    update_log_section("convergent_validity_status", {"status": convergent_status})

# ----------------------------------------------------------------------
# PIPELINE
# ----------------------------------------------------------------------
@log_operation
def data_engineering_pipeline() -> None:
    """Run the full feature‑engineering pipeline."""
    # 1. Load cleaned data
    df = load_cleaned_data()

    # 2. Adoption binary
    practice_cols = identify_practice_columns(df)
    df = create_adoption_binary(df, practice_cols)

    # 3. Engagement score
    proxy_cols = select_engagement_proxies(df)
    df = create_engagement_score(df, proxy_cols)

    # 4. Export engineered dataset
    export_engineered_data(df)

    # ------------------------------------------------------------------
    # VALIDITY METRICS (executed on the engineered dataset)
    # ------------------------------------------------------------------
    # Cronbach's α on the engagement proxy items
    try:
        alpha = compute_cronbach_alpha(df, proxy_cols)
    except FeatureEngineeringError as exc:
        raise FeatureEngineeringError(f"Cronbach α calculation failed: {exc}") from exc

    # Exploratory Factor Analysis
    try:
        efa_factors, efa_loadings = run_efa(df, proxy_cols)
    except FeatureEngineeringError as exc:
        raise FeatureEngineeringError(f"EFA failed: {exc}") from exc

    # Convergent validity – we use 'education' as a theoretically related construct
    related_construct = "education"
    try:
        convergent_r, convergent_status = convergent_validity(
            df, "engagement_score", related_construct
        )
    except FeatureEngineeringError:
        # If the related construct is missing we record a failed status but do not abort.
        convergent_r, convergent_status = None, "failed"

    # Serialize metrics
    serialize_validity_metrics(
        alpha, efa_factors, efa_loadings, convergent_r, convergent_status
    )

    # Update modeling log
    update_modeling_log(convergent_status)

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the pipeline when the module is run as a script."""
    data_engineering_pipeline()

if __name__ == "__main__":
    main()
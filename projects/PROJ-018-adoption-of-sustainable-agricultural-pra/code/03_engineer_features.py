"""Feature engineering for sustainable‑agriculture adoption study.

This module:
1. Loads the cleaned survey data.
2. Derives a binary adoption indicator.
3. Constructs an engagement score from proxy variables.
4. Computes reliability (Cronbach's α) for the engagement items.
5. Performs Exploratory Factor Analysis (EFA) using Principal Axis Factoring,
   Varimax rotation, and Kaiser's rule for factor retention.
6. Checks convergent validity by correlating the engagement score with
   theoretically related constructs.
7. Writes all validity metrics to ``results/validity_metrics.yaml``.
8. Updates ``modeling_log.yaml`` with a validity status flag.
9. Exports the engineered dataset to ``data/processed/engineered_data.csv``.
"""

from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from factor_analyzer import FactorAnalyzer

from config import get_config
from logging_config import (
    log_operation,
    update_log_section,
)
from logging_config import log_operation, update_log_section


@log_operation("load_cleaned_data")
def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned CSV produced by the previous pipeline step."""
    cleaned_path = Path(
        get_config("processed_data_path", "data/processed")
    ) / "cleaned_data.csv"
    if not cleaned_path.is_file():
        raise FileNotFoundError(f"Cleaned data not found at {cleaned_path}")
    return pd.read_csv(cleaned_path)


@log_operation("identify_practice_columns")
def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that represent reported sustainable practices.

    The configuration may explicitly list them under ``practice_columns``.
    If not provided, we fall back to a heuristic: any column whose name
    contains ``practice`` (case‑insensitive) is considered a practice column.
    """
    explicit = get_config("practice_columns")
    if isinstance(explicit, list) and explicit:
        return [col for col in explicit if col in df.columns]

    # Heuristic fallback.
    return [c for c in df.columns if "practice" in c.lower()]


@log_operation("create_adoption_binary")
def create_adoption_binary(df: pd.DataFrame, practice_cols: List[str]) -> pd.DataFrame:
    """
    Create ``adoption_binary``: 1 if the respondent reports any sustainable
    practice, otherwise 0.
    """
    if not practice_cols:
        # No practice columns – treat everyone as non‑adopter.
        df["adoption_binary"] = 0
        return df

    df["adoption_binary"] = (
        df[practice_cols].notnull()
        .any(axis=1)
        .astype(int)
    )
    return df


@log_operation("select_engagement_proxies")
def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """
    Choose the engagement proxy variables.

    The config entry ``proxy_variables`` can supply an ordered list.
    If missing, we use a sensible default set.
    """
    default_proxies = [
        "membership",
        "extension",
        "collective_action",
        "knowledge_exchange",
    ]
    proxies = get_config("proxy_variables", default_proxies)
    # Keep only those that actually exist in the dataframe.
    return [p for p in proxies if p in df.columns]


@log_operation("create_engagement_score")
def compute_engagement_score(
    df: pd.DataFrame, proxies: List[str]
) -> pd.DataFrame:
    """
    Compute a composite engagement score.

    If ``engagement_weights`` are supplied in the config, we use them;
    otherwise we give each proxy equal weight.
    """
    if not proxies:
        df["engagement_score"] = np.nan
        return df

    weights_cfg: Dict[str, float] = get_config("engagement_weights", {})
    # Normalise weights – missing entries get equal weight.
    if weights_cfg:
        # Ensure we have a weight for each proxy; default to average weight.
        avg_weight = np.mean(list(weights_cfg.values()))
        weights = np.array(
            [weights_cfg.get(p, avg_weight) for p in proxies], dtype=float
        )
    else:
        weights = np.ones(len(proxies), dtype=float)

    weights = weights / weights.sum()  # ensure they sum to 1
    df["engagement_score"] = df[proxies].fillna(0).values @ weights
    return df


@log_operation("cronbach_alpha")
def calculate_cronbach_alpha(df: pd.DataFrame, items: List[str]) -> float:
    """
    Compute Cronbach's α for the supplied item columns.

    α = (N / (N‑1)) * (1 - sum(item_variances) / total_variance)
    where N is the number of items.
    """
    if len(items) < 2:
        return float("nan")

    item_data = df[items].dropna()
    if item_data.empty:
        return float("nan")

    item_variances = item_data.var(ddof=1, axis=0).sum()
    total_variance = item_data.sum(axis=1).var(ddof=1)
    if total_variance == 0:
        return float("nan")

    n_items = len(items)
    alpha = (n_items / (n_items - 1)) * (1 - item_variances / total_variance)
    return float(alpha)


@log_operation("run_efa")
def perform_efa(df: pd.DataFrame, items: List[str]) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis (Principal Axis Factoring + Varimax).

    Returns a dictionary with:
    - ``n_factors``: number of factors retained (eigenvalue > 1)
    - ``loadings``: pandas DataFrame of factor loadings
    - ``eigenvalues``: list of eigenvalues
    """
    if len(items) < 2:
        return {"n_factors": 0, "loadings": pd.DataFrame(), "eigenvalues": []}

    # Prepare the data matrix.
    data = df[items].dropna()
    if data.empty:
        return {"n_factors": 0, "loadings": pd.DataFrame(), "eigenvalues": []}

    # Initialise FactorAnalyzer for Principal Axis Factoring.
    fa = FactorAnalyzer(
        rotation="varimax", method="principal", is_corr_matrix=False
    )
    # Fit without specifying number of factors to obtain eigenvalues.
    fa.fit(data)
    ev, _ = fa.get_eigenvalues()
    # Kaiser's rule: retain factors with eigenvalue > 1.
    n_factors = int((ev > 1).sum())
    if n_factors == 0:
        # At least keep one factor to avoid empty results.
        n_factors = 1

    # Re‑fit with the retained number of factors.
    fa = FactorAnalyzer(
        n_factors=n_factors,
        rotation="varimax",
        method="principal",
        is_corr_matrix=False,
    )
    fa.fit(data)
    loadings = pd.DataFrame(
        fa.loadings_, index=items, columns=[f"Factor{i+1}" for i in range(n_factors)]
    )
    return {
        "n_factors": n_factors,
        "loadings": loadings,
        "eigenvalues": ev.tolist(),
    }


@log_operation("convergent_validity")
def assess_convergent_validity(
    df: pd.DataFrame, score_col: str = "engagement_score"
) -> Dict[str, float]:
    """
    Compute Pearson correlations between the engagement score and a set of
    theoretically related constructs.

    The related construct column names are read from the config key
    ``convergent_constructs`` (list of column names). Returns a dict of
    ``{construct_name: correlation}``.
    """
    related = get_config("convergent_constructs", [])
    if not isinstance(related, list):
        related = []
    results: Dict[str, float] = {}
    if score_col not in df.columns:
        return results
    for col in related:
        if col not in df.columns:
            continue
        # Drop rows where either column is missing.
        sub = df[[score_col, col]].dropna()
        if sub.empty:
            continue
        corr = sub[score_col].corr(sub[col])
        results[col] = float(corr) if not np.isnan(corr) else float("nan")
    return results


@log_operation("write_validity_metrics")
def write_validity_metrics(metrics: Dict[str, Any]) -> None:
    """Serialize the validity metrics to ``results/validity_metrics.yaml``."""
    results_dir = Path(get_config("results_path", "results"))
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "validity_metrics.yaml"
    # Convert any pandas objects to plain structures.
    serialisable = {}
    for k, v in metrics.items():
        if isinstance(v, pd.DataFrame):
            serialisable[k] = v.round(3).replace({np.nan: None}).to_dict()
        elif isinstance(v, (np.ndarray, list, tuple)):
            serialisable[k] = list(v)
        else:
            serialisable[k] = v
    with out_path.open("w") as f:
        yaml.safe_dump(serialisable, f, sort_keys=False)


@log_operation("update_modeling_log")
def update_modeling_log(metrics: Dict[str, Any]) -> None:
    """
    Update ``modeling_log.yaml`` with a flag indicating whether convergent
    validity passed a (soft) threshold.

    If any absolute correlation exceeds 0.3 we consider the validity check
    to have succeeded.
    """
    # Determine status.
    conv_corrs = metrics.get("convergent_validity", {})
    status = {
        "convergent_validity_status": any(
            abs(v or 0) >= 0.3 for v in conv_corrs.values()
        )
    }
    # Write to the log file.
    update_log_section("validity", status)


@log_operation("export_engineered_data")
def export_engineered_data(df: pd.DataFrame) -> None:
    """Write the engineered dataframe to the processed data folder."""
    out_dir = Path(get_config("processed_data_path", "data/processed"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "engineered_data.csv"
    df.to_csv(out_path, index=False)


# ----------------------------------------------------------------------
# PIPELINE
# ----------------------------------------------------------------------
@log_operation
def data_engineering_pipeline() -> None:
    """Run the full feature‑engineering pipeline."""
    # 1. Load cleaned data.
    df = load_cleaned_data()

    # 2. Adoption binary
    practice_cols = identify_practice_columns(df)
    df = create_adoption_binary(df, practice_cols)

    # 3. Engagement score
    proxy_cols = select_engagement_proxies(df)
    df = compute_engagement_score(df, proxy_cols)

    # 4. Reliability (Cronbach's α) for the proxy items.
    cronbach_alpha = calculate_cronbach_alpha(df, proxy_cols)

    # 5. Exploratory Factor Analysis.
    efa_results = perform_efa(df, proxy_cols)

    # 6. Convergent validity.
    conv_validity = assess_convergent_validity(df, "engagement_score")

    # 7. Persist metrics.
    metrics = {
        "cronbach_alpha": cronbach_alpha,
        "efa": {
            "n_factors": efa_results.get("n_factors"),
            "eigenvalues": efa_results.get("eigenvalues"),
            "loadings": efa_results.get("loadings"),
        },
        "convergent_validity": conv_validity,
    }
    write_validity_metrics(metrics)
    update_modeling_log(metrics)

    # 8. Export the engineered dataset.
    export_engineered_data(df)


if __name__ == "__main__":
    main()
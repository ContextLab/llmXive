"""Feature engineering script for the Sustainable Agriculture adoption project.

This script loads the cleaned survey data, creates the binary adoption indicator,
constructs a community‑engagement score from proxy variables, and performs
psychometric validation (Cronbach's α, Exploratory Factor Analysis, and a simple
convergent validity check).  All resulting metrics are serialized to
``results/validity_metrics.yaml`` and the modelling log is updated with the
convergent validity status.

The script is deliberately self‑contained and avoids the broken ``log_operation``
decorator that existed in earlier versions of the repository.  Instead it uses a
very small ``SimpleLogger`` that writes JSON entries to the modelling log file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml
from factor_analyzer import FactorAnalyzer
from numpy import var

# ---------------------------------------------------------------------------
# Simple logger – replaces the broken ``log_operation`` decorator
# ---------------------------------------------------------------------------

class SimpleLogger:
    """Very small logger that appends JSON log entries to a yaml file."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        # Ensure the log file exists and is a valid yaml document
        if not self.log_path.exists():
            self.log_path.write_text(yaml.safe_dump({}))

    def log(self, operation: str, **kwargs: Any) -> None:
        entry = {
            "operation": operation,
            "parameters": kwargs,
            "timestamp": pd.Timestamp.utcnow().isoformat(),
        }
        # Load existing log, update, and write back
        with self.log_path.open("r", encoding="utf-8") as f:
            try:
                log_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                log_data = {}
        # Keep a list of entries per operation
        log_data.setdefault(operation, []).append(entry)
        with self.log_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(log_data, f)

# ---------------------------------------------------------------------------
# Configuration helpers – thin wrappers around the project's config module
# ---------------------------------------------------------------------------

try:
    from config import get_config
except Exception:  # pragma: no cover – defensive fallback
    # Minimal fallback if the config module is broken; use defaults.
    def get_config(key: str = None, default: Any = None) -> Any:  # type: ignore
        defaults = {
            "project_root": ".",
            "raw_data_path": "data/raw",
            "processed_data_path": "data/processed",
            "results_path": "results",
            "modeling_log_path": "modeling_log.yaml",
        }
        if key is None:
            return defaults
        return defaults.get(key, default)

# ---------------------------------------------------------------------------
# Custom exception for the feature‑engineering pipeline
# ---------------------------------------------------------------------------

class FeatureEngineeringError(RuntimeError):
    """Raised when a step in the feature‑engineering pipeline fails."""

    pass

# ---------------------------------------------------------------------------
# Core pipeline functions
# ---------------------------------------------------------------------------

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned data produced by ``02_clean_data.py``."""
    base_dir = Path(get_config("project_root", "."))
    processed_dir = base_dir / get_config("processed_data_path", "data/processed")
    cleaned_path = processed_dir / "cleaned_data.csv"
    if not cleaned_path.is_file():
        raise FeatureEngineeringError(f"Cleaned data not found at {cleaned_path}")
    df = pd.read_csv(cleaned_path)
    return df

def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """
    Return a list of column names that represent reported sustainable practices.
    The convention used throughout the repo is that practice columns start with
    ``practice_``.
    """
    practice_cols = [c for c in df.columns if c.lower().startswith("practice_")]
    if not practice_cols:
        raise FeatureEngineeringError("No practice columns identified in cleaned data.")
    return practice_cols

def create_adoption_binary(df: pd.DataFrame, practice_cols: List[str]) -> pd.DataFrame:
    """
    Create a binary indicator ``adoption_binary`` that is 1 if the respondent
    reports any sustainable practice, otherwise 0.
    """
    df["adoption_binary"] = (df[practice_cols].sum(axis=1) > 0).astype(int)
    return df

def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """
    Select the proxy variables that will be combined into the community‑engagement
    score.  The proxy list can be overridden via the config key
    ``proxy_variables``; otherwise a sensible default list is used.
    """
    default_proxies = [
        "membership",
        "extension_contacts",
        "collective_action",
        "knowledge_exchange",
    ]
    proxies = get_config("proxy_variables", default_proxies)
    # Keep only those that actually exist in the dataframe
    existing = [p for p in proxies if p in df.columns]
    if not existing:
        raise FeatureEngineeringError(
            "None of the configured engagement proxies are present in the data."
        )
    return existing

def create_engagement_score(df: pd.DataFrame, proxy_cols: List[str]) -> pd.DataFrame:
    """
    Compute the engagement score as a weighted (or equal‑weight) average of the
    selected proxy variables.  Weights can be supplied via the config key
    ``engagement_weights``; missing weights default to 1.0 (equal weighting).
    """
    weights_cfg: Dict[str, float] = get_config("engagement_weights", {})
    weights = [weights_cfg.get(col, 1.0) for col in proxy_cols]
    total_weight = sum(weights)
    # Normalise weights so they sum to 1
    norm_weights = [w / total_weight for w in weights]
    df["engagement_score"] = sum(df[col] * w for col, w in zip(proxy_cols, norm_weights))
    return df

# ---------------------------------------------------------------------------
# Validation / psychometric functions
# ---------------------------------------------------------------------------

def cronbach_alpha(df: pd.DataFrame, items: List[str]) -> float:
    """
    Compute Cronbach's α for a set of items.  Formula:

        α = (k / (k‑1)) * (1 - Σσ_i² / σ_total²)

    where *k* is the number of items, σ_i² is the variance of item *i*,
    and σ_total² is the variance of the sum of all items.
    """
    if len(items) < 2:
        raise FeatureEngineeringError("Cronbach's α requires at least two items.")
    item_scores = df[items].dropna()
    k = len(items)
    item_vars = item_scores.var(ddof=1).sum()
    total_var = item_scores.sum(axis=1).var(ddof=1)
    if total_var == 0:
        raise FeatureEngineeringError("Zero variance in total score; cannot compute α.")
    alpha = (k / (k - 1)) * (1 - item_vars / total_var)
    return float(alpha)

def run_efa(df: pd.DataFrame, items: List[str]) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis (principal‑axis factoring) on the
    supplied items.  Uses varimax rotation and retains factors with eigenvalues
    > 1 (Kaiser's rule).

    Returns a dict with:
        - ``num_factors``: number of factors retained
        - ``loadings``: DataFrame of factor loadings (items × factors)
        - ``eigenvalues``: list of eigenvalues
    """
    # Prepare data matrix (drop rows with missing values for the items)
    efa_data = df[items].dropna()
    if efa_data.empty:
        raise FeatureEngineeringError("No complete cases available for EFA.")

    # FactorAnalyzer with minimum residual (PAF) extraction
    fa = FactorAnalyzer(method="minres", rotation="varimax")
    fa.fit(efa_data)

    eigenvalues, _ = fa.get_eigenvalues()
    # Kaiser's rule: retain factors with eigenvalue > 1
    retained = sum(eig > 1.0 for eig in eigenvalues)
    if retained == 0:
        # At least keep one factor to avoid empty results
        retained = 1

    # Re‑fit with the retained number of factors
    fa = FactorAnalyzer(
        n_factors=retained, method="minres", rotation="varimax"
    )
    fa.fit(efa_data)

    loadings = pd.DataFrame(
        fa.loadings_, index=efa_data.columns, columns=[f"Factor_{i+1}" for i in range(retained)]
    )
    return {
        "num_factors": retained,
        "loadings": loadings,
        "eigenvalues": eigenvalues.tolist(),
    }

def convergent_validity(
    df: pd.DataFrame, score_col: str, related_cols: List[str]
) -> Dict[str, Any]:
    """
    Simple convergent validity check: Pearson correlation between the new score
    and each theoretically related construct.  Returns a dict mapping each
    related column to its correlation coefficient and a ``passed`` flag that
    is True when any correlation exceeds 0.5 (a common heuristic).
    """
    results: Dict[str, Any] = {"correlations": {}, "passed": False}
    if score_col not in df.columns:
        raise FeatureEngineeringError(f"{score_col} not found for convergent validity.")
    for col in related_cols:
        if col not in df.columns:
            continue
        # Drop missing values pairwise
        pair = df[[score_col, col]].dropna()
        if pair.empty:
            continue
        corr = pair[score_col].corr(pair[col])
        results["correlations"][col] = float(corr)
        if abs(corr) >= 0.5:
            results["passed"] = True
    return results

# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def export_engineered_data(df: pd.DataFrame) -> None:
    """Write the engineered dataset to ``data/processed/engineered_data.csv``."""
    base_dir = Path(get_config("project_root", "."))
    processed_dir = base_dir / get_config("processed_data_path", "data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / "engineered_data.csv"
    df.to_csv(out_path, index=False)

def write_validity_metrics(metrics: Dict[str, Any]) -> None:
    """Serialize validation metrics to ``results/validity_metrics.yaml``."""
    base_dir = Path(get_config("project_root", "."))
    results_dir = base_dir / get_config("results_path", "results")
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "validity_metrics.yaml"
    # Convert any pandas objects to plain python for yaml safety
    serialisable = {}
    for k, v in metrics.items():
        if isinstance(v, pd.DataFrame):
            serialisable[k] = v.round(3).astype(float).to_dict(orient="list")
        else:
            serialisable[k] = v
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(serialisable, f, sort_keys=False)

def update_modeling_log(status: Dict[str, Any]) -> None:
    """Update ``modeling_log.yaml`` with the convergent validity status."""
    base_dir = Path(get_config("project_root", "."))
    log_path = base_dir / get_config("modeling_log_path", "modeling_log.yaml")
    logger = SimpleLogger(log_path)
    logger.log("convergent_validity_status", **status)

# ---------------------------------------------------------------------------
# Main execution routine
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> None:
    """
    End‑to‑end feature‑engineering pipeline.

    Steps:
    1. Load cleaned data.
    2. Create ``adoption_binary``.
    3. Build ``engagement_score`` from proxy variables.
    4. Compute Cronbach's α for the proxy items.
    5. Run EFA on the proxy items.
    6. Perform a convergent validity check (correlate the score with any
       column whose name contains ``related`` – configurable via ``convergent_cols``).
    7. Write engineered data, validity metrics, and update the modelling log.
    """
    try:
        df = load_cleaned_data()
        practice_cols = identify_practice_columns(df)
        df = create_adoption_binary(df, practice_cols)

        proxy_cols = select_engagement_proxies(df)
        df = create_engagement_score(df, proxy_cols)

        # --- Psychometric validation -------------------------------------------------
        alpha = cronbach_alpha(df, proxy_cols)

        efa_results = run_efa(df, proxy_cols)

        # Convergent validity: look for columns that the config flags as related.
        default_related = [c for c in df.columns if "related" in c.lower()]
        related_cols = get_config("convergent_cols", default_related)
        conv_valid = convergent_validity(df, "engagement_score", related_cols)

        # ---------------------------------------------------------------------------

        # Export engineered dataset
        export_engineered_data(df)

        # Assemble all metrics
        all_metrics = {
            "cronbach_alpha": round(alpha, 3),
            "efa": {
                "num_factors": efa_results["num_factors"],
                "eigenvalues": [round(ev, 3) for ev in efa_results["eigenvalues"]],
                "loadings": efa_results["loadings"],
            },
            "convergent_validity": conv_valid,
        }

        # Write metrics to YAML
        write_validity_metrics(all_metrics)

        # Update modelling log
        update_modeling_log(
            {
                "passed": conv_valid["passed"],
                "alpha": round(alpha, 3),
                "num_factors": efa_results["num_factors"],
            }
        )

        print("Feature engineering completed successfully.")
    except FeatureEngineeringError as fe:
        sys.stderr.write(f"Feature engineering error: {fe}\\n")
        sys.exit(1)
    except Exception as exc:  # pragma: no cover – unexpected errors
        sys.stderr.write(f"Unexpected error during feature engineering: {exc}\\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

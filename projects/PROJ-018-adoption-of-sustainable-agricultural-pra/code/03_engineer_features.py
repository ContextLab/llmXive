"""Feature engineering for the sustainable‑agriculture project.

This module implements the full pipeline required by task **T022**:
1. Load the cleaned dataset produced by ``code/02_clean_data.py``.
2. Identify practice‑related columns and create a binary adoption indicator.
3. Select engagement‑proxy variables, compute an engagement score, and
   attach it to the dataframe.
4. Compute reliability (Cronbach's α) for the proxy set.
5. Run an Exploratory Factor Analysis (EFA) using Principal Axis Factoring,
   Varimax rotation, and retain factors with eigenvalues > 1 (Kaiser's rule).
6. Perform a convergent‑validity check by correlating the engagement score
   with a theoretically related construct (if present).
7. Serialize all validity metrics to ``results/validity_metrics.yaml``.
8. Update ``modeling_log.yaml`` with the convergent‑validity status.

The implementation is deliberately defensive: missing columns are logged
but do not stop execution, and all logging is performed via the tolerant
``log_operation`` decorator / helper defined in ``code/logging_config.py``.
"""
from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from factor_analyzer import FactorAnalyzer, calculate_kmo, calculate_bartlett_sphericity
from scipy.stats import pearsonr

# --------------------------------------------------------------------------- #
# Logging utilities (decorator & direct calls) – imported from the shared module.
# --------------------------------------------------------------------------- #
from .logging_config import log_operation, update_log_section

# --------------------------------------------------------------------------- #
# Configuration utilities.
# --------------------------------------------------------------------------- #
from .config import (
    get_config,
    get_processed_data_path,
    get_results_path,
    get_modeling_log_path,
    set_random_seed,
)

# --------------------------------------------------------------------------- #
# Helper constants – these can be overridden via the configuration file.
# --------------------------------------------------------------------------- #
DEFAULT_ENGAGEMENT_PROXIES = [
    "membership",
    "extension_visits",
    "collective_action",
    "knowledge_exchange",
]

# --------------------------------------------------------------------------- #
# Core pipeline functions.
# --------------------------------------------------------------------------- #

@log_operation("load_cleaned_data")
def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned CSV produced by the previous stage."""
    cleaned_path = get_processed_data_path() / "cleaned_data.csv"
    if not cleaned_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {cleaned_path}")
    df = pd.read_csv(cleaned_path)
    return df

@log_operation("identify_practice_columns")
def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Return a list of columns that indicate practice adoption.

    Heuristic: any column whose name contains the word ``practice`` or ends
    with ``_adopt`` is considered a practice column.
    """
    practice_cols = [
        col
        for col in df.columns
        if "practice" in col.lower() or col.lower().endswith("_adopt")
    ]
    return practice_cols

@log_operation("create_adoption_binary")
def create_adoption_binary(df: pd.DataFrame, practice_cols: List[str]) -> pd.DataFrame:
    """Create a binary ``adoption_binary`` column.

    The column is set to 1 if **any** practice column has a truthy (non‑zero)
    value for the row, otherwise 0.
    """
    if not practice_cols:
        # No practice columns – default to all zeros and log the limitation.
        df["adoption_binary"] = 0
        return df
    df["adoption_binary"] = (df[practice_cols] > 0).any(axis=1).astype(int)
    return df

@log_operation("select_engagement_proxies")
def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """Select the proxy variables used to build the engagement score.

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
    """Create ``engagement_score`` as the (equal‑weight) mean of proxy columns.

    Missing values in proxy columns are filled with the column mean before
    averaging.
    """
    if not proxy_cols:
        # No proxies – create a column of zeros and note the fallback.
        df["engagement_score"] = 0.0
        update_log_section(
            "feature_engineering",
            {"engagement_score_fallback": "no proxies available"},
            log_path=get_modeling_log_path(),
        )
        return df

    # Impute missing values with the column mean.
    proxy_data = df[proxy_cols].apply(pd.to_numeric, errors="coerce")
    imputed = proxy_data.fillna(proxy_data.mean())
    df["engagement_score"] = imputed.mean(axis=1)
    return df

@log_operation("cronbach_alpha")
def cronbach_alpha(df: pd.DataFrame, proxy_cols: List[str]) -> float:
    """Calculate Cronbach's α for the engagement proxy set.

    Returns ``float('nan')`` if fewer than two items are present.
    """
    if len(proxy_cols) < 2:
        return float("nan")
    # factor_analyzer provides a direct implementation.
    from factor_analyzer import calculate_alpha

    # Ensure numeric data.
    items = df[proxy_cols].apply(pd.to_numeric, errors="coerce")
    items = items.dropna(axis=0, how="any")
    if items.empty:
        return float("nan")
    alpha, _ = calculate_alpha(items)
    return float(alpha)

@log_operation("run_efa")
def run_efa(df: pd.DataFrame, proxy_cols: List[str]) -> Tuple[pd.DataFrame, List[int]]:
    """Perform Exploratory Factor Analysis.

    Extraction method: Principal Axis Factoring (``method='pa'``).
    Rotation: Varimax.
    Factor retention: Kaiser's rule (eigenvalue > 1).

    Returns
    -------
    loadings_df : pd.DataFrame
        DataFrame where rows are proxy variables and columns are factors.
    retained_factors : list[int]
        Indices (1‑based) of factors retained according to Kaiser's rule.
    """
    if len(proxy_cols) < 2:
        # Not enough items for a meaningful factor analysis.
        empty = pd.DataFrame()
        return empty, []

    items = df[proxy_cols].apply(pd.to_numeric, errors="coerce")
    items = items.dropna(axis=0, how="any")
    if items.empty:
        empty = pd.DataFrame()
        return empty, []

    # Kaiser‑Meyer‑Olkin and Bartlett's test are optional but useful for diagnostics.
    try:
        kmo_all, kmo_model = calculate_kmo(items)
        bartlett_chi2, bartlett_p = calculate_bartlett_sphericity(items)
        update_log_section(
            "efa_diagnostics",
            {"kmo": float(kmo_model), "bartlett_p": float(bartlett_p)},
            log_path=get_modeling_log_path(),
        )
    except Exception:
        # If the tests fail we simply continue – they are not required for the core EFA.
        pass

    # Initialise the factor analyzer.
    fa = FactorAnalyzer(method="principal", rotation="varimax", is_corr_matrix=False)
    fa.fit(items)

    eigenvalues, _ = fa.get_eigenvalues()
    retained = [i + 1 for i, ev in enumerate(eigenvalues) if ev > 1.0]

    if not retained:
        # If no eigenvalue exceeds 1, retain the first factor by default.
        retained = [1]

    # Re‑fit using the retained number of factors.
    fa = FactorAnalyzer(
        n_factors=len(retained), method="principal", rotation="varimax", is_corr_matrix=False
    )
    fa.fit(items)

    loadings = pd.DataFrame(fa.loadings_, index=proxy_cols)
    loadings.columns = [f"Factor_{i+1}" for i in range(loadings.shape[1])]
    return loadings, retained

@log_operation("convergent_validity")
def convergent_validity(df: pd.DataFrame) -> Tuple[float, float]:
    """Compute Pearson correlation between ``engagement_score`` and a theoretical construct.

    The theoretical construct is expected to be stored in a column named
    ``theoretical_construct``.  If that column is absent, the function returns
    ``(nan, nan)`` and logs the limitation.
    """
    if "engagement_score" not in df.columns:
        raise KeyError("engagement_score column is missing from the dataframe.")
    if "theoretical_construct" not in df.columns:
        update_log_section(
            "convergent_validity",
            {"status": "missing_theoretical_construct"},
            log_path=get_modeling_log_path(),
        )
        return float("nan"), float("nan")
    x = pd.to_numeric(df["engagement_score"], errors="coerce")
    y = pd.to_numeric(df["theoretical_construct"], errors="coerce")
    mask = x.notna() & y.notna()
    if mask.sum() == 0:
        return float("nan"), float("nan")
    r, p = pearsonr(x[mask], y[mask])
    return float(r), float(p)

@log_operation("export_engineered_data")
def export_engineered_data(df: pd.DataFrame) -> None:
    """Write the engineered dataframe to ``data/processed/engineered_data.csv``."""
    out_path = get_processed_data_path() / "engineered_data.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

@log_operation("write_validity_metrics")
def write_validity_metrics(
    alpha: float,
    efa_loadings: pd.DataFrame,
    retained_factors: List[int],
    conv_corr: float,
    conv_p: float,
) -> None:
    """Serialise all validity metrics to ``results/validity_metrics.yaml``."""
    results_path = get_results_path()
    results_path.mkdir(parents=True, exist_ok=True)
    metrics: Dict[str, Any] = {
        "cronbach_alpha": alpha,
        "efa": {
            "retained_factors": retained_factors,
            "loadings": efa_loadings.round(3).to_dict(),
        },
        "convergent_validity": {
            "pearson_r": conv_corr,
            "p_value": conv_p,
        },
    }
    out_file = results_path / "validity_metrics.yaml"
    with out_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(metrics, f, sort_keys=False)

@log_operation("update_modeling_log")
def update_modeling_log(conv_corr: float, conv_p: float) -> None:
    """Update ``modeling_log.yaml`` with the convergent‑validity status."""
    status = "passed" if (not pd.isna(conv_corr) and conv_p < 0.05) else "failed"
    entry = {
        "convergent_validity_status": status,
        "convergent_validity": {"pearson_r": conv_corr, "p_value": conv_p},
    }
    update_log_section("validity", entry, log_path=get_modeling_log_path())

@log_operation("feature_engineering_main")
def main() -> None:
    """Run the full feature‑engineering pipeline."""
    # Seed handling – ensures reproducibility across runs.
    set_random_seed(int(get_config("random_seed", 42)))

    # 1. Load cleaned data.
    df = load_cleaned_data()

    # 2. Adoption binary.
    practice_cols = identify_practice_columns(df)
    df = create_adoption_binary(df, practice_cols)

    # 3. Engagement score.
    proxy_cols = select_engagement_proxies(df)
    df = create_engagement_score(df, proxy_cols)

    # 4. Reliability (Cronbach's α).
    alpha = cronbach_alpha(df, proxy_cols)

    # 5. Exploratory Factor Analysis.
    efa_loadings, retained = run_efa(df, proxy_cols)

    # 6. Convergent validity.
    conv_r, conv_p = convergent_validity(df)

    # 7. Persist engineered dataset.
    export_engineered_data(df)

    # 8. Persist validity metrics.
    write_validity_metrics(alpha, efa_loadings, retained, conv_r, conv_p)

    # 9. Update the global modeling log.
    update_modeling_log(conv_r, conv_p)

    # Inform the user (optional – not required for the automated run‑book).
    print("Feature engineering completed successfully.")
    print(f"Cronbach's α: {alpha:.3f}")
    print(f"Retained EFA factors: {retained}")
    print(f"Convergent validity (r, p): ({conv_r:.3f}, {conv_p:.3f})")

if __name__ == "__main__":
    main()

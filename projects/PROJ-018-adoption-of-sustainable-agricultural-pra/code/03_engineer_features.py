"""
Feature Engineering for Sustainable Agriculture Adoption Study (US2)

Tasks:
- Create adoption_binary indicator
- Construct engagement_score (composite index)
- Calculate Cronbach's Alpha
- Perform Exploratory Factor Analysis (EFA) with Principal Axis Factoring
- Check convergent validity
- Serialize metrics to results/validity_metrics.yaml
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from factor_analyzer import FactorAnalyzer

# Import shared config and logging
from config import get_config
from logging_config import (
    get_logger,
    log_operation,
    update_log_section,
    initialize_modeling_log,
)

logger = logging.getLogger(__name__)
reproducibility_logger = get_logger()

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------

@log_operation("identify_practice_columns")
def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns representing sustainable agricultural practices.
    Assumes columns contain keywords like 'practice', 'method', 'technique'.
    """
    keywords = ["practice", "method", "technique", "irrigation", "organic", "conservation"]
    cols = []
    for col in df.columns:
        if any(kw in col.lower() for kw in keywords):
            cols.append(col)
    # Fallback: if no matches, look for binary-like columns not in standard metadata
    if not cols:
        for col in df.columns:
            if df[col].dtype in ["int64", "float64"] and df[col].nunique() <= 2:
                cols.append(col)
    return cols

@log_operation("create_adoption_binary")
def create_adoption_binary(df: pd.DataFrame, practice_cols: List[str]) -> pd.DataFrame:
    """
    Create adoption_binary: 1 if any sustainable practice reported (value > 0), else 0.
    """
    if not practice_cols:
        logger.warning("No practice columns found. Creating dummy adoption_binary column.")
        df["adoption_binary"] = 0
        return df

    # Check if any of the practice columns have non-zero values
    # Assuming 1 = adopted, 0 = not adopted
    adoption_mask = df[practice_cols].gt(0).any(axis=1)
    df["adoption_binary"] = adoption_mask.astype(int)
    return df

@log_operation("select_engagement_proxies")
def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """
    Select proxy variables for community engagement.
    Keywords: membership, extension, collective, knowledge, exchange, training.
    """
    keywords = [
        "membership", "extension", "collective", "knowledge", "exchange",
        "training", "group", "community", "social", "network"
    ]
    cols = []
    for col in df.columns:
        if any(kw in col.lower() for kw in keywords):
            cols.append(col)
    return cols

@log_operation("create_engagement_score")
def create_engagement_score(df: pd.DataFrame, proxy_cols: List[str]) -> pd.DataFrame:
    """
    Create engagement_score as a weighted sum or equal-weight average of proxies.
    """
    if not proxy_cols:
        logger.warning("No engagement proxies found. Creating dummy score of 0.")
        df["engagement_score"] = 0.0
        return df

    # Ensure numeric
    numeric_proxies = df[proxy_cols].select_dtypes(include=[np.number])
    if numeric_proxies.empty:
        logger.warning("No numeric engagement proxies found.")
        df["engagement_score"] = 0.0
        return df

    # Equal-weight average (handling NaNs by mean of available)
    df["engagement_score"] = numeric_proxies.mean(axis=1)
    return df

@log_operation("calculate_cronbach_alpha")
def calculate_cronbach_alpha(df: pd.DataFrame, item_cols: List[str]) -> Optional[float]:
    """
    Calculate Cronbach's Alpha for reliability.
    Returns None if calculation fails (e.g., < 2 items).
    """
    if len(item_cols) < 2:
        logger.warning("Less than 2 items provided for Cronbach's Alpha.")
        return None

    data = df[item_cols].dropna()
    if data.shape[0] < 2:
        return None

    # Using a manual calculation or factor_analyzer if available
    # factor_analyzer's reliability function is often preferred
    try:
        from factor_analyzer import calculate_cronbach_alpha as fa_cronbach
        alpha, _ = fa_cronbach(data)
        return float(alpha)
    except Exception as e:
        logger.warning(f"Could not calculate Cronbach's Alpha: {e}")
        return None

@log_operation("perform_efa")
def perform_efa(
    df: pd.DataFrame,
    item_cols: List[str],
    rotation: str = "varimax",
    method: str = "pa"
) -> Tuple[Optional[FactorAnalyzer], Dict[str, Any]]:
    """
    Perform Exploratory Factor Analysis.
    Extraction: Principal Axis Factoring ('pa')
    Rotation: Varimax
    Retention: Kaiser's rule (eigenvalues > 1)
    """
    if len(item_cols) < 2:
        logger.warning("Insufficient items for EFA.")
        return None, {}

    data = df[item_cols].dropna()
    if data.shape[0] < 2:
        return None, {}

    try:
        # Initialize FactorAnalyzer
        # method='pa' for Principal Axis Factoring
        fa = FactorAnalyzer(rotation=rotation, method=method)
        fa.fit(data)

        # Get eigenvalues
        ev, _ = fa.get_eigenvalues()
        
        # Kaiser's rule: retain factors with eigenvalue > 1
        n_factors = sum(ev > 1)
        if n_factors == 0:
            n_factors = 1 # At least one factor if possible

        # Refit with determined number of factors if needed (factor_analyzer doesn't auto-select n)
        # Re-initialize with n_factors
        fa_final = FactorAnalyzer(rotation=rotation, method=method, n_factors=n_factors)
        fa_final.fit(data)

        # Get loadings
        loadings = fa_final.loadings
        
        # Format results
        results = {
            "n_factors_retained": int(n_factors),
            "eigenvalues": ev.tolist(),
            "loadings": loadings.tolist(),
            "rotation": rotation,
            "method": method,
            "success": True
        }
        return fa_final, results
    except Exception as e:
        logger.warning(f"EFA failed: {e}")
        return None, {"success": False, "error": str(e)}

@log_operation("check_convergent_validity")
def check_convergent_validity(
    df: pd.DataFrame,
    engagement_score_col: str,
    related_constructs: List[str]
) -> Dict[str, float]:
    """
    Check convergent validity by correlating engagement_score with related constructs.
    Returns a dict of correlations.
    """
    if engagement_score_col not in df.columns:
        return {}

    correlations = {}
    for construct in related_constructs:
        if construct in df.columns:
            # Calculate Pearson correlation, handling NaNs
            corr = df[engagement_score_col].corr(df[construct])
            if not np.isnan(corr):
                correlations[construct] = float(corr)
    return correlations

@log_operation("calculate_reliability_and_validity")
def calculate_reliability_and_validity(
    df: pd.DataFrame,
    engagement_cols: List[str],
    related_constructs: List[str]
) -> Dict[str, Any]:
    """
    Orchestrate reliability (Cronbach's Alpha) and validity (EFA + Convergent) checks.
    """
    metrics = {
        "cronbach_alpha": None,
        "efa_results": {},
        "convergent_validity": {}
    }

    # 1. Cronbach's Alpha
    alpha = calculate_cronbach_alpha(df, engagement_cols)
    metrics["cronbach_alpha"] = alpha

    # 2. EFA
    fa_model, efa_res = perform_efa(df, engagement_cols)
    metrics["efa_results"] = efa_res

    # 3. Convergent Validity
    if "engagement_score" in df.columns:
        conv_validity = check_convergent_validity(
            df, "engagement_score", related_constructs
        )
        metrics["convergent_validity"] = conv_validity

    return metrics

@log_operation("save_validity_metrics")
def save_validity_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Serialize validity metrics to YAML.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Validity metrics saved to {output_path}")

@log_operation("update_modeling_log")
def update_modeling_log(metrics: Dict[str, Any], log_path: str) -> None:
    """
    Update modeling_log.yaml with convergence validity status.
    """
    # Initialize log if it doesn't exist
    initialize_modeling_log()
    
    # Load existing log
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log_data = yaml.safe_load(f) or {}
    else:
        log_data = {}

    # Determine status
    conv_validity = metrics.get("convergent_validity", {})
    if conv_validity:
        # If we have correlations, check if any are significant (arbitrary threshold > 0.3 for exploratory)
        significant = any(abs(v) > 0.3 for v in conv_validity.values())
        status = "passed" if significant else "weak"
    else:
        status = "not_computed"

    # Update log section
    log_data["validity_analysis"] = {
        "convergent_validity_status": status,
        "timestamp": log_data.get("timestamp", ""),
        "details": metrics
    }

    with open(log_path, "w", encoding="utf-8") as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Modeling log updated at {log_path}")

# ----------------------------------------------------------------------
# Main Pipeline
# ----------------------------------------------------------------------

@log_operation("main")
def main() -> None:
    config = get_config()
    
    input_path = config.get("data", {}).get("cleaned_data_path", "data/processed/cleaned_data.csv")
    output_path = config.get("data", {}).get("engineered_data_path", "data/processed/engineered_data.csv")
    results_dir = config.get("results", {}).get("path", "results")
    validity_metrics_path = os.path.join(results_dir, "validity_metrics.yaml")
    modeling_log_path = "modeling_log.yaml"

    # Ensure paths are relative to project root if absolute
    # (Assuming config handles this, but safe-guarding)
    if not os.path.isabs(input_path):
        input_path = os.path.join(config.get("project_root", "."), input_path)

    logger.info(f"Loading cleaned data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. Run T014 first.")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records.")

    # 1. Identify Practice Columns & Create Adoption Binary
    practice_cols = identify_practice_columns(df)
    df = create_adoption_binary(df, practice_cols)
    logger.info(f"Created adoption_binary column. Positive cases: {df['adoption_binary'].sum()}")

    # 2. Select Engagement Proxies & Create Score
    proxy_cols = select_engagement_proxies(df)
    df = create_engagement_score(df, proxy_cols)
    logger.info(f"Created engagement_score using {len(proxy_cols)} proxies.")

    # 3. Reliability and Validity Checks
    # Use the proxy columns for Cronbach's Alpha and EFA
    reliability_validity_metrics = calculate_reliability_and_validity(
        df, proxy_cols, ["farm_size", "education"] # Example related constructs
    )

    # 4. Save Outputs
    # Save engineered data
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Engineered data saved to {output_path}")

    # Save validity metrics
    save_validity_metrics(reliability_validity_metrics, validity_metrics_path)

    # Update modeling log
    update_modeling_log(reliability_validity_metrics, modeling_log_path)

    logger.info("Feature engineering and validity checks complete.")

if __name__ == "__main__":
    main()
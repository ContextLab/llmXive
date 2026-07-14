"""
Feature Engineering Module for Agricultural Survey Data.

Creates engagement_score and adoption_binary columns.
Performs reliability and validity checks.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats

from config import get_config, set_random_seed
from logging_config import update_log_section, log_operation


class FeatureEngineeringError(Exception):
    """Custom exception for feature engineering failures."""
    pass


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML."""
    config = get_config()
    return config.to_dict() if config else {}


def load_cleaned_data(input_path: str) -> pd.DataFrame:
    """Load cleaned data from CSV."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(path)


def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns representing sustainable practices."""
    candidates = ["organic_farming", "crop_rotation", "water_conservation", "integrated_pest_management"]
    return [c for c in candidates if c in df.columns]


def create_adoption_binary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create adoption_binary column: 1 if any sustainable practice reported, else 0.
    Based on actual practice columns in the dataset.
    """
    practice_cols = identify_practice_columns(df)
    
    if not practice_cols:
        raise FeatureEngineeringError("No sustainable practice columns found in data")
    
    # Check if any practice is 1
    df["adoption_binary"] = df[practice_cols].any(axis=1).astype(int)
    return df


def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """Select engagement proxy columns."""
    candidates = ["membership", "extension_visits", "collective_action", "knowledge_exchange"]
    return [c for c in candidates if c in df.columns]


def create_engagement_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create engagement_score as weighted sum or equal-weight average of proxies.
    """
    proxy_cols = select_engagement_proxies(df)
    
    if not proxy_cols:
        # Fallback: create a dummy score if no proxies exist
        logging.warning("No engagement proxies found. Creating dummy score.")
        df["engagement_score"] = 0.0
        return df
    
    # Equal-weight average, normalized to 0-1
    score = df[proxy_cols].mean(axis=1)
    
    # Normalize to 0-1 range based on max possible score (assuming max 5 or 10 depending on col)
    max_score = df[proxy_cols].max().max()
    if max_score > 0:
        df["engagement_score"] = score / max_score
    else:
        df["engagement_score"] = 0.0
    
    return df


def calculate_cronbach_alpha(df: pd.DataFrame, item_cols: List[str]) -> float:
    """Calculate Cronbach's alpha for reliability."""
    if len(item_cols) < 2:
        return 0.0
    
    items = df[item_cols].dropna(axis=1)
    if items.shape[1] < 2:
        return 0.0
    
    n_items = items.shape[1]
    var_total = items.var(axis=1).sum()
    var_items = items.var(axis=0).sum()
    
    if var_total == 0:
        return 0.0
    
    alpha = (n_items / (n_items - 1)) * (1 - var_items / var_total)
    return alpha


def perform_efa(df: pd.DataFrame, item_cols: List[str]) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis (EFA).
    Uses Principal Axis Factoring, Varimax rotation, Kaiser's rule.
    """
    if len(item_cols) < 2:
        return {"factors_retained": 0, "loadings": {}, "method": "skipped"}
    
    try:
        import factor_analyzer
        items = df[item_cols].dropna()
        if items.shape[0] < 10 or items.shape[1] < 2:
            return {"factors_retained": 0, "loadings": {}, "method": "insufficient_data"}
        
        fa = factor_analyzer.FactorAnalyzer(
            rotation='varimax',
            method='principal',
            impute='median'
        )
        fa.fit(items)
        
        # Kaiser's rule: eigenvalues > 1
        ev = fa.get_eigenvalues()
        n_factors = sum(e > 1 for e in ev[0])
        
        return {
            "factors_retained": n_factors,
            "loadings": fa.loadings_.tolist(),
            "method": "principal_axis_varimax"
        }
    except ImportError:
        return {"factors_retained": 0, "loadings": {}, "method": "factor_analyzer_not_installed"}
    except Exception as e:
        return {"factors_retained": 0, "loadings": {}, "method": "error", "error": str(e)}


def check_convergent_validity(df: pd.DataFrame, score_col: str, related_col: str) -> Dict[str, Any]:
    """Check convergent validity via correlation."""
    if score_col not in df.columns or related_col not in df.columns:
        return {"passed": False, "correlation": None, "p_value": None}
    
    valid = df[[score_col, related_col]].dropna()
    if len(valid) < 10:
        return {"passed": False, "correlation": None, "p_value": None}
    
    corr, p_val = stats.pearsonr(valid[score_col], valid[related_col])
    return {
        "passed": abs(corr) > 0.3,  # Arbitrary threshold
        "correlation": corr,
        "p_value": p_val
    }


def calculate_reliability_and_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate all reliability and validity metrics."""
    proxy_cols = select_engagement_proxies(df)
    
    alpha = calculate_cronbach_alpha(df, proxy_cols)
    efa_result = perform_efa(df, proxy_cols)
    
    # Convergent validity: correlation with credit_access (theoretically related)
    conv_valid = check_convergent_validity(df, "engagement_score", "credit_access")
    
    return {
        "cronbach_alpha": alpha,
        "efa": efa_result,
        "convergent_validity": conv_valid
    }


def save_validity_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save validity metrics to YAML."""
    import yaml
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(metrics, f)


def update_modeling_log(metrics: Dict[str, Any]) -> None:
    """Update modeling log with validity results."""
    update_log_section("validity_metrics", {
        "convergent_validity_status": "passed" if metrics["convergent_validity"]["passed"] else "failed"
    })


def export_engineered_data(df: pd.DataFrame, output_path: str) -> None:
    """Export engineered data to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


@log_operation("feature_engineering_main")
def main():
    """Main entry point for feature engineering."""
    parser = argparse.ArgumentParser(description="Engineer features from cleaned data")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_data.csv", help="Input path")
    parser.add_argument("--output", type=str, default="data/processed/engineered_data.csv", help="Output path")
    args = parser.parse_args()

    cfg = load_config()
    set_random_seed(cfg.get("random_seed", 42))
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    update_log_section("feature_engineering", {"status": "started", "timestamp": datetime.utcnow().isoformat()})
    
    try:
        # Load
        df = load_cleaned_data(str(input_path))
        
        # Create adoption_binary
        df = create_adoption_binary(df)
        
        # Create engagement_score
        df = create_engagement_score(df)
        
        # Calculate metrics
        metrics = calculate_reliability_and_validity(df)
        
        # Save metrics
        results_dir = Path(cfg.get("results_path", "results"))
        metrics_path = results_dir / "validity_metrics.yaml"
        save_validity_metrics(metrics, str(metrics_path))
        
        # Update log
        update_modeling_log(metrics)
        
        # Export
        export_engineered_data(df, str(output_path))
        
        update_log_section("feature_engineering", {"status": "completed", "rows": len(df)})
        print(f"Engineered data saved to {output_path}")
        
    except Exception as e:
        update_log_section("feature_engineering", {"status": "failed", "error": str(e)})
        raise


if __name__ == "__main__":
    main()

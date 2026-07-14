"""Feature Engineering for Sustainable Agriculture Adoption Study.

This script constructs the `adoption_binary` indicator and `engagement_score`
from the cleaned survey data, performs reliability (Cronbach's alpha) and
validity (EFA) checks, and saves the results.

Input: data/processed/cleaned_data.csv
Output: data/processed/engineered_data.csv, results/validity_metrics.yaml
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from factor_analyzer import FactorAnalyzer
from scipy.stats import pearsonr

# Local imports
from config import get_config
from logging_config import get_logger, log_operation, update_log_section

# --- Custom Exceptions ---
class FeatureEngineeringError(Exception):
    """Custom exception for feature engineering errors."""
    pass

# --- Helper Functions ---

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    return get_config()

def load_cleaned_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the cleaned dataset from the configured path."""
    input_path = config.get("paths", {}).get("cleaned_data", "data/processed/cleaned_data.csv")
    if not os.path.exists(input_path):
        raise FeatureEngineeringError(f"Cleaned data file not found at {input_path}")
    df = pd.read_csv(input_path)
    logging.info(f"Loaded {len(df)} records from {input_path}")
    return df

@log_operation("identify_practice_columns")
def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns representing sustainable agricultural practices.
    Looks for columns containing 'practice' or specific known suffixes.
    """
    # Heuristic: columns with 'practice' in name, or specific known practice columns
    practice_candidates = [
        col for col in df.columns
        if 'practice' in col.lower() or col.startswith('prac_')
    ]
    
    # If heuristic fails, look for binary-like columns that might be practices
    if not practice_candidates:
        binary_like = []
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64'] and df[col].nunique() <= 2:
                binary_like.append(col)
        # Filter out obvious IDs or scores
        practice_candidates = [c for c in binary_like if c not in ['id', 'household_id', 'engagement_score', 'adoption_binary']]
    
    logging.info(f"Identified practice columns: {practice_candidates}")
    return practice_candidates

def create_adoption_binary(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Create `adoption_binary` (1 if any sustainable practice reported).
    Based on FR-005: 1 if any practice column has a value > 0 (or True).
    """
    practice_cols = identify_practice_columns(df)
    
    if not practice_cols:
        logging.warning("No practice columns found. Setting adoption_binary to 0 for all.")
        df['adoption_binary'] = 0
        return df

    # Check if any practice column is non-zero for each row
    # Assuming practices are encoded as 0 (no) and 1 (yes) or similar counts
    # We sum across practice columns; if sum > 0, adoption is 1
    adoption_mask = df[practice_cols].sum(axis=1) > 0
    df['adoption_binary'] = adoption_mask.astype(int)
    
    adoption_rate = df['adoption_binary'].mean()
    logging.info(f"Created adoption_binary. Adoption rate: {adoption_rate:.2%}")
    return df

def select_engagement_proxies(df: pd.DataFrame, config: Dict[str, Any]) -> List[str]:
    """
    Select proxy variables for community engagement.
    Priority: membership, extension, collective_action, knowledge_exchange.
    Fallback: any column with 'engagement', 'community', 'social' in name.
    """
    priority_proxies = ['membership', 'extension', 'collective_action', 'knowledge_exchange']
    found_proxies = []
    
    for p in priority_proxies:
        if p in df.columns:
            found_proxies.append(p)
    
    if not found_proxies:
        # Fallback heuristic
        fallback_cols = [
            col for col in df.columns
            if any(k in col.lower() for k in ['engagement', 'community', 'social', 'group'])
        ]
        found_proxies = fallback_cols

    logging.info(f"Selected engagement proxies: {found_proxies}")
    return found_proxies

def create_engagement_score(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Construct `engagement_score` using weighted sum or equal-weight average
    of selected proxies.
    """
    proxy_cols = select_engagement_proxies(df, config)
    
    if not proxy_cols:
        logging.warning("No engagement proxies found. Creating dummy score of 0.")
        df['engagement_score'] = 0.0
        return df

    # Ensure numeric
    df_proxy = df[proxy_cols].copy()
    df_proxy = df_proxy.apply(pd.to_numeric, errors='coerce')
    
    # Average of available proxies (row-wise mean ignoring NaN)
    df['engagement_score'] = df_proxy.mean(axis=1)
    
    # Fill NaN if all proxies were missing for a row
    df['engagement_score'] = df['engagement_score'].fillna(0.0)
    
    logging.info(f"Created engagement_score from {len(proxy_cols)} proxies.")
    return df

def calculate_cronbach_alpha(df: pd.DataFrame, items: List[str]) -> float:
    """Calculate Cronbach's Alpha for a set of items."""
    if len(items) < 2:
        return 0.0
    
    data = df[items].apply(pd.to_numeric, errors='coerce').dropna(how='all')
    if data.empty or data.shape[0] < 2:
        return 0.0
    
    k = data.shape[1]
    if k < 2:
        return 0.0
    
    item_vars = data.var(ddof=1)
    total_var = data.sum(axis=1).var(ddof=1)
    
    if total_var == 0:
        return 0.0
        
    alpha = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
    return float(alpha)

def perform_efa(df: pd.DataFrame, items: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis (EFA).
    Method: Principal Axis Factoring, Varimax rotation, Kaiser's rule.
    """
    data = df[items].apply(pd.to_numeric, errors='coerce').dropna(how='all')
    if data.empty or data.shape[0] < 2:
        return {"error": "Insufficient data for EFA"}
    
    # FactorAnalyzer with PA extraction and Varimax rotation
    # n_factors=None allows Kaiser's rule to determine factors (eigenvalues > 1)
    fa = FactorAnalyzer(rotation="varimax", method="pa")
    fa.fit(data)
    
    # Get eigenvalues to determine number of factors (Kaiser's rule)
    ev, _ = fa.get_eigenvalues()
    n_factors = sum(ev > 1)
    
    if n_factors == 0:
        n_factors = 1 # Fallback to 1 factor if none pass Kaiser's rule
    
    fa = FactorAnalyzer(n_factors=n_factors, rotation="varimax", method="pa")
    fa.fit(data)
    
    loadings = fa.loadings
    communalities = fa.get_communalities()
    
    return {
        "n_factors": int(n_factors),
        "eigenvalues": ev.tolist(),
        "loadings": loadings.tolist(),
        "communality": communalities.tolist()
    }

def check_convergent_validity(df: pd.DataFrame, engagement_score_col: str, target_col: str) -> Optional[float]:
    """
    Check convergent validity: correlation between engagement_score and a theoretically related construct.
    Returns correlation coefficient if target_col exists, else None.
    """
    if target_col not in df.columns:
        return None
    
    valid_data = df[[engagement_score_col, target_col]].apply(pd.to_numeric, errors='coerce').dropna()
    if valid_data.shape[0] < 2:
        return None
    
    corr, _ = pearsonr(valid_data[engagement_score_col], valid_data[target_col])
    return float(corr)

def calculate_reliability_and_validity(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate all reliability and validity metrics."""
    proxy_cols = select_engagement_proxies(df, config)
    
    metrics = {
        "cronbach_alpha": 0.0,
        "efa_results": {},
        "convergent_validity": None,
        "convergent_validity_target": None
    }
    
    if len(proxy_cols) >= 2:
        alpha = calculate_cronbach_alpha(df, proxy_cols)
        metrics["cronbach_alpha"] = alpha
        
        efa_res = perform_efa(df, proxy_cols, config)
        metrics["efa_results"] = efa_res
    
    # Convergent validity: check correlation with 'social_capital' if available
    target = 'social_capital'
    if target in df.columns:
        corr = check_convergent_validity(df, 'engagement_score', target)
        if corr is not None:
            metrics["convergent_validity"] = corr
            metrics["convergent_validity_target"] = target
    
    return metrics

def save_validity_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save validity metrics to a YAML file."""
    import yaml
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
    logging.info(f"Saved validity metrics to {output_path}")

def update_modeling_log(metrics: Dict[str, Any]) -> None:
    """Update modeling_log.yaml with validity status."""
    status = "passed" if metrics.get("cronbach_alpha", 0) > 0.6 else "warning"
    update_log_section("validity_analysis", {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "cronbach_alpha": metrics.get("cronbach_alpha"),
        "n_factors": metrics.get("efa_results", {}).get("n_factors")
    })

def export_engineered_data(df: pd.DataFrame, config: Dict[str, Any]) -> None:
    """Save the engineered dataframe to CSV."""
    output_path = config.get("paths", {}).get("engineered_data", "data/processed/engineered_data.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Saved engineered data to {output_path}")

# --- Main Execution ---

@log_operation("engineer_features_main")
def main():
    """Main entry point for feature engineering."""
    parser = argparse.ArgumentParser(description="Feature Engineering for Agriculture Study")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    args = parser.parse_args()

    try:
        config = load_config()
        df = load_cleaned_data(config)
        
        # Step 1: Create adoption_binary
        df = create_adoption_binary(df, config)
        
        # Step 2: Create engagement_score
        df = create_engagement_score(df, config)
        
        # Step 3: Calculate reliability and validity
        metrics = calculate_reliability_and_validity(df, config)
        
        # Step 4: Save metrics
        metrics_path = config.get("paths", {}).get("validity_metrics", "results/validity_metrics.yaml")
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        save_validity_metrics(metrics, metrics_path)
        
        # Step 5: Update log
        update_modeling_log(metrics)
        
        # Step 6: Export data
        export_engineered_data(df, config)
        
        logging.info("Feature engineering completed successfully.")
        
    except Exception as e:
        logging.error(f"Feature engineering failed: {str(e)}")
        update_log_section("feature_engineering", {"status": "failed", "error": str(e)})
        raise FeatureEngineeringError(str(e))

if __name__ == "__main__":
    main()
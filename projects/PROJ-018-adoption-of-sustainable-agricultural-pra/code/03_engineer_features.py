"""Feature Engineering Module for Sustainable Agriculture Study (US2).

This module constructs the engagement score and adoption binary indicator,
performs reliability (Cronbach's alpha) and validity (EFA, convergent) checks,
and exports the engineered dataset.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from factor_analyzer import FactorAnalyzer
from scipy import stats
from sklearn.preprocessing import StandardScaler

# Import local config and logging utilities
# Note: Using the API surface defined in the project
try:
    from config import get_config
    from logging_config import update_log_section
except ImportError:
    # Fallback for direct execution if imports fail in some environments
    # In a real project, these should be resolvable relative to code/
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import get_config
    from logging_config import update_log_section


class FeatureEngineeringError(Exception):
    """Custom exception for feature engineering failures."""
    pass


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = Path(get_config("config_path", "code/config.yaml"))
    if not config_path.exists():
        # Fallback to default if file missing, though T002/T007 should handle this
        return {
            "random_seed": 42,
            "data_path": "data",
            "processed_data_path": "data/processed",
            "results_path": "results",
            "engagement_weights": {
                "membership": 1.0,
                "extension": 1.0,
                "collective_action": 1.0,
                "knowledge_exchange": 1.0
            },
            "proxy_variables": ["membership", "extension", "collective_action", "knowledge_exchange"]
        }
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_cleaned_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """Load the cleaned dataset."""
    if input_path is None:
        base_dir = Path(get_config("project_root", "."))
        input_path = base_dir / get_config("processed_data_path", "data/processed") / "cleaned_data.csv"
    else:
        input_path = Path(input_path)

    if not input_path.exists():
        raise FeatureEngineeringError(f"Cleaned data file not found: {input_path}")

    df = pd.read_csv(input_path)
    logging.info(f"Loaded cleaned data with {len(df)} rows and {len(df.columns)} columns from {input_path}")
    return df


def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns related to sustainable practice adoption."""
    # Heuristic: look for columns containing 'practice', 'adopt', or specific crop/tech names
    # This assumes the cleaned data has standardized column names or we use a pattern
    possible_keywords = ['practice', 'adopt', 'organic', 'conservation', 'irrigation', 'seed']
    practice_cols = []

    for col in df.columns:
        col_lower = col.lower()
        # Check if column name matches any keyword or if it's a known binary adoption indicator
        if any(kw in col_lower for kw in possible_keywords):
            practice_cols.append(col)

    # If no columns found via heuristic, check for a generic 'adoption' column or similar
    if not practice_cols:
        for col in df.columns:
            if 'adoption' in col.lower() and 'binary' not in col.lower():
                practice_cols.append(col)

    logging.info(f"Identified {len(practice_cols)} practice columns: {practice_cols}")
    return practice_cols


def create_adoption_binary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a binary adoption indicator (adoption_binary).
    Rule: 1 if ANY sustainable practice is reported (value > 0 or 'Yes'), 0 otherwise.
    """
    practice_cols = identify_practice_columns(df)

    if not practice_cols:
        logging.warning("No practice columns found. Creating a dummy adoption_binary column (all 0).")
        df['adoption_binary'] = 0
        return df

    # Determine which columns are numeric vs categorical
    # Assume 1/Yes indicates adoption, 0/No indicates non-adoption
    # We will sum the adoption status across all practice columns
    adoption_flags = []

    for col in practice_cols:
        if df[col].dtype in ['int64', 'float64']:
            # Numeric: assume > 0 means adopted
            flag = (df[col] > 0).astype(int)
        else:
            # Categorical: assume 'Yes', 'True', 1 means adopted
            flag = df[col].astype(str).str.lower().isin(['yes', 'true', '1', 'adopted']).astype(int)
        adoption_flags.append(flag)

    # Combine: if ANY flag is 1, then adoption_binary is 1
    df['adoption_binary'] = np.any(adoption_flags, axis=0).astype(int)

    logging.info(f"Created adoption_binary: {df['adoption_binary'].sum()} adopters out of {len(df)}")
    return df


def select_engagement_proxies(df: pd.DataFrame, config: Dict[str, Any]) -> List[str]:
    """
    Select proxy variables for community engagement.
    Priority list: membership, extension, collective_action, knowledge_exchange.
    Fallback: use any available columns with 'engagement', 'community', or 'social' in name.
    """
    priority_proxies = config.get("proxy_variables", [
        "membership", "extension", "collective_action", "knowledge_exchange"
    ])

    available_proxies = []
    missing_proxies = []

    for proxy in priority_proxies:
        # Check for exact match or case-insensitive match
        col_match = None
        for col in df.columns:
            if col.lower() == proxy.lower():
                col_match = col
                break

        if col_match and col_match in df.columns:
            # Check if the column has numeric data suitable for scoring
            if pd.api.types.is_numeric_dtype(df[col_match]) or df[col_match].dtype == 'object':
                # If object, check if it can be mapped to numeric (e.g., 1, 2, 3)
                # For now, assume we can convert or it's already numeric
                available_proxies.append(col_match)
            else:
                missing_proxies.append(proxy)
        else:
            missing_proxies.append(proxy)

    # Fallback mechanism if top-priority proxies are absent
    if not available_proxies:
        logging.warning("No priority proxies found. Searching for fallback engagement variables...")
        fallback_keywords = ['engagement', 'community', 'social', 'network', 'group']
        for col in df.columns:
            if any(kw in col.lower() for kw in fallback_keywords):
                if pd.api.types.is_numeric_dtype(df[col]) or df[col].dtype == 'object':
                    available_proxies.append(col)

    if not available_proxies:
        raise FeatureEngineeringError(
            "No engagement proxy variables found in the dataset. "
            "Cannot construct engagement_score."
        )

    logging.info(f"Selected engagement proxies: {available_proxies}")
    return available_proxies


def create_engagement_score(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Construct engagement_score using proxy variables.
    Method: Weighted sum or equal-weight average.
    Fallback: If weights are missing, use equal weights.
    """
    proxies = select_engagement_proxies(df, config)
    weights = config.get("engagement_weights", {})

    # Normalize proxies to 0-1 scale if they are not already
    # Assuming inputs are counts or ordinal scales (e.g., 1-5)
    # We will standardize them to z-scores first, then sum, to handle different scales
    # Or if they are already 0-1, just sum.
    # Let's assume they are ordinal (0-4 or 1-5) and standardize.

    scaler = StandardScaler()
    proxy_data = df[proxies].copy()

    # Handle missing values in proxy columns (impute with mean)
    proxy_data = proxy_data.fillna(proxy_data.mean())

    # Standardize
    scaled_data = scaler.fit_transform(proxy_data)

    # Apply weights
    # If weights are provided for specific names, use them; else equal weight
    weighted_sum = np.zeros(len(df))
    total_weight = 0

    for i, col in enumerate(proxies):
        w = weights.get(col, 1.0)
        weighted_sum += w * scaled_data[:, i]
        total_weight += w

    # Normalize score to a 0-100 range for interpretability
    # Min-max normalization of the weighted sum
    min_val = weighted_sum.min()
    max_val = weighted_sum.max()
    if max_val - min_val == 0:
        df['engagement_score'] = 50.0  # Default if no variance
    else:
        df['engagement_score'] = ((weighted_sum - min_val) / (max_val - min_val)) * 100.0

    logging.info(f"Created engagement_score (mean={df['engagement_score'].mean():.2f}, std={df['engagement_score'].std():.2f})")
    return df


def calculate_cronbach_alpha(df: pd.DataFrame, proxies: List[str]) -> float:
    """Calculate Cronbach's Alpha for the engagement proxies."""
    proxy_data = df[proxies].copy()
    proxy_data = proxy_data.fillna(proxy_data.mean())

    # Cronbach's alpha formula: (k / (k-1)) * (1 - sum(var_i) / var_total)
    k = len(proxies)
    if k < 2:
        logging.warning("Need at least 2 items to calculate Cronbach's alpha.")
        return 0.0

    item_vars = proxy_data.var(ddof=1)
    total_var = proxy_data.sum(axis=1).var(ddof=1)

    if total_var == 0:
        return 0.0

    alpha = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
    return max(0.0, min(1.0, alpha))


def perform_efa(df: pd.DataFrame, proxies: List[str]) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis (EFA).
    Method: Principal Axis Factoring, Varimax rotation, Kaiser's rule (eigenvalues > 1).
    """
    proxy_data = df[proxies].copy()
    proxy_data = proxy_data.fillna(proxy_data.mean())

    if len(proxies) < 2:
        logging.warning("Not enough variables for EFA.")
        return {"status": "skipped", "reason": "insufficient_variables"}

    try:
        # Factor Analyzer setup
        # method='principal' corresponds to Principal Axis Factoring in factor_analyzer
        fa = FactorAnalyzer(n_factors=None, rotation='varimax', method='principal')
        fa.fit(proxy_data)

        # Get eigenvalues
        ev = fa.get_eigenvalues()
        # Kaiser's rule: retain factors with eigenvalue > 1
        factors_retained = sum(e > 1 for e in ev[0])

        if factors_retained == 0:
            factors_retained = 1  # At least one factor

        # Refit with retained factors
        fa_final = FactorAnalyzer(n_factors=factors_retained, rotation='varimax', method='principal')
        fa_final.fit(proxy_data)

        loadings = fa_final.loadings
        communalities = fa_final.get_communalities()

        return {
            "status": "completed",
            "method": "Principal Axis Factoring",
            "rotation": "Varimax",
            "factors_retained": factors_retained,
            "eigenvalues": ev[0].tolist(),
            "loadings": loadings.tolist(),
            "communalities": communalities.tolist()
        }
    except Exception as e:
        logging.error(f"EFA failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "method": "Principal Axis Factoring",
            "rotation": "Varimax"
        }


def check_convergent_validity(df: pd.DataFrame, proxies: List[str], adoption_binary: Optional[pd.Series] = None) -> Dict[str, Any]:
    """
    Check convergent validity: correlation between engagement score and adoption.
    """
    if adoption_binary is None or 'adoption_binary' not in df.columns:
        return {"status": "skipped", "reason": "adoption_binary_not_available"}

    engagement = df['engagement_score']
    adoption = df['adoption_binary']

    # Point-biserial correlation
    try:
        corr, p_val = stats.pointbiserialr(adoption, engagement)
        return {
            "status": "completed",
            "correlation": corr,
            "p_value": p_val,
            "passed": p_val < 0.05  # Statistically significant correlation
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def calculate_reliability_and_validity(df: pd.DataFrame, proxies: List[str]) -> Dict[str, Any]:
    """Calculate all reliability and validity metrics."""
    metrics = {}

    # Cronbach's Alpha
    alpha = calculate_cronbach_alpha(df, proxies)
    metrics['cronbach_alpha'] = alpha

    # EFA
    efa_results = perform_efa(df, proxies)
    metrics['efa'] = efa_results

    # Convergent Validity
    conv_results = check_convergent_validity(df, proxies)
    metrics['convergent_validity'] = conv_results

    return metrics


def save_validity_metrics(metrics: Dict[str, Any], output_path: Optional[str] = None):
    """Save validity metrics to a YAML file."""
    if output_path is None:
        base_dir = Path(get_config("project_root", "."))
        output_path = base_dir / get_config("results_path", "results") / "validity_metrics.yaml"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        # Ensure numpy types are converted to native Python types for YAML
        def convert(obj):
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        yaml.dump(metrics, f, default_flow_style=False, default_style=None, sort_keys=False, allow_unicode=True)

    logging.info(f"Saved validity metrics to {output_path}")


def update_modeling_log(metrics: Dict[str, Any], log_path: Optional[str] = None):
    """Update the modeling log with validity analysis results."""
    if log_path is None:
        base_dir = Path(get_config("project_root", "."))
        log_path = base_dir / get_config("modeling_log_path", "modeling_log.yaml")
    else:
        log_path = Path(log_path)

    log_data = {
        "feature_engineering": {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "validity_analysis": {
                "cronbach_alpha": metrics.get('cronbach_alpha'),
                "efa_factors_retained": metrics.get('efa', {}).get('factors_retained'),
                "efa_method": metrics.get('efa', {}).get('method'),
                "efa_rotation": metrics.get('efa', {}).get('rotation'),
                "convergent_validity_status": metrics.get('convergent_validity', {}).get('passed', False),
                "convergent_validity_details": metrics.get('convergent_validity', {}).get('correlations', {})
            }
        }
    }

    # Load existing log if it exists
    existing_log = {}
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                existing_log = yaml.safe_load(f) or {}
        except Exception:
            existing_log = {}

    # Merge
    for key, value in log_data.items():
        if key in existing_log and isinstance(existing_log[key], dict) and isinstance(value, dict):
            existing_log[key].update(value)
        else:
            existing_log[key] = value

    with open(log_path, 'w') as f:
        yaml.dump(existing_log, f, default_flow_style=False)

    logging.info(f"Updated modeling log at {log_path}")


def export_engineered_data(df: pd.DataFrame, output_path: Optional[str] = None):
    """Export the engineered dataset."""
    if output_path is None:
        base_dir = Path(get_config("project_root", "."))
        output_path = base_dir / get_config("processed_data_path", "data/processed") / "engineered_data.csv"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Exported engineered data to {output_path}")


def main():
    """Main entry point for feature engineering."""
    parser = argparse.ArgumentParser(description="Feature Engineering for Sustainable Agriculture Study")
    parser.add_argument("--input", type=str, help="Path to cleaned data CSV")
    parser.add_argument("--output", type=str, help="Path to output engineered data CSV")
    parser.add_argument("--metrics", type=str, help="Path to output validity metrics YAML")
    args = parser.parse_args()

    try:
        # Load config
        config = get_config()
        if not isinstance(config, dict):
            # Handle case where get_config returns a Config object
            config = config._config if hasattr(config, '_config') else {}

        # Load data
        df = load_cleaned_data(args.input)

        # Create adoption binary
        df = create_adoption_binary(df)

        # Create engagement score
        df = create_engagement_score(df, config)

        # Calculate metrics
        proxies = select_engagement_proxies(df, config)
        metrics = calculate_reliability_and_validity(df, proxies)

        # Save metrics
        save_validity_metrics(metrics, args.metrics)

        # Update log
        update_modeling_log(metrics)

        # Export data
        export_engineered_data(df, args.output)

        # Log completion
        update_log_section("feature_engineering", {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logging.error(f"Feature engineering failed: {e}")
        update_log_section("feature_engineering", {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        raise FeatureEngineeringError(f"Feature engineering failed: {e}") from e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
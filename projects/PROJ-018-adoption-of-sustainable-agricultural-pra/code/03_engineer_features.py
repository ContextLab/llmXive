"""Feature Engineering for Sustainable Agriculture Adoption Study.

This module implements User Story 2:
- Construct Community-Engagement Score & Adoption Indicator
- Reliability and validity checks (Cronbach's alpha, EFA, convergent validity)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from factor_analyzer import FactorAnalyzer
from scipy.stats import pearsonr

# Import from local modules
from config import Config, load_config, get_config, set_random_seed
from logging_config import log_operation, update_log_section, initialize_modeling_log, append_log_entry

# Local imports
from config import get_config
from logging_config import get_logger, log_operation, update_log_section

# --- Custom Exceptions ---
class FeatureEngineeringError(Exception):
    """Custom exception for feature engineering failures."""
    pass

# --- Helper Functions ---

@log_operation
def load_config_wrapper() -> Config:
    """Load configuration."""
    return load_config()


@log_operation
def load_cleaned_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """Load cleaned data from CSV."""
    config = load_config()
    if input_path is None:
        input_path = config.get("processed_data_path", "data/processed/cleaned_data.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")

def load_cleaned_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the cleaned dataset from the configured path."""
    input_path = config.get("paths", {}).get("cleaned_data", "data/processed/cleaned_data.csv")
    if not os.path.exists(input_path):
        raise FeatureEngineeringError(f"Cleaned data file not found at {input_path}")
    df = pd.read_csv(input_path)
    logging.info(f"Loaded {len(df)} records from {input_path}")
    return df


@log_operation
def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns related to sustainable agricultural practices."""
    # Define possible column name patterns for sustainable practices
    practice_patterns = [
        'sustainable_', 'organic_', 'conservation_', 'agroforestry_',
        'crop_rotation', 'integrated_pest', 'water_management', 'soil_health'
    ]

    practice_cols = []
    for col in df.columns:
        col_lower = col.lower()
        for pattern in practice_patterns:
            if pattern in col_lower:
                practice_cols.append(col)
                break

    # If no pattern matches, look for generic 'practice' columns
    if not practice_cols:
        for col in df.columns:
            if 'practice' in col.lower() and col != 'adoption_binary':
                practice_cols.append(col)

    return practice_cols


@log_operation
def create_adoption_binary(df: pd.DataFrame, practice_columns: List[str]) -> pd.DataFrame:
    """
    Create adoption_binary column.
    1 if ANY sustainable practice reported (value > 0 or True), else 0.
    """
    if not practice_columns:
        logging.warning("No practice columns found. Creating adoption_binary as 0 for all.")
        df['adoption_binary'] = 0
        return df

    # Check if columns are boolean or numeric
    valid_cols = []
    for col in practice_columns:
        if col in df.columns:
            # Convert to numeric if needed, treating non-numeric as 0
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                valid_cols.append(col)
            except Exception:
                continue

    if not valid_cols:
        logging.warning("No valid practice columns after conversion. Creating adoption_binary as 0.")
        df['adoption_binary'] = 0
        return df

    # Create binary adoption: 1 if any practice column > 0
    df['adoption_binary'] = (df[valid_cols].gt(0).any(axis=1)).astype(int)

    logging.info(f"Created adoption_binary: {df['adoption_binary'].sum()} adopters out of {len(df)}")
    return df


@log_operation
def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """
    Select proxy variables for community engagement.
    Priority: membership, extension, collective_action, knowledge_exchange
    Fallback: any column containing 'engagement', 'community', 'social', 'network'
    """
    priority_patterns = [
        'membership', 'extension', 'collective_action', 'knowledge_exchange',
        'training', 'workshop', 'group_participation'
    ]

    fallback_patterns = [
        'engagement', 'community', 'social', 'network', 'participation',
        'meeting', 'association', 'cooperative'
    ]

    proxy_cols = []

    # First pass: priority patterns
    for col in df.columns:
        col_lower = col.lower()
        for pattern in priority_patterns:
            if pattern in col_lower:
                proxy_cols.append(col)
                break

    # Second pass: fallback patterns if needed
    if len(proxy_cols) < 2:
        for col in df.columns:
            if col not in proxy_cols:
                col_lower = col.lower()
                for pattern in fallback_patterns:
                    if pattern in col_lower:
                        proxy_cols.append(col)
                        break

    return proxy_cols


@log_operation
def create_engagement_score(df: pd.DataFrame, proxy_columns: List[str]) -> pd.DataFrame:
    """
    Create engagement_score using weighted sum or equal-weight average.
    Normalized to 0-100 scale.
    """
    if not proxy_columns:
        logging.warning("No engagement proxy columns found. Creating engagement_score as 0.")
        df['engagement_score'] = 0.0
        return df

    valid_cols = []
    for col in proxy_columns:
        if col in df.columns:
            try:
                # Convert to numeric
                numeric_col = pd.to_numeric(df[col], errors='coerce').fillna(0)
                df[f'{col}_numeric'] = numeric_col
                valid_cols.append(f'{col}_numeric')
            except Exception:
                continue

    if not valid_cols:
        logging.warning("No valid engagement columns. Creating engagement_score as 0.")
        df['engagement_score'] = 0.0
        return df

    # Calculate mean score across valid proxies
    df['engagement_score'] = df[valid_cols].mean(axis=1)

    # Normalize to 0-100 scale if needed
    if df['engagement_score'].max() > 100:
        max_val = df['engagement_score'].max()
        min_val = df['engagement_score'].min()
        if max_val > min_val:
            df['engagement_score'] = ((df['engagement_score'] - min_val) / (max_val - min_val)) * 100

    logging.info(f"Created engagement_score: mean={df['engagement_score'].mean():.2f}, std={df['engagement_score'].std():.2f}")
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

@log_operation
def calculate_cronbach_alpha(df: pd.DataFrame, item_columns: List[str]) -> float:
    """
    Calculate Cronbach's Alpha for reliability assessment.
    Returns alpha value.
    """
    if len(item_columns) < 2:
        logging.warning("Less than 2 items for Cronbach's alpha. Returning 0.0.")
        return 0.0

    valid_data = df[item_columns].dropna(axis=1, how='all')
    if valid_data.shape[1] < 2:
        logging.warning("Less than 2 valid items after dropping NaN columns. Returning 0.0.")
        return 0.0

    # Calculate Cronbach's alpha manually
    # alpha = (k / (k-1)) * (1 - sum(var_i) / var_total)
    k = valid_data.shape[1]
    if k < 2:
        return 0.0

    item_vars = valid_data.var(ddof=1)
    total_var = valid_data.sum(axis=1).var(ddof=1)

    if total_var == 0:
        return 0.0

    sum_item_vars = item_vars.sum()
    alpha = (k / (k - 1)) * (1 - (sum_item_vars / total_var))

    # Ensure alpha is in valid range [0, 1]
    alpha = max(0.0, min(1.0, alpha))

    return alpha


@log_operation
def perform_efa(df: pd.DataFrame, item_columns: List[str], n_factors: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis (EFA).
    - Extraction: Principal Axis Factoring (method='uls' in factor_analyzer)
    - Rotation: Varimax
    - Retention: Kaiser's rule (eigenvalues > 1)
    """
    if len(item_columns) < 3:
        logging.warning("Less than 3 items for EFA. Skipping.")
        return {
            'extraction': 'skipped',
            'rotation': 'skipped',
            'factors_retained': 0,
            'loadings': {},
            'eigenvalues': []
        }

    valid_data = df[item_columns].dropna()
    if valid_data.shape[0] < 10 or valid_data.shape[1] < 3:
        logging.warning("Insufficient data for EFA. Skipping.")
        return {
            'extraction': 'skipped',
            'rotation': 'skipped',
            'factors_retained': 0,
            'loadings': {},
            'eigenvalues': []
        }

    try:
        # Use 'uls' (Unweighted Least Squares) as approximation for Principal Axis Factoring
        # factor_analyzer doesn't have 'paf' but 'uls' is the closest equivalent
        fa = FactorAnalyzer(rotation='varimax', method='uls')
        fa.fit(valid_data)

        # Get eigenvalues
        eigenvalues, _ = fa.get_eigenvalues()

        # Kaiser's rule: retain factors with eigenvalue > 1
        factors_retained = int(np.sum(eigenvalues > 1))
        if factors_retained == 0 and len(eigenvalues) > 0:
            factors_retained = 1  # At least one factor

        # Get factor loadings
        loadings = fa.loadings_

        # Convert loadings to dict for serialization
        loadings_dict = {}
        for i, col in enumerate(valid_data.columns):
            loadings_dict[col] = {f'factor_{j+1}': float(loadings[i, j]) for j in range(loadings.shape[1])}

        result = {
            'extraction': 'Principal Axis Factoring (uls)',
            'rotation': 'Varimax',
            'factors_retained': factors_retained,
            'loadings': loadings_dict,
            'eigenvalues': [float(e) for e in eigenvalues]
        }

        logging.info(f"EFA completed: {factors_retained} factors retained")
        return result

    except Exception as e:
        logging.error(f"EFA failed: {str(e)}")
        return {
            'extraction': 'failed',
            'rotation': 'failed',
            'factors_retained': 0,
            'loadings': {},
            'eigenvalues': [],
            'error': str(e)
        }


@log_operation
def check_convergent_validity(df: pd.DataFrame, engagement_score_col: str, adoption_col: str) -> Dict[str, Any]:
    """
    Check convergent validity: correlation between engagement_score and adoption_binary.
    Theoretically, higher engagement should correlate with higher adoption.
    """
    if engagement_score_col not in df.columns or adoption_col not in df.columns:
        logging.warning("Columns for convergent validity check not found.")
        return {
            'correlation': None,
            'p_value': None,
            'status': 'skipped',
            'reason': 'Columns not found'
        }

    valid_data = df[[engagement_score_col, adoption_col]].dropna()
    if len(valid_data) < 10:
        logging.warning("Insufficient data for convergent validity check.")
        return {
            'correlation': None,
            'p_value': None,
            'status': 'skipped',
            'reason': 'Insufficient data'
        }

    try:
        corr, p_value = pearsonr(valid_data[engagement_score_col], valid_data[adoption_col])

        # Determine status based on correlation direction and significance
        if p_value < 0.05:
            if corr > 0:
                status = 'passed_positive'
            elif corr < 0:
                status = 'passed_negative'
            else:
                status = 'passed_neutral'
        else:
            status = 'not_significant'

        result = {
            'correlation': float(corr),
            'p_value': float(p_value),
            'status': status,
            'interpretation': f"Correlation of {corr:.3f} (p={p_value:.4f})"
        }

        logging.info(f"Convergent validity: {result['interpretation']}")
        return result

    except Exception as e:
        logging.error(f"Convergent validity check failed: {str(e)}")
        return {
            'correlation': None,
            'p_value': None,
            'status': 'failed',
            'error': str(e)
        }


@log_operation
def calculate_reliability_and_validity(df: pd.DataFrame, item_columns: List[str]) -> Dict[str, Any]:
    """
    Calculate all reliability and validity metrics.
    Returns a dictionary with all metrics.
    """
    metrics = {}

    # Cronbach's Alpha
    alpha = calculate_cronbach_alpha(df, item_columns)
    metrics['cronbach_alpha'] = alpha
    metrics['reliability_status'] = 'passed' if alpha >= 0.7 else 'marginal' if alpha >= 0.6 else 'failed'

    # EFA
    efa_results = perform_efa(df, item_columns)
    metrics['efa'] = efa_results

    # Convergent Validity
    conv_valid = check_convergent_validity(df, 'engagement_score', 'adoption_binary')
    metrics['convergent_validity'] = conv_valid

    return metrics


@log_operation
def save_validity_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save validity metrics to YAML file."""
    import yaml

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        yaml.dump(metrics, f, default_flow_style=False, allow_unicode=True)

    logging.info(f"Validity metrics saved to {output_path}")


@log_operation
def update_modeling_log(metrics: Dict[str, Any]) -> None:
    """Update modeling_log.yaml with validity check results."""
    update_log_section("validity_metrics", {
        "cronbach_alpha": metrics.get('cronbach_alpha'),
        "reliability_status": metrics.get('reliability_status'),
        "convergent_validity_status": metrics.get('convergent_validity', {}).get('status', 'skipped'),
        "efa_factors_retained": metrics.get('efa', {}).get('factors_retained'),
        "efa_rotation": metrics.get('efa', {}).get('rotation'),
        "efa_extraction": metrics.get('efa', {}).get('extraction')
    })

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

@log_operation
def save_engineered_data(df: pd.DataFrame, output_path: str) -> None:
    """Save engineered data to CSV."""
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    logging.info(f"Engineered data saved to {output_path}")

def export_engineered_data(df: pd.DataFrame, config: Dict[str, Any]) -> None:
    """Save the engineered dataframe to CSV."""
    output_path = config.get("paths", {}).get("engineered_data", "data/processed/engineered_data.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Saved engineered data to {output_path}")

@log_operation
def main() -> None:
    """Main entry point for feature engineering."""
    logging.basicConfig(level=logging.INFO)

    # Initialize modeling log
    initialize_modeling_log()

    # Load config
    config = load_config_wrapper()
    set_random_seed(config.get("random_seed", 42))

    # Load cleaned data
    input_path = config.get("processed_data_path", "data/processed/cleaned_data.csv")
    df = load_cleaned_data(input_path)

    # Step 1: Create adoption_binary
    practice_cols = identify_practice_columns(df)
    df = create_adoption_binary(df, practice_cols)

    # Step 2: Create engagement_score
    proxy_cols = select_engagement_proxies(df)
    df = create_engagement_score(df, proxy_cols)

    # Step 3: Calculate reliability and validity metrics
    # Use engagement proxy columns for EFA and Cronbach's alpha
    if proxy_cols:
        # Convert to numeric for analysis
        numeric_proxy_cols = []
        for col in proxy_cols:
            if col in df.columns:
                try:
                    numeric_col = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    df[f'{col}_numeric'] = numeric_col
                    numeric_proxy_cols.append(f'{col}_numeric')
                except Exception:
                    continue

        if numeric_proxy_cols:
            metrics = calculate_reliability_and_validity(df, numeric_proxy_cols)
        else:
            metrics = {
                'cronbach_alpha': 0.0,
                'reliability_status': 'skipped',
                'convergent_validity': {'status': 'skipped'},
                'efa': {'extraction': 'skipped', 'rotation': 'skipped', 'factors_retained': 0}
            }
    else:
        metrics = {
            'cronbach_alpha': 0.0,
            'reliability_status': 'skipped',
            'convergent_validity': {'status': 'skipped'},
            'efa': {'extraction': 'skipped', 'rotation': 'skipped', 'factors_retained': 0}
        }

    # Step 4: Save validity metrics
    metrics_output_path = config.get("results_path", "results") + "/validity_metrics.yaml"
    save_validity_metrics(metrics, metrics_output_path)

    # Step 5: Update modeling log
    update_modeling_log(metrics)

    # Step 6: Save engineered data
    output_path = config.get("processed_data_path", "data/processed") + "/engineered_data.csv"
    save_engineered_data(df, output_path)

    logging.info("Feature engineering completed successfully.")


if __name__ == "__main__":
    main()
"""
Feature Engineering for Sustainable Agriculture Adoption Study (US2).

This script constructs:
1. `adoption_binary`: A binary indicator (1 if any sustainable practice reported, else 0).
2. `engagement_score`: A composite index based on community engagement proxies.

It also performs reliability checks (Cronbach's Alpha) and Exploratory Factor Analysis (EFA)
to validate the engagement construct, saving metrics to `results/validity_metrics.yaml`.

Dependencies:
- pandas
- statsmodels (for EFA)
- factor_analyzer (for Cronbach's Alpha and EFA)
- numpy
- yaml
- config (project local)
- logging_config (project local)
"""

import os
import sys
import logging
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project local imports
from config import get_config, get_data_path
from logging_config import get_logger, update_log_section

# Ensure statsmodels and factor_analyzer are available
try:
    from statsmodels.stats.diagnostic import het_breuschpagan
except ImportError:
    pass

try:
    from factor_analyzer import FactorAnalyzer, calculate_kmo, calculate_bartlett_sphericity
    from factor_analyzer.factor_analyzer import calculate_cronbach_alpha
except ImportError:
    # Fallback if factor_analyzer is not installed (though requirements.txt should have it)
    FactorAnalyzer = None
    calculate_kmo = None
    calculate_bartlett_sphericity = None
    calculate_cronbach_alpha = None

# Initialize logger
logger = get_logger(__name__)
config = get_config()

# Define paths
DATA_DIR = get_data_path("processed")
RESULTS_DIR = Path(config.get("paths", {}).get("results_dir", "results"))
LOG_FILE = Path(config.get("paths", {}).get("modeling_log", "modeling_log.yaml"))

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# FR-005: Definition of sustainable practices
# Assuming raw data has columns like: 'practice_organic', 'practice_crop_rotation', etc.
# We will look for columns starting with 'practice_' or specific known names.
PRACTICE_PREFIXES = ['practice_']
# Specific known columns if prefixes don't match
KNOWN_PRACTICE_COLS = [
    'practice_organic', 'practice_crop_rotation', 'practice_agroforestry',
    'practice_conservation_tillage', 'practice_integrated_pest_management',
    'practice_water_harvesting'
]

# FR-011: Engagement proxies
# These are the variables used to construct the engagement score.
# Priority order: membership, extension, collective_action, knowledge_exchange
ENGAGEMENT_PROXIES = [
    'membership', 'extension', 'collective_action', 'knowledge_exchange'
]
# Fallback proxies if top ones are missing
FALLBACK_PROXIES = [
    'training_attended', 'group_participation', 'extension_visits'
]

def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns representing sustainable practices."""
    practice_cols = []
    # Check known columns first
    for col in KNOWN_PRACTICE_COLS:
        if col in df.columns:
            practice_cols.append(col)
    
    # Check prefixes
    for prefix in PRACTICE_PREFIXES:
        matching = [c for c in df.columns if c.startswith(prefix)]
        practice_cols.extend(matching)
    
    # Deduplicate
    return list(set(practice_cols))

def create_adoption_binary(df: pd.DataFrame) -> pd.DataFrame:
    """
    FR-005: Create adoption_binary (1 if any sustainable practice reported).
    
    Logic:
    1. Identify all practice columns.
    2. If any practice column is > 0 (or 'Yes'/'True'), set adoption_binary = 1.
    3. Otherwise, 0.
    """
    practice_cols = identify_practice_columns(df)
    
    if not practice_cols:
        logger.warning("No practice columns found. Creating adoption_binary as all 0s.")
        df['adoption_binary'] = 0
        return df

    # Normalize columns to numeric (0/1) for calculation
    # Assuming 1 = Yes/Adopted, 0 = No/Not Adopted. 
    # If categorical, we might need mapping, but synthetic data usually uses 0/1.
    practice_data = df[practice_cols].copy()
    practice_data = pd.to_numeric(practice_data, errors='coerce').fillna(0)
    
    # A row is adopted if sum of practices > 0
    df['adoption_binary'] = (practice_data.sum(axis=1) > 0).astype(int)
    
    logger.info(f"Created adoption_binary based on {len(practice_cols)} practice columns.")
    logger.info(f"Adoption rate: {df['adoption_binary'].mean():.2%}")
    
    return df

def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """
    FR-011: Select available engagement proxies with fallback mechanism.
    """
    available = [c for c in ENGAGEMENT_PROXIES if c in df.columns]
    
    if available:
        logger.info(f"Using primary engagement proxies: {available}")
        return available
    
    # Fallback
    fallback_available = [c for c in FALLBACK_PROXIES if c in df.columns]
    if fallback_available:
        logger.warning(f"Primary proxies missing. Using fallbacks: {fallback_available}")
        return fallback_available
    
    logger.error("No engagement proxies found. Cannot create engagement_score.")
    return []

def create_engagement_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    FR-011: Construct engagement_score using weighted sum or equal-weight average.
    
    Logic:
    1. Select available proxies.
    2. Normalize them to 0-1 scale if necessary (min-max normalization).
    3. Compute mean (equal weight) or weighted sum.
    """
    proxies = select_engagement_proxies(df)
    
    if not proxies:
        logger.warning("No engagement proxies available. Setting engagement_score to 0.")
        df['engagement_score'] = 0.0
        return df

    proxy_data = df[proxies].copy()
    # Ensure numeric
    proxy_data = pd.to_numeric(proxy_data, errors='coerce').fillna(0)
    
    # Normalize to 0-1 range to handle different scales (e.g., Likert 1-5 vs Binary 0/1)
    # If all are binary or same scale, this is identity, but safe for mixed.
    min_vals = proxy_data.min()
    max_vals = proxy_data.max()
    
    # Avoid division by zero if max=min=0
    ranges = max_vals - min_vals
    ranges[ranges == 0] = 1
    
    normalized = (proxy_data - min_vals) / ranges
    
    # Equal weight average
    df['engagement_score'] = normalized.mean(axis=1)
    
    logger.info(f"Created engagement_score from {len(proxies)} proxies.")
    
    return df

def calculate_reliability_and_validity(df: pd.DataFrame, proxies: List[str]) -> Dict[str, Any]:
    """
    FR-004, SC-002, FR-011: Calculate Cronbach's Alpha and perform EFA.
    """
    metrics = {
        "cronbach_alpha": None,
        "efa": {
            "method": "Principal Axis Factoring",
            "rotation": "Varimax",
            "retention_rule": "Kaiser's rule (eigenvalues > 1)",
            "factors_retained": None,
            "loadings": None,
            "kmo": None,
            "bartlett": None
        },
        "convergent_validity": {
            "status": "skipped",
            "details": "Requires external construct correlation"
        }
    }
    
    if not proxies or len(proxies) < 2:
        logger.warning("Insufficient proxies for reliability/validity check.")
        return metrics

    # Prepare data for factor analysis (drop NaNs)
    data_for_efa = df[proxies].copy()
    data_for_efa = pd.to_numeric(data_for_efa, errors='coerce')
    data_for_efa = data_for_efa.dropna()
    
    if len(data_for_efa) < 5:
        logger.warning("Too few samples for EFA.")
        return metrics

    # 1. Cronbach's Alpha
    if calculate_cronbach_alpha:
        try:
            alpha, _ = calculate_cronbach_alpha(data_for_efa)
            metrics["cronbach_alpha"] = float(alpha)
            logger.info(f"Cronbach's Alpha: {alpha:.3f}")
        except Exception as e:
            logger.error(f"Failed to calculate Cronbach's Alpha: {e}")
    else:
        logger.warning("factor_analyzer not installed. Skipping Cronbach's Alpha.")

    # 2. KMO and Bartlett's Test
    if calculate_kmo and calculate_bartlett_sphericity:
        try:
            kmo_all, kmo_model = calculate_kmo(data_for_efa)
            metrics["efa"]["kmo"] = float(kmo_model)
            
            chi_sq, p_val = calculate_bartlett_sphericity(data_for_efa)
            metrics["efa"]["bartlett"] = {
                "chi_square": float(chi_sq),
                "p_value": float(p_val)
            }
            logger.info(f"KMO: {kmo_model:.3f}, Bartlett p-value: {p_val:.3e}")
        except Exception as e:
            logger.error(f"Failed KMO/Bartlett test: {e}")
    else:
        logger.warning("factor_analyzer not installed. Skipping KMO/Bartlett.")

    # 3. Exploratory Factor Analysis (EFA)
    if FactorAnalyzer:
        try:
            # Determine number of factors using Kaiser's rule (eigenvalues > 1)
            # We start with a max of len(proxies)
            fa = FactorAnalyzer(rotation="varimax", method="principal")
            fa.fit(data_for_efa)
            
            ev = fa.get_eigenvalues()
            # Count factors with eigenvalue > 1
            n_factors = sum(e > 1 for e in ev)
            if n_factors == 0:
                n_factors = 1 # At least one factor
            
            # Refit with determined number of factors
            fa_final = FactorAnalyzer(n_factors=n_factors, rotation="varimax", method="principal")
            fa_final.fit(data_for_efa)
            
            loadings = fa_final.get_loadings()
            metrics["efa"]["factors_retained"] = n_factors
            # Convert loadings to dict for YAML serialization
            metrics["efa"]["loadings"] = loadings.tolist()
            metrics["efa"]["factor_names"] = [f"Factor_{i+1}" for i in range(n_factors)]
            
            logger.info(f"EFA: Retained {n_factors} factors.")
        except Exception as e:
            logger.error(f"Failed EFA: {e}")
    else:
        logger.warning("factor_analyzer not installed. Skipping EFA.")

    return metrics

def update_modeling_log(metrics: Dict[str, Any], status: str) -> None:
    """Update the modeling_log.yaml with validity metrics."""
    log_entry = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "task": "T020_Feature_Engineering",
        "validity_metrics": metrics,
        "status": status
    }
    
    log_path = Path(LOG_FILE)
    if log_path.exists():
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    else:
        log_data = {}
    
    if "validity_assessment" not in log_data:
        log_data["validity_assessment"] = []
    
    log_data["validity_assessment"].append(log_entry)
    
    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)

def main():
    """Main entry point for feature engineering."""
    logger.info("Starting Feature Engineering (T020)...")
    
    # Load cleaned data
    input_path = DATA_DIR / "cleaned_data.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. Run T014 first.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # 1. Create Adoption Binary
    df = create_adoption_binary(df)
    
    # 2. Create Engagement Score
    df = create_engagement_score(df)
    
    # 3. Reliability and Validity Checks
    proxies = select_engagement_proxies(df)
    validity_metrics = calculate_reliability_and_validity(df, proxies)
    
    # 4. Save Results
    output_path = DATA_DIR / "engineered_data.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved engineered data to {output_path}")
    
    # 5. Save Validity Metrics
    results_file = RESULTS_DIR / "validity_metrics.yaml"
    with open(results_file, 'w') as f:
        yaml.dump(validity_metrics, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Saved validity metrics to {results_file}")
    
    # 6. Update Modeling Log
    update_modeling_log(validity_metrics, "completed")
    
    logger.info("Feature Engineering (T020) completed successfully.")
    return df

if __name__ == "__main__":
    main()
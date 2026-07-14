"""
Feature Engineering Module for Sustainable Agriculture Study (US2)

This module implements:
1. Creation of binary adoption indicator
2. Construction of community engagement score
3. Reliability analysis (Cronbach's Alpha)
4. Exploratory Factor Analysis (EFA) with Principal Axis Factoring, Varimax rotation
5. Convergent validity checks
6. Serialization of metrics to results/validity_metrics.yaml
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
from scipy import stats

# Local imports
from config import get_config
from logging_config import get_logger, log_operation, update_log_section

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)


class FeatureEngineeringError(Exception):
    """Custom exception for feature engineering failures."""
    pass


def get_logger_instance() -> logging.Logger:
    """Return the configured logger instance."""
    return logger


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        # Fallback to default paths if config missing
        return {
            "data": {
                "raw_path": "data/raw/survey_data.csv",
                "cleaned_path": "data/processed/cleaned_data.csv",
                "engineered_path": "data/processed/engineered_data.csv"
            },
            "results": {
                "validity_metrics_path": "results/validity_metrics.yaml",
                "modeling_log_path": "modeling_log.yaml"
            },
            "engagement": {
                "proxies": ["membership", "extension", "collective_action", "knowledge_exchange"],
                "weights": [0.4, 0.3, 0.2, 0.1]
            }
        }
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset."""
    config = load_config()
    path = Path(config["data"]["cleaned_path"])
    if not path.exists():
        raise FeatureEngineeringError(f"Cleaned data not found at {path}. Run T014 first.")
    return pd.read_csv(path)


def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns related to sustainable practices."""
    practice_keywords = ['organic', 'conservation', 'agroforestry', 'irrigation_efficient', 
                       'crop_rotation', 'integrated_pest', 'soil_test', 'cover_crop']
    practice_cols = [col for col in df.columns if any(kw in col.lower() for kw in practice_keywords)]
    return practice_cols


def create_adoption_binary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create adoption_binary column:
    1 if ANY sustainable practice is reported (value > 0 or True), else 0.
    """
    practice_cols = identify_practice_columns(df)
    if not practice_cols:
        logger.warning("No practice columns found. Creating adoption_binary as 0.")
        df["adoption_binary"] = 0
    else:
        # Check if any practice column has a positive value (or True)
        # Assuming binary/ordinal scales where >0 indicates adoption
        mask = df[practice_cols].gt(0).any(axis=1)
        df["adoption_binary"] = mask.astype(int)
    
    logger.info(f"Created adoption_binary: {df['adoption_binary'].sum()} adopters out of {len(df)}")
    return df


def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """
    Select engagement proxy columns from the dataset.
    Priority: membership, extension, collective_action, knowledge_exchange
    Fallback: any column containing 'engagement', 'community', 'social'
    """
    config = load_config()
    priority_proxies = config.get("engagement", {}).get("proxies", 
        ["membership", "extension", "collective_action", "knowledge_exchange"])
    
    available_proxies = [col for col in priority_proxies if col in df.columns]
    
    if not available_proxies:
        # Fallback: search for generic engagement columns
        fallback_keywords = ['engagement', 'community', 'social', 'participation', 'group']
        available_proxies = [col for col in df.columns if any(kw in col.lower() for kw in fallback_keywords)]
    
    if not available_proxies:
        logger.warning("No engagement proxies found in dataset.")
        return []
    
    logger.info(f"Selected engagement proxies: {available_proxies}")
    return available_proxies


def create_engagement_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct engagement_score using weighted sum or equal-weight average.
    If top-priority proxies are absent, use fallback proxies with equal weights.
    """
    proxies = select_engagement_proxies(df)
    if not proxies:
        logger.warning("No engagement proxies found. Creating dummy score of 0.")
        df["engagement_score"] = 0.0
        return df

    config = load_config()
    weights = config.get("engagement", {}).get("weights", [])
    
    # Ensure we have enough weights
    if len(weights) < len(proxies):
        # Use equal weights if specific weights are missing
        weights = [1.0 / len(proxies)] * len(proxies)
        logger.info(f"Using equal weights for {len(proxies)} proxies.")
    else:
        weights = weights[:len(proxies)]
    
    # Normalize weights to sum to 1
    weight_sum = sum(weights)
    if weight_sum > 0:
        weights = [w / weight_sum for w in weights]
    else:
        weights = [1.0 / len(proxies)] * len(proxies)

    # Calculate weighted score
    # Handle missing values by filling with 0 for calculation, or dropping rows
    # Strategy: Fill NaN with 0 for the score calculation (conservative approach)
    score_series = pd.Series(0.0, index=df.index)
    
    for i, proxy in enumerate(proxies):
        col_data = df[proxy].fillna(0)
        score_series += col_data * weights[i]
    
    df["engagement_score"] = score_series
    logger.info(f"Created engagement_score using {len(proxies)} proxies.")
    return df


def calculate_cronbach_alpha(df: pd.DataFrame, items: List[str]) -> float:
    """
    Calculate Cronbach's Alpha for a set of items.
    Formula: alpha = (k / (k-1)) * (1 - sum(var_i) / var_total)
    """
    if len(items) < 2:
        logger.warning("Need at least 2 items for Cronbach's Alpha.")
        return 0.0
    
    item_data = df[items].dropna(axis=0, how='any')
    if item_data.empty:
        logger.warning("No valid data for Cronbach's Alpha calculation.")
        return 0.0
    
    k = len(items)
    variances = item_data.var(axis=0)
    total_variance = item_data.sum(axis=1).var()
    
    if total_variance == 0:
        return 0.0
    
    alpha = (k / (k - 1)) * (1 - variances.sum() / total_variance)
    return float(alpha)


def perform_efa(df: pd.DataFrame, items: List[str], min_factors: int = 1) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis (EFA).
    Extraction: Principal Axis Factoring (PAF)
    Rotation: Varimax
    Retention: Kaiser's rule (eigenvalues > 1)
    
    Returns:
        Dictionary with factor loadings, eigenvalues, number of factors retained.
    """
    if len(items) < 2:
        logger.warning("Need at least 2 items for EFA.")
        return {"loadings": {}, "eigenvalues": [], "n_factors": 0}
    
    item_data = df[items].dropna(axis=0, how='any')
    if item_data.empty:
        logger.warning("No valid data for EFA.")
        return {"loadings": {}, "eigenvalues": [], "n_factors": 0}
    
    # Determine number of factors using Kaiser's rule (eigenvalues > 1)
    # We'll try a range and pick the one that satisfies Kaiser's rule
    # FactorAnalyzer can estimate the number of factors automatically if we set n_factors=None
    # but we need to extract eigenvalues to apply Kaiser's rule explicitly.
    
    # Step 1: Fit with max possible factors to get eigenvalues
    max_f = min(len(items) - 1, 10)  # Reasonable upper bound
    fa = FactorAnalyzer(n_factors=max_f, rotation=None, method='pa')
    fa.fit(item_data)
    
    eigenvalues = fa.get_eigenvalues()
    # eigenvalues[0] is the array of eigenvalues
    n_factors_kaiser = sum(ev > 1 for ev in eigenvalues[0])
    
    # Ensure at least min_factors
    n_factors = max(n_factors_kaiser, min_factors)
    if n_factors == 0:
        n_factors = 1
    
    logger.info(f"EFA: {n_factors} factors retained (Kaiser's rule: eigenvalues > 1).")
    
    # Step 2: Fit with determined number of factors and Varimax rotation
    fa_final = FactorAnalyzer(n_factors=n_factors, rotation='varimax', method='pa')
    fa_final.fit(item_data)
    
    loadings = fa_final.loadings
    # Convert to dictionary for serialization
    loadings_dict = {}
    for i, item in enumerate(items):
        loadings_dict[item] = {f"Factor_{j+1}": float(loadings[i, j]) for j in range(n_factors)}
    
    return {
        "loadings": loadings_dict,
        "eigenvalues": [float(ev) for ev in eigenvalues[0]],
        "n_factors": n_factors
    }


def check_convergent_validity(df: pd.DataFrame, engagement_score_col: str = "engagement_score") -> Dict[str, float]:
    """
    Perform convergent validity check by correlating engagement_score with 
    theoretically related constructs (e.g., adoption_binary, knowledge_score, 
    or other positive indicators).
    
    Returns:
        Dictionary of correlations with related constructs.
    """
    correlations = {}
    
    # Candidate related constructs
    related_constructs = ["adoption_binary", "knowledge_score", "farm_income", "years_farming"]
    
    for construct in related_constructs:
        if construct in df.columns:
            # Calculate Pearson correlation
            valid_data = df[[engagement_score_col, construct]].dropna()
            if len(valid_data) > 10:  # Minimum sample size for correlation
                corr, p_value = stats.pearsonr(valid_data[engagement_score_col], valid_data[construct])
                correlations[construct] = {
                    "correlation": float(corr),
                    "p_value": float(p_value)
                }
                logger.info(f"Convergent validity: {engagement_score_col} vs {construct} = {corr:.3f} (p={p_value:.3f})")
            else:
                logger.warning(f"Insufficient data for correlation: {construct}")
        else:
            logger.debug(f"Related construct '{construct}' not found in dataset.")
    
    if not correlations:
        logger.warning("No convergent validity checks performed (no related constructs found).")
    
    return correlations


def calculate_reliability_and_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Main orchestrator for reliability and validity analysis.
    1. Calculate Cronbach's Alpha for engagement proxies.
    2. Perform EFA on engagement proxies.
    3. Check convergent validity.
    """
    config = load_config()
    proxies = select_engagement_proxies(df)
    
    results = {
        "cronbach_alpha": None,
        "efa": {},
        "convergent_validity": {}
    }
    
    # 1. Cronbach's Alpha
    if len(proxies) >= 2:
        alpha = calculate_cronbach_alpha(df, proxies)
        results["cronbach_alpha"] = alpha
        logger.info(f"Cronbach's Alpha for engagement score: {alpha:.3f}")
    else:
        logger.warning("Cannot calculate Cronbach's Alpha: fewer than 2 proxies.")
    
    # 2. EFA
    if len(proxies) >= 2:
        efa_results = perform_efa(df, proxies)
        results["efa"] = efa_results
    else:
        logger.warning("Cannot perform EFA: fewer than 2 proxies.")
    
    # 3. Convergent Validity
    if "engagement_score" in df.columns:
        conv_validity = check_convergent_validity(df, "engagement_score")
        results["convergent_validity"] = conv_validity
    
    return results


def save_validity_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Serialize validity metrics to YAML file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Validity metrics saved to {output_path}")


def update_modeling_log(log_path: str, convergent_validity_status: str) -> None:
    """Update modeling_log.yaml with convergent validity status."""
    log_path = Path(log_path)
    
    # Load existing log or create new
    if log_path.exists():
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    else:
        log_data = {}
    
    # Update the specific section
    if "validity_analysis" not in log_data:
        log_data["validity_analysis"] = {}
    
    log_data["validity_analysis"]["convergent_validity_status"] = convergent_validity_status
    log_data["validity_analysis"]["timestamp"] = str(pd.Timestamp.now())
    
    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Modeling log updated with convergent_validity_status: {convergent_validity_status}")


@log_operation("engineer_features_main")
def main() -> None:
    """Main execution for User Story 2: Feature Engineering."""
    logger.info("Starting feature engineering (US2)...")
    
    try:
        # Load config
        config = load_config()
        data_path = Path(config["data"]["cleaned_path"])
        output_path = Path(config["data"]["engineered_path"])
        validity_metrics_path = Path(config["results"]["validity_metrics_path"])
        modeling_log_path = Path(config["results"]["modeling_log_path"])
        
        # Load cleaned data
        df = load_cleaned_data()
        logger.info(f"Loaded {len(df)} records from {data_path}")
        
        # 1. Create adoption_binary
        df = create_adoption_binary(df)
        
        # 2. Create engagement_score
        df = create_engagement_score(df)
        
        # 3. Calculate reliability and validity metrics
        validity_results = calculate_reliability_and_validity(df)
        
        # 4. Save validity metrics
        save_validity_metrics(validity_results, str(validity_metrics_path))
        
        # 5. Update modeling log
        conv_status = "completed" if validity_results.get("convergent_validity") else "incomplete"
        update_modeling_log(str(modeling_log_path), conv_status)
        
        # 6. Save engineered dataset
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Engineered data saved to {output_path}")
        
        logger.info("Feature engineering completed successfully.")
        
    except Exception as e:
        logger.error(f"Feature engineering failed: {str(e)}")
        update_log_section("feature_engineering", {"status": "failed", "error": str(e)})
        raise FeatureEngineeringError(f"Feature engineering failed: {str(e)}") from e


if __name__ == "__main__":
    main()
"""Feature engineering module for sustainable agriculture adoption study.

This module creates:
1. adoption_binary: Binary indicator for sustainable practice adoption
2. engagement_score: Composite index for community engagement intensity
3. Reliability and validity metrics (Cronbach's alpha, EFA, convergent validity)
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from factor_analyzer import FactorAnalyzer
from scipy import stats
import yaml

# Import from local modules
from config import load_config, get_config, get_processed_data_path, get_results_path
from logging_config import log_operation, update_log_section, initialize_modeling_log


class FeatureEngineeringError(Exception):
    """Custom exception for feature engineering errors."""
    pass


@log_operation("load_config_wrapper")
def load_config_wrapper() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config = load_config()
    return {
        "processed_data_path": config.get("processed_data_path", "data/processed"),
        "results_path": config.get("results_path", "data/results"),
        "random_seed": config.get("random_seed", 42)
    }


@log_operation("load_cleaned_data")
def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset."""
    config = get_config()
    input_path = Path(config.get("processed_data_path", "data/processed")) / "cleaned_data.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. Run 02_clean_data.py first.")

    df = pd.read_csv(input_path)
    logging.info(f"Loaded cleaned data with {len(df)} rows and {len(df.columns)} columns")
    return df


@log_operation("identify_practice_columns")
def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns related to sustainable agricultural practices.

    Expected columns contain keywords like: 'practice', 'sustainable', 'organic',
    'conservation', 'irrigation', 'fertilizer', 'pesticide'.
    """
    practice_keywords = ['practice', 'sustainable', 'organic', 'conservation',
                       'irrigation', 'fertilizer', 'pesticide', 'crop_rotation',
                       'cover_crop', 'integrated_pest', 'drought_resistant']

    practice_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in practice_keywords):
            practice_cols.append(col)

    logging.info(f"Identified {len(practice_cols)} practice columns: {practice_cols}")
    return practice_cols


@log_operation("create_adoption_binary")
def create_adoption_binary(df: pd.DataFrame, practice_cols: List[str]) -> pd.DataFrame:
    """Create binary adoption indicator.

    adoption_binary = 1 if any sustainable practice is reported (value > 0 or True)
    adoption_binary = 0 otherwise
    """
    if not practice_cols:
        logging.warning("No practice columns found. Creating adoption_binary as all zeros.")
        df['adoption_binary'] = 0
        return df

    # Check for any positive adoption in practice columns
    adoption_mask = df[practice_cols].applymap(lambda x: 1 if pd.notna(x) and x > 0 and x != 'No' and x != 'no' and x != '0' else 0).sum(axis=1) > 0
    df['adoption_binary'] = adoption_mask.astype(int)

    adoption_rate = df['adoption_binary'].mean()
    logging.info(f"Adoption rate: {adoption_rate:.2%} ({df['adoption_binary'].sum()} / {len(df)})")

    return df


@log_operation("select_engagement_proxies")
def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """Select proxy variables for community engagement.

    Expected proxies: membership, extension, collective_action, knowledge_exchange
    """
    proxy_keywords = ['membership', 'extension', 'collective', 'knowledge',
                    'exchange', 'community', 'group', 'training', 'advisor']

    proxy_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in proxy_keywords):
            proxy_cols.append(col)

    logging.info(f"Selected {len(proxy_cols)} engagement proxy columns: {proxy_cols}")
    return proxy_cols


@log_operation("create_engagement_score")
def create_engagement_score(df: pd.DataFrame, proxy_cols: List[str]) -> pd.DataFrame:
    """Create composite engagement score.

    Uses equal-weight average of normalized proxy variables.
    Handles missing values by imputing with median or dropping if >50% missing.
    """
    if not proxy_cols:
        logging.warning("No engagement proxy columns found. Creating dummy score of 0.")
        df['engagement_score'] = 0.0
        return df

    # Select only numeric proxy columns
    numeric_proxies = []
    for col in proxy_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_proxies.append(col)

    if not numeric_proxies:
        logging.warning("No numeric engagement proxy columns found. Creating dummy score of 0.")
        df['engagement_score'] = 0.0
        return df

    # Calculate median for each proxy to handle missing values
    medians = df[numeric_proxies].median()

    # Impute missing values with median
    df_imputed = df[numeric_proxies].copy()
    for col in numeric_proxies:
        if df_imputed[col].isna().any():
            df_imputed[col] = df_imputed[col].fillna(medians[col])

    # Normalize each column to 0-1 range
    df_normalized = (df_imputed - df_imputed.min()) / (df_imputed.max() - df_imputed.min() + 1e-8)

    # Calculate engagement score as mean of normalized proxies
    df['engagement_score'] = df_normalized.mean(axis=1)

    logging.info(f"Engagement score created from {len(numeric_proxies)} proxies. "
                f"Range: [{df['engagement_score'].min():.3f}, {df['engagement_score'].max():.3f}]")

    return df


@log_operation("calculate_cronbach_alpha")
def calculate_cronbach_alpha(df: pd.DataFrame, item_cols: List[str]) -> Optional[float]:
    """Calculate Cronbach's alpha for reliability assessment.

    Args:
        df: DataFrame with item columns
        item_cols: List of column names to use for alpha calculation

    Returns:
        Cronbach's alpha value or None if calculation fails
    """
    if len(item_cols) < 2:
        logging.warning(f"Need at least 2 items for Cronbach's alpha, got {len(item_cols)}")
        return None

    # Select numeric items only
    numeric_items = []
    for col in item_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_items.append(col)

    if len(numeric_items) < 2:
        logging.warning(f"Need at least 2 numeric items for Cronbach's alpha, got {len(numeric_items)}")
        return None

    # Remove rows with any missing values in item columns
    item_data = df[numeric_items].dropna()

    if len(item_data) < 3:
        logging.warning("Not enough complete cases for Cronbach's alpha calculation")
        return None

    try:
        # Calculate Cronbach's alpha
        from factor_analyzer import calculate_cronbach_alpha as fa_cronbach
        alpha, _ = fa_cronbach(item_data)
        logging.info(f"Cronbach's alpha: {alpha:.3f}")
        return alpha
    except Exception as e:
        logging.warning(f"Could not calculate Cronbach's alpha: {e}")
        return None


@log_operation("perform_efa")
def perform_efa(df: pd.DataFrame, item_cols: List[str], n_factors: Optional[int] = None) -> Dict[str, Any]:
    """Perform Exploratory Factor Analysis (EFA).

    Uses Principal Axis Factoring extraction, Varimax rotation,
    and Kaiser's rule (eigenvalues > 1) for factor retention.

    Args:
        df: DataFrame with item columns
        item_cols: List of column names for EFA
        n_factors: Number of factors to extract (None for automatic)

    Returns:
        Dictionary with EFA results
    """
    if len(item_cols) < 3:
        logging.warning(f"Need at least 3 items for EFA, got {len(item_cols)}")
        return {"factors_retained": 0, "loadings": None, "eigenvalues": []}

    # Select numeric items only
    numeric_items = []
    for col in item_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_items.append(col)

    if len(numeric_items) < 3:
        logging.warning(f"Need at least 3 numeric items for EFA, got {len(numeric_items)}")
        return {"factors_retained": 0, "loadings": None, "eigenvalues": []}

    # Remove rows with any missing values
    item_data = df[numeric_items].dropna()

    if len(item_data) < 10:
        logging.warning("Not enough complete cases for EFA (need at least 10)")
        return {"factors_retained": 0, "loadings": None, "eigenvalues": []}

    try:
        # Determine number of factors using Kaiser's rule (eigenvalues > 1)
        fa = FactorAnalyzer(n_factors=None, method='principal', rotation=None)
        fa.fit(item_data)
        eigenvalues = fa.get_eigenvalues()[0]

        # Kaiser's rule: retain factors with eigenvalues > 1
        n_factors_auto = sum(eigenvalues > 1)

        if n_factors is None:
            n_factors = max(1, n_factors_auto)

        logging.info(f"EFA: {len(eigenvalues)} factors considered, {n_factors} retained (Kaiser's rule)")

        # Fit EFA with specified number of factors using Principal Axis Factoring and Varimax rotation
        fa = FactorAnalyzer(n_factors=n_factors, method='principal', rotation='varimax')
        fa.fit(item_data)

        loadings = fa.get_loadings()
        communalities = fa.get_communalities()

        # Calculate variance explained
        variance_explained = fa.get_factor_variance()[0]

        efa_results = {
            "factors_retained": n_factors,
            "extraction": "Principal Axis Factoring",
            "rotation": "Varimax",
            "loadings": loadings.tolist(),
            "eigenvalues": eigenvalues.tolist(),
            "variance_explained": variance_explained.tolist(),
            "communalities": communalities.tolist()
        }

        logging.info(f"EFA completed. Factors retained: {n_factors}")
        logging.info(f"Total variance explained: {sum(variance_explained):.2%}")

        return efa_results

    except Exception as e:
        logging.warning(f"Could not perform EFA: {e}")
        return {"factors_retained": 0, "loadings": None, "eigenvalues": [], "error": str(e)}


@log_operation("check_convergent_validity")
def check_convergent_validity(df: pd.DataFrame, engagement_score_col: str = 'engagement_score',
                             adoption_col: str = 'adoption_binary') -> Dict[str, Any]:
    """Perform convergent validity check.

    Tests correlation between engagement score and theoretically related constructs.
    Expected: Positive correlation between engagement and adoption.

    Returns:
        Dictionary with correlation results and validity status
    """
    if engagement_score_col not in df.columns or adoption_col not in df.columns:
        logging.warning(f"Required columns not found for convergent validity check")
        return {"convergent_validity": False, "correlation": None, "p_value": None}

    # Remove rows with missing values in both columns
    valid_data = df[[engagement_score_col, adoption_col]].dropna()

    if len(valid_data) < 10:
        logging.warning("Not enough complete cases for convergent validity check")
        return {"convergent_validity": False, "correlation": None, "p_value": None}

    try:
        # Calculate correlation (point-biserial for binary outcome)
        correlation, p_value = stats.pointbiserialr(
            valid_data[adoption_col],
            valid_data[engagement_score_col]
        )

        # Convergent validity is supported if correlation is positive and significant
        is_valid = (correlation > 0) and (p_value < 0.05)

        logging.info(f"Convergent validity check: r = {correlation:.3f}, p = {p_value:.4f}")
        logging.info(f"Validity status: {'PASSED' if is_valid else 'FAILED'}")

        return {
            "convergent_validity": is_valid,
            "correlation": correlation,
            "p_value": p_value,
            "interpretation": "Positive correlation between engagement and adoption" if is_valid else "No significant positive correlation"
        }

    except Exception as e:
        logging.warning(f"Could not calculate convergent validity: {e}")
        return {"convergent_validity": False, "correlation": None, "p_value": None, "error": str(e)}


@log_operation("calculate_reliability_and_validity")
def calculate_reliability_and_validity(df: pd.DataFrame, proxy_cols: List[str]) -> Dict[str, Any]:
    """Calculate all reliability and validity metrics.

    Returns:
        Dictionary with all metrics
    """
    metrics = {}

    # Cronbach's Alpha
    alpha = calculate_cronbach_alpha(df, proxy_cols)
    metrics['cronbach_alpha'] = alpha

    # EFA
    efa_results = perform_efa(df, proxy_cols)
    metrics['efa'] = efa_results

    # Convergent Validity
    conv_valid = check_convergent_validity(df)
    metrics['convergent_validity'] = conv_valid['convergent_validity']
    metrics['convergent_correlation'] = conv_valid.get('correlation')
    metrics['convergent_p_value'] = conv_valid.get('p_value')

    return metrics


@log_operation("save_validity_metrics")
def save_validity_metrics(metrics: Dict[str, Any], output_path: str = "results/validity_metrics.yaml") -> None:
    """Save validity metrics to YAML file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert numpy types to Python types for YAML serialization
    def convert_for_yaml(obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_for_yaml(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_for_yaml(i) for i in obj]
        return obj

    clean_metrics = convert_for_yaml(metrics)

    with open(path, 'w') as f:
        yaml.dump(clean_metrics, f, default_flow_style=False, allow_unicode=True)

    logging.info(f"Validity metrics saved to {output_path}")


@log_operation("update_modeling_log")
def update_modeling_log(metrics: Dict[str, Any]) -> None:
    """Update modeling_log.yaml with validity analysis results."""
    log_data = {
        "validity_analysis": {
            "cronbach_alpha": metrics.get('cronbach_alpha'),
            "efa": {
                "factors_retained": metrics.get('efa', {}).get('factors_retained'),
                "extraction": metrics.get('efa', {}).get('extraction'),
                "rotation": metrics.get('efa', {}).get('rotation')
            },
            "convergent_validity_status": "passed" if metrics.get('convergent_validity') else "failed",
            "convergent_correlation": metrics.get('convergent_correlation'),
            "convergent_p_value": metrics.get('convergent_p_value')
        }
    }

    update_log_section("validity_analysis", log_data["validity_analysis"])
    logging.info("Modeling log updated with validity analysis results")


@log_operation("save_engineered_data")
def save_engineered_data(df: pd.DataFrame, output_path: str = "data/processed/engineered_data.csv") -> None:
    """Save the engineered dataset."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(path, index=False)
    logging.info(f"Engineered data saved to {output_path}")


@log_operation("main")
def main() -> None:
    """Main function to run feature engineering pipeline."""
    # Initialize logging
    initialize_modeling_log()

    # Load configuration
    config = load_config_wrapper()
    random_seed = config['random_seed']
    np.random.seed(random_seed)

    logging.info("Starting feature engineering pipeline")
    logging.info(f"Random seed: {random_seed}")

    try:
        # Load cleaned data
        df = load_cleaned_data()

        # Identify practice columns and create adoption binary
        practice_cols = identify_practice_columns(df)
        df = create_adoption_binary(df, practice_cols)

        # Select engagement proxies and create score
        proxy_cols = select_engagement_proxies(df)
        df = create_engagement_score(df, proxy_cols)

        # Calculate reliability and validity metrics
        logging.info("Calculating reliability and validity metrics...")
        metrics = calculate_reliability_and_validity(df, proxy_cols)

        # Save metrics
        results_path = get_results_path()
        metrics_path = Path(results_path) / "validity_metrics.yaml"
        save_validity_metrics(metrics, str(metrics_path))

        # Update modeling log
        update_modeling_log(metrics)

        # Save engineered data
        processed_path = get_processed_data_path()
        output_path = Path(processed_path) / "engineered_data.csv"
        save_engineered_data(df, str(output_path))

        logging.info("Feature engineering pipeline completed successfully")

    except Exception as e:
        logging.error(f"Feature engineering failed: {str(e)}")
        update_log_section("feature_engineering", {"status": "failed", "error": str(e)})
        raise FeatureEngineeringError(f"Feature engineering failed: {str(e)}") from e


if __name__ == "__main__":
    main()
"""Feature Engineering Module for Sustainable Agriculture Adoption Study.

Constructs engagement_score and adoption_binary columns.
Performs reliability (Cronbach's alpha) and validity (EFA) checks.
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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, get_data_path
from logging_config import get_logger, log_operation, update_log_section

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns representing sustainable practice adoption."""
    practice_keywords = ['practice', 'adopt', 'sustainable', 'organic', 'conservation', 'irrigation']
    practice_cols = []

    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in practice_keywords):
            practice_cols.append(col)

    # If no practice columns found, look for binary adoption indicators
    if not practice_cols and 'adoption' in df.columns:
        practice_cols.append('adoption')

    return practice_cols


def create_adoption_binary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create adoption_binary column.

    1 if any sustainable practice reported, 0 otherwise.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with adoption_binary column.
    """
    logger.info("Creating adoption_binary column (T020)...")
    df_eng = df.copy()

    practice_cols = identify_practice_columns(df_eng)

    if 'adoption_binary' not in df_eng.columns:
        if 'adoption' in df_eng.columns:
            # If adoption column exists, convert to binary
            df_eng['adoption_binary'] = df_eng['adoption'].apply(lambda x: 1 if pd.notna(x) and x != 0 and str(x).lower() not in ['no', 'false', '0'] else 0)
        elif practice_cols:
            # Create binary from any practice column
            binary_cols = []
            for col in practice_cols:
                if df_eng[col].dtype in ['int64', 'float64', 'bool']:
                    binary_cols.append(df_eng[col])
                elif df_eng[col].dtype == 'object':
                    # Convert object to binary
                    binary_vals = df_eng[col].apply(lambda x: 1 if pd.notna(x) and str(x).lower() not in ['no', 'false', '0', ''] else 0)
                    binary_cols.append(binary_vals)

            if binary_cols:
                # Any practice = 1
                df_eng['adoption_binary'] = pd.DataFrame(binary_cols).max(axis=1)
            else:
                logger.warning("No valid practice columns found for adoption_binary.")
                df_eng['adoption_binary'] = 0
        else:
            logger.warning("No adoption or practice columns found. Defaulting adoption_binary to 0.")
            df_eng['adoption_binary'] = 0

    logger.info(f"adoption_binary created. Positive cases: {df_eng['adoption_binary'].sum()}")
    return df_eng


def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """
    Select engagement proxy variables.

    Priority order:
    1. membership (community group membership)
    2. extension_contact (extension service contact)
    3. collective_action (participation in collective action)
    4. knowledge_exchange (knowledge sharing activities)

    Falls back to available proxies if top-priority ones are missing.

    Args:
        df: Input DataFrame.

    Returns:
        List of column names to use for engagement score.
    """
    logger.info("Selecting engagement proxy variables (T021)...")

    priority_proxies = [
        'membership',
        'extension_contact',
        'collective_action',
        'knowledge_exchange'
    ]

    # Also check for common variations
    proxy_variations = {
        'membership': ['membership', 'group_membership', 'community_membership', 'org_membership'],
        'extension_contact': ['extension_contact', 'extension', 'extension_service', 'advisor_contact'],
        'collective_action': ['collective_action', 'collective', 'cooperative_participation', 'group_action'],
        'knowledge_exchange': ['knowledge_exchange', 'knowledge_sharing', 'learning', 'training_participation']
    }

    selected = []
    for priority in priority_proxies:
        found = False
        for col in df.columns:
            col_lower = col.lower()
            for variant in proxy_variations.get(priority, [priority]):
                if variant.lower() in col_lower:
                    selected.append(col)
                    found = True
                    break
            if found:
                break

        if not found:
            logger.warning(f"Proxy '{priority}' not found in data. Will use fallback if available.")

    # If no proxies found, try to find any engagement-related columns
    if not selected:
        engagement_keywords = ['engagement', 'participation', 'member', 'extension', 'collective', 'knowledge', 'training', 'group']
        for col in df.columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in engagement_keywords):
                selected.append(col)
                logger.info(f"Using fallback proxy: {col}")

    if not selected:
        logger.warning("No engagement proxy variables found. Will create engagement_score as 0.")

    logger.info(f"Selected engagement proxies: {selected}")
    return selected


def create_engagement_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct engagement_score using proxy variables.

    Uses equal-weight average of available proxies.
    Falls back gracefully if proxies are missing.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with engagement_score column.
    """
    logger.info("Constructing engagement_score (T021)...")
    df_eng = df.copy()

    proxy_cols = select_engagement_proxies(df_eng)

    if not proxy_cols:
        logger.warning("No proxy variables available. Setting engagement_score to 0.")
        df_eng['engagement_score'] = 0
        return df_eng

    # Normalize each proxy to 0-1 range if not already
    normalized_cols = []
    for col in proxy_cols:
        if df_eng[col].dtype in ['int64', 'float64']:
            # Check if already 0-1
            if df_eng[col].min() >= 0 and df_eng[col].max() <= 1:
                normalized_cols.append(col)
            else:
                # Normalize to 0-1
                min_val = df_eng[col].min()
                max_val = df_eng[col].max()
                if max_val > min_val:
                    df_eng[f'{col}_norm'] = (df_eng[col] - min_val) / (max_val - min_val)
                else:
                    df_eng[f'{col}_norm'] = 0.5
                normalized_cols.append(f'{col}_norm')
        else:
            # Assume binary categorical
            normalized_cols.append(col)

    # Calculate equal-weight average
    score_data = df_eng[normalized_cols].mean(axis=1)
    df_eng['engagement_score'] = score_data

    # Log score statistics
    logger.info(f"engagement_score created. Mean: {df_eng['engagement_score'].mean():.3f}, Std: {df_eng['engagement_score'].std():.3f}")

    return df_eng


def calculate_cronbach_alpha(df: pd.DataFrame, items: List[str]) -> float:
    """
    Calculate Cronbach's Alpha for reliability.

    Args:
        df: DataFrame with item columns.
        items: List of column names representing items.

    Returns:
        Cronbach's alpha value.
    """
    if len(items) < 2:
        return 0.0

    item_data = df[items].dropna(axis=0, how='any')
    if item_data.empty:
        return 0.0

    n_items = len(items)
    item_variances = item_data.var(axis=0)
    total_variance = item_data.sum(axis=1).var()

    if total_variance == 0:
        return 0.0

    alpha = (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance)
    return alpha


def perform_efa(df: pd.DataFrame, items: List[str]) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis.

    Uses Principal Axis Factoring, Varimax rotation, Kaiser's rule.

    Args:
        df: DataFrame with item columns.
        items: List of column names.

    Returns:
        Dictionary with EFA results.
    """
    logger.info("Performing Exploratory Factor Analysis...")

    try:
        from factor_analyzer import FactorAnalyzer

        item_data = df[items].dropna(axis=0, how='any')
        if item_data.empty or len(items) < 2:
            logger.warning("Insufficient data for EFA.")
            return {'status': 'skipped', 'reason': 'insufficient_data'}

        # Determine number of factors using Kaiser's rule (eigenvalues > 1)
        fa = FactorAnalyzer(rotation=None)
        fa.fit(item_data)
        eigenvalues = fa.get_eigenvalues()
        n_factors = sum(eigenvalues > 1)

        if n_factors == 0:
            n_factors = 1  # At least one factor

        # Fit with selected number of factors
        fa = FactorAnalyzer(n_factors=n_factors, rotation='varimax')
        fa.fit(item_data)

        factor_loadings = fa.loadings
        communality = fa.get_communalities()

        return {
            'status': 'completed',
            'n_factors': n_factors,
            'eigenvalues': eigenvalues.tolist(),
            'factor_loadings': factor_loadings.tolist(),
            'communality': communality.tolist()
        }

    except ImportError:
        logger.warning("factor_analyzer not installed. Skipping EFA.")
        return {'status': 'skipped', 'reason': 'module_not_installed'}
    except Exception as e:
        logger.warning(f"EFA failed: {e}")
        return {'status': 'failed', 'error': str(e)}


def check_convergent_validity(df: pd.DataFrame, engagement_score: str, related_constructs: List[str]) -> Dict[str, float]:
    """
    Check convergent validity via correlation with related constructs.

    Args:
        df: DataFrame.
        engagement_score: Name of engagement score column.
        related_constructs: List of column names expected to correlate.

    Returns:
        Dictionary of correlations.
    """
    correlations = {}
    for construct in related_constructs:
        if construct in df.columns:
            corr = df[engagement_score].corr(df[construct])
            correlations[construct] = corr
            logger.debug(f"Correlation({engagement_score}, {construct}) = {corr:.3f}")

    return correlations


def calculate_reliability_and_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate all reliability and validity metrics.

    Args:
        df: DataFrame with engineered features.

    Returns:
        Dictionary with all metrics.
    """
    logger.info("Calculating reliability and validity metrics (T022)...")

    proxy_cols = select_engagement_proxies(df)

    if len(proxy_cols) < 2:
        logger.warning("Insufficient proxies for reliability/validity checks.")
        return {
            'cronbach_alpha': 0.0,
            'efa': {'status': 'skipped', 'reason': 'insufficient_proxies'},
            'convergent_validity': {}
        }

    # Cronbach's Alpha
    alpha = calculate_cronbach_alpha(df, proxy_cols)
    logger.info(f"Cronbach's Alpha: {alpha:.3f}")

    # EFA
    efa_results = perform_efa(df, proxy_cols)

    # Convergent validity
    # Assume adoption_binary is theoretically related
    convergent_corr = check_convergent_validity(df, 'engagement_score', ['adoption_binary'])

    results = {
        'cronbach_alpha': alpha,
        'efa': efa_results,
        'convergent_validity': convergent_corr
    }

    return results


def main() -> pd.DataFrame:
    """
    Main function for feature engineering.

    Returns:
        DataFrame with engineered features.
    """
    logger.info("Starting Feature Engineering (T020, T021, T022)...")

    try:
        # Load cleaned data
        input_path = get_data_path('processed/cleaned_data.csv')
        if not os.path.exists(input_path):
            raise CustomDataError(f"Cleaned data not found at {input_path}. Run 02_clean_data.py first.")

        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")

        # Create adoption_binary
        df = create_adoption_binary(df)

        # Create engagement_score
        df = create_engagement_score(df)

        # Calculate reliability and validity
        validity_metrics = calculate_reliability_and_validity(df)

        # Export engineered data
        output_path = get_data_path('processed/engineered_data.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Engineered data saved to {output_path}")

        # Save validity metrics
        results_dir = get_data_path('../results')
        os.makedirs(results_dir, exist_ok=True)
        metrics_path = os.path.join(results_dir, 'validity_metrics.yaml')

        with open(metrics_path, 'w') as f:
            yaml.dump(validity_metrics, f, default_flow_style=False)
        logger.info(f"Validity metrics saved to {metrics_path}")

        # Update modeling log
        update_log_section(
            'feature_engineering',
            {
                'status': 'completed',
                'n_records': len(df),
                'validity_metrics_summary': {
                    'cronbach_alpha': validity_metrics['cronbach_alpha'],
                    'efa_status': validity_metrics['efa'].get('status', 'unknown')
                }
            },
            log_path=get_data_path('modeling_log.yaml')
        )

        return df

    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        update_log_section(
            'error',
            {'message': str(e)},
            log_path=get_data_path('modeling_log.yaml')
        )
        raise


if __name__ == "__main__":
    main()

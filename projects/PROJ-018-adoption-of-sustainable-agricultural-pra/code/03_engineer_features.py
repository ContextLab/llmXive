"""
Feature Engineering Script for Sustainable Agriculture Adoption Study (T020, T021, T022).

This script performs:
1. Creation of binary adoption indicator (adoption_binary).
2. Construction of community engagement score (engagement_score).
3. Reliability (Cronbach's Alpha) and Validity (EFA, Convergent) analysis.
4. Serialization of metrics to results/validity_metrics.yaml.
"""
import os
import sys
import logging
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, get_data_path
from logging_config import get_logger, update_log_section

# Try importing factor_analyzer, handle gracefully if missing
try:
    import factor_analyzer
    from factor_analyzer import FactorAnalyzer
    from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo
    FA_AVAILABLE = True
except ImportError:
    FA_AVAILABLE = False
    logging.warning("factor_analyzer not installed. EFA and Cronbach's Alpha will be skipped or approximated.")

logger = get_logger(__name__)

# --- Helper Functions for T020/T021 ---

def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns representing sustainable agricultural practices."""
    # Common prefixes/suffixes for practice variables
    practice_keywords = ['practice', 'crop', 'irrigation', 'fertilizer', 'pest', 'soil', 'tillage', 'organic']
    practice_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in practice_keywords):
            # Exclude binary flags that might be outcome variables if named differently,
            # but usually practice columns are the raw survey items.
            # We assume columns with 'adoption' in name are outcomes, not inputs.
            if 'adoption' not in col_lower:
                practice_cols.append(col)
    return practice_cols

def create_adoption_binary(df: pd.DataFrame, practice_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Create adoption_binary column.
    1 if ANY sustainable practice is reported (value > 0 or 'Yes'), 0 otherwise.
    """
    if practice_cols is None:
        practice_cols = identify_practice_columns(df)

    if not practice_cols:
        logger.warning("No practice columns identified. Creating adoption_binary as all zeros.")
        df['adoption_binary'] = 0
        return df

    # Check for any non-zero/non-empty value in practice columns
    # Assume practices are coded as 0 (No) and 1 (Yes) or counts > 0.
    # We sum across practice columns; if sum > 0, adoption is True.
    practice_df = df[practice_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    df['adoption_binary'] = (practice_df.sum(axis=1) > 0).astype(int)
    logger.info(f"Created 'adoption_binary' based on {len(practice_cols)} practice columns.")
    return df

def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """Select columns representing community engagement."""
    engagement_keywords = ['membership', 'extension', 'collective', 'knowledge', 'exchange', 'group', 'meeting', 'training']
    proxy_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in engagement_keywords):
            proxy_cols.append(col)
    return proxy_cols

def create_engagement_score(df: pd.DataFrame, proxy_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Construct engagement_score.
    Weighted sum or equal-weight average of proxy variables.
    """
    if proxy_cols is None:
        proxy_cols = select_engagement_proxies(df)

    if not proxy_cols:
        logger.warning("No engagement proxy columns found. Creating engagement_score as 0.")
        df['engagement_score'] = 0.0
        return df

    # Ensure numeric
    proxy_df = df[proxy_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Equal weight average
    df['engagement_score'] = proxy_df.mean(axis=1)
    logger.info(f"Created 'engagement_score' from {len(proxy_cols)} proxy columns.")
    return df

# --- Reliability and Validity Analysis (T022) ---

def calculate_cronbach_alpha(data: pd.DataFrame) -> float:
    """
    Calculate Cronbach's Alpha for a set of items (columns).
    Uses the formula: alpha = (k / (k-1)) * (1 - sum(var_i) / var_total)
    """
    if FA_AVAILABLE:
        try:
            # factor_analyzer calculates alpha internally if we pass items
            # But we need to extract it. Let's use the formula directly for transparency
            # or use the library if it exposes it cleanly.
            # factor_analyzer doesn't have a direct `calculate_alpha` function exposed simply,
            # so we implement the standard formula.
            pass
        except Exception as e:
            logger.warning(f"factor_analyzer calculation failed: {e}")

    # Standard calculation
    k = data.shape[1]
    if k < 2:
        return 0.0

    variances = data.var(axis=0, ddof=1)
    sum_variances = variances.sum()
    total_variance = data.sum(axis=1).var(ddof=1)

    if total_variance == 0:
        return 0.0

    alpha = (k / (k - 1)) * (1 - (sum_variances / total_variance))
    return float(alpha)

def perform_efa(data: pd.DataFrame, n_factors: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis.
    - Extraction: Principal Axis Factoring
    - Rotation: Varimax
    - Retention: Kaiser's rule (eigenvalues > 1) if n_factors not specified.
    """
    if not FA_AVAILABLE:
        logger.error("factor_analyzer library not available. Skipping EFA.")
        return {"error": "factor_analyzer not installed"}

    results = {}

    # 1. Check KMO and Bartlett's
    try:
        kmo_all, kmo_model = calculate_kmo(data)
        bartlett_chi2, bartlett_p = calculate_bartlett_sphericity(data)
        results['kmo'] = float(kmo_model)
        results['bartlett_chi2'] = float(bartlett_chi2)
        results['bartlett_p'] = float(bartlett_p)
    except Exception as e:
        logger.warning(f"KMO/Bartlett calculation failed: {e}")
        results['kmo'] = None
        results['bartlett_chi2'] = None
        results['bartlett_p'] = None

    # 2. Determine number of factors (Kaiser's Rule)
    if n_factors is None:
        fa_temp = FactorAnalyzer(rotation=None, method='pa') # Principal Axis
        fa_temp.fit(data)
        ev = fa_temp.get_eigenvalues()
        # ev is a tuple of (eigenvalues, variance)
        eigenvalues = ev[0]
        n_factors = sum(eigenvalues > 1)
        if n_factors == 0:
            n_factors = 1 # Minimum 1 factor if all < 1 but data exists
        logger.info(f"Kaiser's rule suggests {n_factors} factors (eigenvalues > 1).")
        results['n_factors_kaiser'] = n_factors
        results['eigenvalues'] = eigenvalues.tolist()

    # 3. Run EFA with determined factors
    try:
        fa = FactorAnalyzer(rotation='varimax', method='pa', n_factors=n_factors)
        fa.fit(data)

        loadings = fa.loadings
        # Handle loadings matrix shape (items x factors)
        # Convert to dict for serialization
        loading_dict = {}
        for i, col in enumerate(data.columns):
            loading_dict[col] = loadings[i].tolist()

        results['n_factors_final'] = n_factors
        results['loadings'] = loading_dict
        results['uniqueness'] = fa.uniquenesses.tolist()
        results['rotation_matrix'] = fa.rotation_matrix.tolist() if hasattr(fa, 'rotation_matrix') else None

    except Exception as e:
        logger.error(f"EFA fitting failed: {e}")
        results['error'] = str(e)

    return results

def check_convergent_validity(df: pd.DataFrame, engagement_score_col: str = 'engagement_score',
                              related_constructs: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Perform convergent validity check.
    Correlate engagement_score with theoretically related constructs.
    If no specific constructs provided, try to find 'knowledge' or 'awareness' columns.
    """
    correlations = {}

    if related_constructs is None:
        # Heuristic: look for columns with 'knowledge', 'awareness', 'belief'
        keywords = ['knowledge', 'awareness', 'belief', 'attitude']
        related_constructs = [c for c in df.columns if any(k in c.lower() for k in keywords)]

    if not related_constructs:
        logger.warning("No related constructs found for convergent validity check.")
        return correlations

    for construct in related_constructs:
        if construct in df.columns and engagement_score_col in df.columns:
            # Drop NaNs for correlation
            valid_data = df[[engagement_score_col, construct]].dropna()
            if len(valid_data) > 2:
                corr = valid_data[engagement_score_col].corr(valid_data[construct])
                correlations[construct] = float(corr) if not np.isnan(corr) else None

    return correlations

def calculate_reliability_and_validity(df: pd.DataFrame,
                                       practice_cols: Optional[List[str]] = None,
                                       proxy_cols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Main orchestrator for T022: Reliability and Validity.
    1. Calculate Cronbach's Alpha on engagement proxies.
    2. Perform EFA on engagement proxies.
    3. Check convergent validity.
    """
    metrics = {}

    # 1. Cronbach's Alpha on Engagement Proxies
    if proxy_cols is None:
        proxy_cols = select_engagement_proxies(df)

    if len(proxy_cols) >= 2:
        proxy_data = df[proxy_cols].apply(pd.to_numeric, errors='coerce').dropna(how='all')
        if len(proxy_data) > 0 and proxy_data.shape[1] >= 2:
            alpha = calculate_cronbach_alpha(proxy_data)
            metrics['cronbach_alpha'] = alpha
            logger.info(f"Cronbach's Alpha for engagement proxies: {alpha:.4f}")
        else:
            metrics['cronbach_alpha'] = None
            logger.warning("Not enough data points for Cronbach's Alpha.")
    else:
        metrics['cronbach_alpha'] = None
        logger.warning("Less than 2 proxy columns for Cronbach's Alpha.")

    # 2. Exploratory Factor Analysis (EFA)
    if FA_AVAILABLE and len(proxy_cols) >= 2:
        proxy_data = df[proxy_cols].apply(pd.to_numeric, errors='coerce').dropna(how='all')
        if len(proxy_data) > 0 and proxy_data.shape[1] >= 2:
            efa_results = perform_efa(proxy_data)
            metrics['efa'] = efa_results
            logger.info("EFA completed.")
        else:
            metrics['efa'] = {"error": "Insufficient data for EFA"}
    else:
        metrics['efa'] = {"error": "factor_analyzer not available or insufficient data"}

    # 3. Convergent Validity
    if 'engagement_score' in df.columns:
        conv_valid = check_convergent_validity(df)
        metrics['convergent_validity'] = conv_valid
        logger.info(f"Convergent validity correlations: {conv_valid}")
    else:
        metrics['convergent_validity'] = {}
        logger.warning("engagement_score column not found for convergent validity.")

    return metrics

def update_modeling_log(metrics: Dict[str, Any], log_path: Path):
    """Update modeling_log.yaml with validity metrics."""
    try:
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        log_data = {}

    # Update validity section
    validity_status = "success"
    if 'cronbach_alpha' in metrics and metrics['cronbach_alpha'] is None:
        validity_status = "warning: alpha not computed"
    if 'efa' in metrics and 'error' in metrics['efa']:
        validity_status = "warning: efa failed"

    log_data['validity_analysis'] = {
        'status': validity_status,
        'convergent_validity_status': 'completed' if metrics.get('convergent_validity') else 'skipped',
        'metrics_summary': {
            'cronbach_alpha': metrics.get('cronbach_alpha'),
            'efa_factors': metrics.get('efa', {}).get('n_factors_final'),
            'convergent_correlations': metrics.get('convergent_validity', {})
        }
    }

    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)
    logger.info(f"Updated modeling_log.yaml at {log_path}")

def main():
    """Main execution for T020, T021, T022."""
    logger.info("Starting Feature Engineering (T020, T021, T022)...")

    config = get_config()
    input_path = get_data_path(config['paths']['cleaned_data'])
    output_path = get_data_path(config['paths']['processed_data']) / 'engineered_data.csv'
    results_dir = get_data_path(config['paths']['results_dir'])
    log_path = get_data_path(config['paths']['modeling_log'])

    # Ensure directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(results_dir).mkdir(parents=True, exist_ok=True)

    # Load Data
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded cleaned data from {input_path} ({len(df)} rows)")
    except FileNotFoundError:
        logger.error(f"Cleaned data not found at {input_path}. Run T014 first.")
        sys.exit(1)

    # T020: Create adoption_binary
    df = create_adoption_binary(df)

    # T021: Create engagement_score
    df = create_engagement_score(df)

    # T022: Reliability and Validity
    # Identify columns again for the analysis functions
    practice_cols = identify_practice_columns(df)
    proxy_cols = select_engagement_proxies(df)

    validity_metrics = calculate_reliability_and_validity(df, practice_cols, proxy_cols)

    # Save validity metrics to results/validity_metrics.yaml
    validity_file = Path(results_dir) / 'validity_metrics.yaml'
    with open(validity_file, 'w') as f:
        yaml.dump(validity_metrics, f, default_flow_style=False)
    logger.info(f"Saved validity metrics to {validity_file}")

    # Update modeling_log.yaml
    update_modeling_log(validity_metrics, log_path)

    # Save engineered data
    df.to_csv(output_path, index=False)
    logger.info(f"Saved engineered data to {output_path}")
    logger.info("Feature engineering complete.")

if __name__ == '__main__':
    main()

"""
Feature Engineering for Sustainable Agriculture Adoption Study (T020, T021, T022).

Implements:
1. Creation of adoption_binary (T020)
2. Construction of engagement_score (T021)
3. Reliability (Cronbach's alpha) and Validity (EFA, Convergent) analysis (T022)

Outputs:
- data/processed/engineered_data.csv
- results/validity_metrics.yaml
- updates modeling_log.yaml
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.stats.reliability as sm_reliability
import yaml
from factor_analyzer import FactorAnalyzer
from scipy.stats import pearsonr

# Import config and logging utilities
sys.path.insert(0, str(Path(__file__).parent))
from config import get_config
from logging_config import get_logger, log_operation, update_log_section

# Configure logger
logger = get_logger("feature_engineering")

# --- T020: Adoption Binary ---

def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns representing sustainable agricultural practices."""
    # Heuristic: look for columns with 'practice' or specific known names
    # In a real scenario, these would be mapped from the data schema
    practice_keywords = ['practice_', 'sustainable_', 'crop_diversity', 'irrigation_efficient', 'organic_fertilizer', 'conservation_tillage']
    cols = []
    for col in df.columns:
        if any(kw in col.lower() for kw in practice_keywords):
            cols.append(col)
    # Fallback if no specific keywords found but binary columns exist
    if not cols:
        binary_cols = [c for c in df.columns if df[c].dtype in ['bool', 'int8', 'int16'] and df[c].nunique() == 2]
        # Filter out obvious non-practice columns
        exclude = ['adoption_binary', 'id', 'respondent_id', 'year']
        cols = [c for c in binary_cols if not any(e in c.lower() for e in exclude)]
    return cols

def create_adoption_binary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a binary indicator for sustainable-practice adoption.
    1 if ANY sustainable practice reported, 0 otherwise.
    """
    practice_cols = identify_practice_columns(df)
    if not practice_cols:
        logger.warning("No sustainable practice columns found. Creating adoption_binary based on 'adoption' column if present.")
        if 'adoption' in df.columns:
            df['adoption_binary'] = (df['adoption'] > 0).astype(int)
        else:
            # Fallback: assume all 0 if no data (should not happen with valid input)
            df['adoption_binary'] = 0
        return df

    # Check if any practice is reported (assuming 1 = adopted, 0 = not)
    # Handle NaNs by treating as 0 (not adopted) for the sum
    df['adoption_binary'] = df[practice_cols].fillna(0).max(axis=1).astype(int)
    logger.info(f"Created adoption_binary based on {len(practice_cols)} practice columns.")
    return df

# --- T021: Engagement Score ---

def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """Select proxy variables for community engagement."""
    # Priority order based on FR-011
    priority_proxies = [
        'community_membership', 'extension_contact', 'collective_action', 
        'knowledge_exchange', 'group_participation', 'training_attended'
    ]
    available = [p for p in priority_proxies if p in df.columns]
    
    # Fallback mechanism if top-priority proxies are absent
    if not available:
        # Look for generic engagement-like columns
        fallback_keywords = ['engage', 'member', 'group', 'training', 'contact', 'particip']
        fallback_cols = [c for c in df.columns if any(k in c.lower() for k in fallback_keywords)]
        available = fallback_cols[:4] # Take up to 4 fallbacks
        if available:
            logger.warning(f"Top priority proxies missing. Using fallback columns: {available}")
        else:
            logger.error("No engagement proxy columns found.")
    
    return available

def create_engagement_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct engagement_score using weighted sum or equal-weight average.
    """
    proxies = select_engagement_proxies(df)
    if not proxies:
        logger.warning("No engagement proxies found. Creating dummy score of 0.")
        df['engagement_score'] = 0.0
        return df

    # Normalize columns to 0-1 range if they are not already (simple min-max)
    # Assuming inputs are ordinal or binary. If continuous, we might need z-score.
    # For this implementation, we assume they are on comparable scales (0-1 or 1-5).
    # We'll use a simple mean of available proxies, handling NaNs.
    
    score_cols = df[proxies].copy()
    # Simple imputation with 0 for missing engagement (conservative)
    score_cols = score_cols.fillna(0)
    
    df['engagement_score'] = score_cols.mean(axis=1)
    logger.info(f"Created engagement_score using {len(proxies)} proxies: {proxies}")
    return df

# --- T022: Reliability and Validity Analysis ---

def calculate_cronbach_alpha(df: pd.DataFrame, proxy_columns: List[str]) -> float:
    """
    Calculate Cronbach's Alpha for the selected proxy columns.
    Uses statsmodels for reliability analysis.
    """
    if len(proxy_columns) < 2:
        logger.warning("Not enough columns for Cronbach's alpha.")
        return 0.0

    data = df[proxy_columns].dropna(how='all')
    if data.shape[0] < 10:
        logger.warning("Sample size too small for reliable alpha calculation.")
        return 0.0

    try:
        # statsmodels alpha expects columns as rows or items as columns?
        # sm_reliability.cronbach_alpha expects items (columns) and returns (alpha, std_err)
        alpha, _ = sm_reliability.cronbach_alpha(data)
        return float(alpha)
    except Exception as e:
        logger.warning(f"Could not calculate Cronbach's alpha: {e}")
        return 0.0

def perform_efa(df: pd.DataFrame, proxy_columns: List[str], n_factors: Optional[int] = None) -> Dict[str, Any]:
    """
    Conduct Exploratory Factor Analysis (EFA).
    - Extraction: Principal Axis Factoring (method='uls' in factor_analyzer)
    - Rotation: Varimax (rotation='varimax')
    - Retention: Kaiser's rule (eigenvalues > 1) if n_factors not specified
    """
    if len(proxy_columns) < 2:
        return {"error": "Not enough variables for EFA"}

    data = df[proxy_columns].dropna()
    if data.shape[0] < 10:
        return {"error": "Sample size too small for EFA"}

    try:
        # Determine number of factors using Kaiser's rule (eigenvalues > 1)
        # First, fit without rotation to get eigenvalues
        fa_temp = FactorAnalyzer(n_factors=len(proxy_columns), method='uls', rotation=None)
        fa_temp.fit(data)
        eigenvalues = fa_temp.get_eigenvalues()
        
        # Kaiser's rule: keep factors with eigenvalue > 1
        if n_factors is None:
            n_factors = sum(eigenvalues > 1)
            if n_factors == 0:
                n_factors = 1 # Force at least one if all are < 1 but > 0
        
        logger.info(f"EFA: Selected {n_factors} factors based on Kaiser's rule (eigenvalues > 1).")
        
        # Fit final model
        fa = FactorAnalyzer(n_factors=n_factors, method='uls', rotation='varimax')
        fa.fit(data)
        
        loadings = fa.loadings
        communalities = fa.get_communalities()
        eigenvalues_final = fa.get_eigenvalues()
        
        return {
            "n_factors": n_factors,
            "loadings": loadings.tolist(),
            "communalities": communalities.tolist(),
            "eigenvalues": eigenvalues_final[0].tolist(), # Eigenvalues after rotation
            "variance_explained": (eigenvalues_final[1] / len(proxy_columns) * 100).tolist()
        }
    except Exception as e:
        logger.error(f"EFA failed: {e}")
        return {"error": str(e)}

def check_convergent_validity(df: pd.DataFrame, proxy_columns: List[str]) -> Dict[str, Any]:
    """
    Perform convergent validity check by correlating engagement_score with
    theoretically related constructs (e.g., 'knowledge_score', 'access_to_credit').
    """
    # Define theoretical constructs to correlate with
    related_constructs = ['knowledge_score', 'access_to_credit', 'farm_income', 'years_farming']
    available_constructs = [c for c in related_constructs if c in df.columns]
    
    if 'engagement_score' not in df.columns:
        return {"error": "engagement_score not found"}

    results = {}
    for construct in available_constructs:
        try:
            # Drop rows with NaN in either column
            valid_data = df[['engagement_score', construct]].dropna()
            if len(valid_data) > 5:
                corr, p_val = pearsonr(valid_data['engagement_score'], valid_data[construct])
                results[construct] = {
                    "correlation": float(corr),
                    "p_value": float(p_val),
                    "n": len(valid_data)
                }
            else:
                results[construct] = {"error": "Insufficient data"}
        except Exception as e:
            results[construct] = {"error": str(e)}

    return results

def calculate_reliability_and_validity(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the calculation of reliability and validity metrics.
    """
    proxies = select_engagement_proxies(df)
    
    # 1. Cronbach's Alpha
    alpha = calculate_cronbach_alpha(df, proxies)
    
    # 2. EFA
    efa_results = perform_efa(df, proxies)
    
    # 3. Convergent Validity
    convergent_results = check_convergent_validity(df, proxies)
    
    return {
        "cronbach_alpha": alpha,
        "efa": efa_results,
        "convergent_validity": convergent_results,
        "proxy_columns_used": proxies
    }

def save_validity_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Serialize metrics to YAML."""
    # Ensure directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to python types for YAML serialization
    def convert(obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, dict): return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list): return [convert(i) for i in obj]
        return obj
    
    clean_metrics = convert(metrics)
    
    with open(output_path, 'w') as f:
        yaml.dump(clean_metrics, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Validity metrics saved to {output_path}")

def update_modeling_log(status: str, metrics: Dict[str, Any]) -> None:
    """Update modeling_log.yaml with validity analysis status."""
    config = get_config()
    log_path = config.get('modeling_log_path', 'modeling_log.yaml')
    
    # Load existing log or create new
    log_data = {}
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    
    # Update section
    if 'validity_analysis' not in log_data:
        log_data['validity_analysis'] = {}
    
    log_data['validity_analysis']['convergent_validity_status'] = status
    log_data['validity_analysis']['timestamp'] = datetime.now().isoformat()
    log_data['validity_analysis']['cronbach_alpha'] = metrics.get('cronbach_alpha')
    
    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)
    logger.info(f"Modeling log updated at {log_path}")

@log_operation("feature_engineering_main")
def main() -> None:
    """Main entry point for feature engineering."""
    config = get_config()
    
    # Paths
    input_path = Path(config.get('cleaned_data_path', 'data/processed/cleaned_data.csv'))
    output_dir = Path(config.get('processed_data_dir', 'data/processed'))
    output_path = output_dir / 'engineered_data.csv'
    validity_metrics_path = Path(config.get('results_dir', 'results')) / 'validity_metrics.yaml'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T014 first.")
    
    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_csv(input_path)
    
    # T020: Create adoption_binary
    df = create_adoption_binary(df)
    
    # T021: Create engagement_score
    df = create_engagement_score(df)
    
    # T022: Calculate Reliability and Validity
    metrics = calculate_reliability_and_validity(df, config)
    
    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Engineered data saved to {output_path}")
    
    # Save validity metrics
    save_validity_metrics(metrics, str(validity_metrics_path))
    
    # Update modeling log
    status = "completed" if metrics.get('cronbach_alpha', 0) > 0 else "partial"
    if metrics.get('efa', {}).get('error'):
        status = "efa_failed"
    update_modeling_log(status, metrics)

if __name__ == "__main__":
    main()

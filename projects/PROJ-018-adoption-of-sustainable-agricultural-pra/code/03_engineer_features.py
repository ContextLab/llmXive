"""Feature Engineering for Sustainable Agricultural Practices Adoption Study.

This module handles the creation of derived variables:
1. adoption_binary: Binary indicator of sustainable practice adoption.
2. engagement_score: Composite index of community engagement.
3. Reliability (Cronbach's Alpha) and Validity (EFA, Convergent) checks.

Dependencies:
- pandas
- numpy
- statsmodels
- factor_analyzer (>=0.5.0)
- scipy
- pyyaml
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
from scipy.stats import pearsonr
from statsmodels.stats.inter_rater import cohens_kappa

# Import shared utilities from project root
# Note: We assume this script runs from project root or code/ is in path
try:
    from config import get_config, set_random_seed
    from logging_config import update_log_section, initialize_modeling_log
except ImportError:
    # Fallback for direct execution in isolated environments
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, set_random_seed
    from logging_config import update_log_section, initialize_modeling_log


class FeatureEngineeringError(Exception):
    """Custom exception for feature engineering pipeline errors."""
    pass


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    return get_config()


def load_cleaned_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the cleaned dataset from the processed directory."""
    if input_path is None:
        config = get_config()
        base_dir = Path(config.get("project_root", "."))
        processed_path = base_dir / config.get("processed_data_path", "data/processed")
        input_path = processed_path / "cleaned_data.csv"

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found at {input_path}")

    df = pd.read_csv(input_path)
    logging.info(f"Loaded {len(df)} records from {input_path}")
    return df


def identify_practice_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns representing sustainable agricultural practices.

    Heuristics:
    - Look for columns containing 'practice', 'sustain', 'tech', 'method'
    - Exclude known non-practice columns (demographics, IDs)
    """
    exclude_cols = {
        'id', 'respondent_id', 'country', 'region', 'age', 'education',
        'farm_size', 'credit_access', 'income', 'engagement_score',
        'adoption_binary', 'timestamp', 'date'
    }
    practice_keywords = ['practice', 'sustain', 'tech', 'method', 'crop', 'soil', 'water', 'seed']

    practice_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in exclude_cols:
            continue
        if any(kw in col_lower for kw in practice_keywords):
            practice_cols.append(col)

    # If no keyword matches, assume binary columns with specific naming convention
    if not practice_cols:
        # Fallback: look for binary columns (0/1) that might be practices
        # This is a last resort; real data should have named practice columns
        logging.warning("No practice columns identified by keywords. Checking for binary columns.")
        for col in df.columns:
            if col in exclude_cols:
                continue
            if df[col].dtype in ['int64', 'float64']:
                unique_vals = df[col].unique()
                if set(unique_vals).issubset({0, 1, np.nan}):
                    practice_cols.append(col)

    return practice_cols


def create_adoption_binary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a binary adoption indicator.

    Logic:
    - adoption_binary = 1 if ANY sustainable practice column has a value >= 1 (or True)
    - adoption_binary = 0 otherwise
    """
    practice_cols = identify_practice_columns(df)

    if not practice_cols:
        logging.warning("No practice columns found to create adoption_binary. Creating dummy column.")
        df['adoption_binary'] = 0
        return df

    # Convert practice columns to numeric, coercing errors to NaN
    df_practices = df[practice_cols].apply(pd.to_numeric, errors='coerce')

    # Define adoption as having at least one positive practice
    # Assuming 1 means "adopted", 0 means "not adopted"
    # If data uses Likert scales (1-5), we might consider >= 3 as adoption,
    # but for binary "adoption", we assume 1 = adopted.
    # To be safe, we check if any value > 0 (excluding NaN)
    adoption_mask = (df_practices > 0).any(axis=1)

    df['adoption_binary'] = adoption_mask.astype(int)

    logging.info(f"Created adoption_binary. Positive cases: {df['adoption_binary'].sum()}")
    return df


def select_engagement_proxies(df: pd.DataFrame) -> List[str]:
    """Select proxy variables for community engagement.

    Expected proxies:
    - membership (in coops/groups)
    - extension (contact with extension officers)
    - collective_action (participation in collective actions)
    - knowledge_exchange (sharing knowledge with peers)
    """
    proxy_keywords = ['membership', 'extension', 'collective', 'knowledge', 'exchange', 'group', 'coop', 'training']
    exclude_cols = {'id', 'age', 'education', 'farm_size', 'credit', 'income', 'adoption_binary', 'engagement_score'}

    proxy_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in exclude_cols:
            continue
        if any(kw in col_lower for kw in proxy_keywords):
            proxy_cols.append(col)

    return proxy_cols


def create_engagement_score(df: pd.DataFrame) -> pd.DataFrame:
    """Create a composite engagement score.

    Method:
    - Equal-weighted average of standardized proxy variables.
    - Fallback: If fewer than 2 proxies, use the first available or a dummy.
    """
    proxy_cols = select_engagement_proxies(df)

    if len(proxy_cols) < 1:
        logging.warning("No engagement proxies found. Creating dummy engagement_score.")
        df['engagement_score'] = 0.0
        return df

    # Ensure proxies are numeric
    df_proxies = df[proxy_cols].apply(pd.to_numeric, errors='coerce')

    # Standardize (Z-score) each proxy
    # Use (x - mean) / std
    df_standardized = (df_proxies - df_proxies.mean()) / df_proxies.std()

    # Handle cases where std is 0 (constant column)
    df_standardized = df_standardized.fillna(0)

    # Compute mean score
    df['engagement_score'] = df_standardized.mean(axis=1)

    logging.info(f"Created engagement_score from {len(proxy_cols)} proxies: {proxy_cols}")
    return df


def calculate_cronbach_alpha(df: pd.DataFrame, item_cols: List[str]) -> float:
    """Calculate Cronbach's Alpha for a set of items.

    Args:
        df: DataFrame containing the items.
        item_cols: List of column names representing items in the scale.

    Returns:
        Cronbach's Alpha coefficient.
    """
    if len(item_cols) < 2:
        logging.warning("Need at least 2 items to calculate Cronbach's Alpha.")
        return 0.0

    data = df[item_cols].apply(pd.to_numeric, errors='coerce').dropna()

    if data.empty:
        return 0.0

    # Formula: alpha = (k / (k-1)) * (1 - sum(var_i) / var_total)
    k = len(item_cols)
    var_items = data.var(axis=0, ddof=1)
    var_total = data.var(axis=0, ddof=1).sum() # Sum of variances? No, var of sum
    # Correct formula: var_total is variance of the sum of items
    sum_items = data.sum(axis=1)
    var_total_correct = sum_items.var(ddof=1)

    if var_total_correct == 0:
        return 0.0

    alpha = (k / (k - 1)) * (1 - var_items.sum() / var_total_correct)
    return float(alpha)


def perform_efa(df: pd.DataFrame, item_cols: List[str], max_factors: int = 5) -> Dict[str, Any]:
    """Perform Exploratory Factor Analysis (EFA).

    Configuration:
    - Extraction: Principal Axis Factoring (PAF)
    - Rotation: Varimax
    - Retention: Kaiser's rule (eigenvalues > 1)

    Args:
        df: DataFrame with items.
        item_cols: Columns to analyze.
        max_factors: Maximum factors to attempt (for initial check).

    Returns:
        Dictionary with factor loadings, eigenvalues, factors retained.
    """
    if len(item_cols) < 2:
        logging.warning("Need at least 2 items for EFA.")
        return {"factors_retained": 0, "loadings": {}, "eigenvalues": []}

    data = df[item_cols].apply(pd.to_numeric, errors='coerce').dropna()

    if data.empty:
        return {"factors_retained": 0, "loadings": {}, "eigenvalues": []}

    # Calculate correlation matrix
    corr_matrix = data.corr()

    # Compute initial eigenvalues to determine factors to retain (Kaiser's rule)
    eigenvalues = np.linalg.eigvals(corr_matrix).real
    eigenvalues = sorted(eigenvalues, reverse=True)
    factors_to_retain = sum(e > 1 for e in eigenvalues)

    # Ensure at least 1 factor if eigenvalues > 1 exist, else 1
    if factors_to_retain == 0:
        factors_to_retain = 1

    # Limit to max_factors or number of items
    n_factors = min(factors_to_retain, len(item_cols) - 1, max_factors)
    if n_factors < 1:
        n_factors = 1

    try:
        # Use factor_analyzer with PAF extraction
        # method='pa' corresponds to Principal Axis Factoring
        fa = FactorAnalyzer(n_factors=n_factors, rotation='varimax', method='pa')
        # fit() handles the data
        fa.fit(data.values)

        # Get eigenvalues from the fitted model (communalities + unique variances)
        # Note: fa.get_eigenvalues() returns (ev_before, ev_after)
        ev_before, ev_after = fa.get_eigenvalues()
        
        # Re-calculate retained based on ev_before (initial eigenvalues)
        retained_count = sum(e > 1 for e in ev_before)
        if retained_count == 0:
            retained_count = 1
        retained_count = min(retained_count, len(item_cols) - 1)

        loadings = fa.loadings
        
        # Format loadings for YAML serialization
        loadings_dict = {}
        for i, col in enumerate(item_cols):
            loadings_dict[col] = [float(val) for val in loadings[i, :]]

        return {
            "factors_retained": int(retained_count),
            "eigenvalues": [float(e) for e in ev_before],
            "loadings": loadings_dict,
            "method": "Principal Axis Factoring",
            "rotation": "Varimax"
        }

    except Exception as e:
        logging.error(f"EFA failed: {str(e)}")
        # Fallback: return empty results if EFA fails
        return {
            "factors_retained": 0,
            "eigenvalues": [],
            "loadings": {},
            "error": str(e),
            "method": "Principal Axis Factoring",
            "rotation": "Varimax"
        }


def check_convergent_validity(df: pd.DataFrame, score_col: str, related_cols: List[str]) -> Dict[str, Any]:
    """Check convergent validity by correlating the score with related constructs.

    Args:
        df: DataFrame.
        score_col: The engagement score column.
        related_cols: Columns theoretically related to engagement.

    Returns:
        Dictionary with correlations and validity status.
    """
    results = {}
    valid_status = True

    for col in related_cols:
        if col not in df.columns:
            continue
        
        # Calculate correlation
        corr, p_val = pearsonr(df[score_col], df[col])
        if np.isnan(corr):
            corr = 0.0
            p_val = 1.0
        
        results[col] = {
            "correlation": float(corr),
            "p_value": float(p_val)
        }

        # Convergent validity typically expects significant positive correlation
        if p_val > 0.05 or corr < 0.3:
            valid_status = False

    return {
        "correlations": results,
        "passed": valid_status,
        "threshold": "p < 0.05 and r > 0.3"
    }


def calculate_reliability_and_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """Main orchestration for reliability and validity checks.

    Steps:
    1. Calculate Cronbach's Alpha for engagement proxies.
    2. Perform EFA on engagement proxies.
    3. Check convergent validity (correlation with adoption or other constructs).
    """
    # 1. Cronbach's Alpha
    proxy_cols = select_engagement_proxies(df)
    alpha = 0.0
    if len(proxy_cols) >= 2:
        alpha = calculate_cronbach_alpha(df, proxy_cols)

    # 2. EFA
    efa_results = {}
    if len(proxy_cols) >= 2:
        efa_results = perform_efa(df, proxy_cols)

    # 3. Convergent Validity
    # Correlate engagement_score with adoption_binary (theoretically related)
    # Or other related constructs if available
    related_constructs = ['adoption_binary', 'income', 'education'] # Example
    convergent = check_convergent_validity(df, 'engagement_score', related_constructs)

    return {
        "cronbach_alpha": float(alpha),
        "efa": efa_results,
        "convergent_validity": convergent
    }


def save_validity_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save validity metrics to a YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
    logging.info(f"Saved validity metrics to {output_path}")


def update_modeling_log(metrics: Dict[str, Any], log_path: Path) -> None:
    """Update the modeling_log.yaml with validity analysis results."""
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        log_data = {}

    if 'validity_analysis' not in log_data:
        log_data['validity_analysis'] = {}

    log_data['validity_analysis']['cronbach_alpha'] = metrics.get('cronbach_alpha')
    
    efa_data = metrics.get('efa', {})
    if efa_data:
        log_data['validity_analysis']['efa_factors_retained'] = efa_data.get('factors_retained')
        log_data['validity_analysis']['efa_method'] = efa_data.get('method')
        log_data['validity_analysis']['efa_rotation'] = efa_data.get('rotation')

    conv_data = metrics.get('convergent_validity', {})
    if conv_data:
        log_data['validity_analysis']['convergent_validity_status'] = conv_data.get('passed', False)
        log_data['validity_analysis']['convergent_validity_details'] = conv_data.get('correlations', {})

    with open(log_path, 'w', encoding='utf-8') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    
    logging.info(f"Updated modeling log at {log_path}")


def export_engineered_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save the engineered dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Saved engineered data to {output_path}")


def main():
    """Main entry point for feature engineering."""
    parser = argparse.ArgumentParser(description="Feature Engineering Pipeline")
    parser.add_argument("--input", type=str, help="Path to cleaned data CSV")
    parser.add_argument("--output", type=str, help="Path to save engineered data CSV")
    parser.add_argument("--metrics", type=str, help="Path to save validity metrics YAML")
    args = parser.parse_args()

    # Initialize logging
    initialize_modeling_log()
    logging.info("Starting feature engineering pipeline.")

    try:
        config = get_config()
        base_dir = Path(config.get("project_root", "."))
        
        # Paths
        input_path = Path(args.input) if args.input else (base_dir / config.get("processed_data_path", "data/processed") / "cleaned_data.csv")
        output_path = Path(args.output) if args.output else (base_dir / config.get("processed_data_path", "data/processed") / "engineered_data.csv")
        metrics_path = Path(args.metrics) if args.metrics else (base_dir / config.get("results_path", "results") / "validity_metrics.yaml")
        log_path = base_dir / "modeling_log.yaml"

        # 1. Load Data
        df = load_cleaned_data(input_path)

        # 2. Create Adoption Binary
        df = create_adoption_binary(df)

        # 3. Create Engagement Score
        df = create_engagement_score(df)

        # 4. Reliability and Validity Checks
        metrics = calculate_reliability_and_validity(df)

        # 5. Save Artifacts
        save_validity_metrics(metrics, metrics_path)
        update_modeling_log(metrics, log_path)
        export_engineered_data(df, output_path)

        logging.info("Feature engineering pipeline completed successfully.")
        update_log_section("feature_engineering", {"status": "completed", "timestamp": datetime.utcnow().isoformat()})

    except Exception as e:
        logging.error(f"Feature engineering pipeline failed: {str(e)}")
        update_log_section("feature_engineering", {"status": "failed", "error": str(e), "timestamp": datetime.utcnow().isoformat()})
        raise FeatureEngineeringError(str(e))


if __name__ == "__main__":
    main()

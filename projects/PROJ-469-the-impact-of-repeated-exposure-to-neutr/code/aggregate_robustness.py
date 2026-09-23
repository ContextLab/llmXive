"""
Aggregation pipeline for robustness metrics.
Consolidates bootstrap, alpha sweep, covariate, and binary model results.
"""
import os
import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
from config_manager import get_results_path, get_config
from logging_config import get_logger

logger = get_logger(__name__)

def load_csv_safely(path: Path) -> Optional[pd.DataFrame]:
    """Load a CSV file safely, returning None if not found."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return None

def extract_bootstrap_metrics(bootstrap_json_path: Path) -> Dict[str, Any]:
    """Extract key metrics from bootstrap results JSON."""
    if not bootstrap_json_path.exists():
        return {}
    try:
        with open(bootstrap_json_path, 'r') as f:
            data = json.load(f)
        return {
            "bootstrap_mean": data.get("mean", None),
            "bootstrap_std": data.get("std", None),
            "bootstrap_ci_lower": data.get("ci_lower", None),
            "bootstrap_ci_upper": data.get("ci_upper", None),
            "converged_pct": data.get("converged_pct", None)
        }
    except Exception as e:
        logger.error(f"Error extracting bootstrap metrics: {e}")
        return {}

def extract_alpha_sweep_metrics(alpha_csv_path: Path) -> pd.DataFrame:
    """Load alpha sweep results."""
    return load_csv_safely(alpha_csv_path)

def extract_covariate_metrics(covariate_csv_path: Path) -> Optional[pd.DataFrame]:
    """Load covariate model results."""
    return load_csv_safely(covariate_csv_path)

def extract_binary_model_metrics(binary_csv_path: Path) -> Optional[pd.DataFrame]:
    """Load binary model results."""
    return load_csv_safely(binary_csv_path)

def aggregate_robustness_metrics(
    bootstrap_metrics: Dict,
    alpha_df: Optional[pd.DataFrame],
    covariate_df: Optional[pd.DataFrame],
    binary_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    Aggregate all robustness metrics into a single summary DataFrame.
    """
    rows = []
    
    # Bootstrap metrics
    for key, value in bootstrap_metrics.items():
        rows.append({"metric": key, "value": value, "source": "bootstrap"})
        
    # Alpha sweep
    if alpha_df is not None:
        for _, row in alpha_df.iterrows():
            rows.append({
                "metric": f"alpha_{row['alpha']}_significant",
                "value": 1 if row['is_significant'] else 0,
                "source": "alpha_sweep"
            })
            
    # Covariate comparison
    if covariate_df is not None:
        interaction_row = covariate_df[covariate_df['term'] == 'news_exposure_z:political_ideology']
        if not interaction_row.empty:
            rows.append({
                "metric": "covariate_interaction_coef",
                "value": interaction_row['estimate'].values[0],
                "source": "covariate_model"
            })
            rows.append({
                "metric": "covariate_interaction_pval",
                "value": interaction_row['p_value'].values[0],
                "source": "covariate_model"
            })
            
    # Binary model comparison
    if binary_df is not None:
        interaction_row = binary_df[binary_df['term'] == 'news_exposure_z:ideology_binary']
        if not interaction_row.empty:
            rows.append({
                "metric": "binary_interaction_coef",
                "value": interaction_row['estimate'].values[0],
                "source": "binary_model"
            })
            rows.append({
                "metric": "binary_interaction_pval",
                "value": interaction_row['p_value'].values[0],
                "source": "binary_model"
            })
            
    return pd.DataFrame(rows)

def run_aggregation_pipeline() -> pd.DataFrame:
    """Run the full aggregation pipeline."""
    results_dir = get_results_path()
    
    # Load sources
    bootstrap_metrics = extract_bootstrap_metrics(results_dir / "bootstrap_results.json")
    alpha_df = extract_alpha_sweep_metrics(results_dir / "alpha_sweep.csv")
    covariate_df = extract_covariate_metrics(results_dir / "covariate_model.csv")
    binary_df = extract_binary_model_metrics(results_dir / "binary_model.csv")
    
    # Aggregate
    aggregated_df = aggregate_robustness_metrics(bootstrap_metrics, alpha_df, covariate_df, binary_df)
    
    # Save
    output_path = results_dir / "robustness_metrics.csv"
    aggregated_df.to_csv(output_path, index=False)
    logger.info(f"Aggregated robustness metrics saved to {output_path}")
    
    return aggregated_df

def main():
    """CLI entry point."""
    run_aggregation_pipeline()

if __name__ == "__main__":
    main()
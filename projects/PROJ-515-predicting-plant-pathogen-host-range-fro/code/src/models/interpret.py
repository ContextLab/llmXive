import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from loguru import logger
from src.utils.logging import get_logger
from src.config import Paths, Thresholds, load_config_from_json

def calculate_shap_values(model, data: pd.DataFrame, feature_names: List[str]) -> np.ndarray:
    """
    Calculate SHAP values for a given model and dataset.
    
    Args:
        model: Trained scikit-learn model
        data: Feature matrix (pandas DataFrame)
        feature_names: List of feature names
        
    Returns:
        np.ndarray: SHAP values matrix
    """
    try:
        import shap
        logger.info("Initializing SHAP explainer...")
        explainer = shap.LinearExplainer(model, data)
        shap_values = explainer.shap_values(data)
        logger.info(f"SHAP values calculated. Shape: {shap_values.shape}")
        return shap_values
    except Exception as e:
        logger.error(f"Error calculating SHAP values: {e}")
        raise

def generate_feature_importance_report(
    shap_values: np.ndarray,
    feature_names: List[str],
    output_path: Path
) -> None:
    """
    Generate a feature importance report based on SHAP values.
    
    Args:
        shap_values: SHAP values matrix
        feature_names: List of feature names
        output_path: Path to save the report (CSV)
    """
    logger.info(f"Generating feature importance report at {output_path}")
    
    # Calculate mean absolute SHAP value for each feature
    mean_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Create DataFrame
    importance_df = pd.DataFrame({
        'feature_name': feature_names,
        'mean_abs_shap': mean_shap
    })
    
    # Sort by importance
    importance_df = importance_df.sort_values(by='mean_abs_shap', ascending=False)
    
    # Save to CSV
    importance_df.to_csv(output_path, index=False)
    logger.info(f"Feature importance report saved to {output_path}")

def run_shap_analysis(
    model,
    data: pd.DataFrame,
    feature_names: List[str],
    output_dir: Path
) -> Dict[str, Any]:
    """
    Run full SHAP analysis pipeline.
    
    Args:
        model: Trained model
        data: Feature matrix
        feature_names: List of feature names
        output_dir: Directory to save results
        
    Returns:
        Dict containing analysis results
    """
    logger.info("Starting SHAP analysis...")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate SHAP values
    shap_values = calculate_shap_values(model, data, feature_names)
    
    # Generate feature importance report
    importance_path = output_dir / "feature_importance.csv"
    generate_feature_importance_report(shap_values, feature_names, importance_path)
    
    return {
        "shap_values": shap_values,
        "importance_path": str(importance_path),
        "feature_names": feature_names
    }

def generate_bias_awareness_report(
    interactions_path: Union[str, Path],
    output_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Generate a bias-awareness report analyzing interaction distribution across pathogens.
    
    Logic:
    1. Load interaction data
    2. Calculate interaction count per pathogen
    3. Check if top 10 pathogens account for >80% of total interactions
    4. Output report to JSON
    
    Args:
        interactions_path: Path to interactions CSV file
        output_path: Path to save the bias awareness report (JSON)
        
    Returns:
        Dict containing the bias analysis results
    """
    logger.info(f"Generating bias-awareness report from {interactions_path}")
    
    # Load interactions
    if isinstance(interactions_path, str):
        interactions_path = Path(interactions_path)
    if isinstance(output_path, str):
        output_path = Path(output_path)
    
    if not interactions_path.exists():
        raise FileNotFoundError(f"Interactions file not found: {interactions_path}")
    
    df = pd.read_csv(interactions_path)
    
    # Ensure we have the right columns (pathogen column name might vary)
    # Assuming 'pathogen_id' or similar based on standard data model
    pathogen_col = None
    possible_cols = ['pathogen_id', 'pathogen', 'organism_id', 'source_organism']
    for col in possible_cols:
        if col in df.columns:
            pathogen_col = col
            break
    
    if pathogen_col is None:
        # Fallback: use first column if it looks like an ID
        logger.warning(f"Could not find standard pathogen column, using first column: {df.columns[0]}")
        pathogen_col = df.columns[0]
    
    # Calculate interaction count per pathogen
    interaction_counts = df[pathogen_col].value_counts()
    total_interactions = len(df)
    
    # Get top 10 pathogens
    top_10_counts = interaction_counts.head(10).sum()
    top_10_percentage = (top_10_counts / total_interactions) * 100 if total_interactions > 0 else 0.0
    
    # Determine if bias flag is set
    bias_flag = top_10_percentage > 80.0
    
    # Prepare report data
    report = {
        "total_interactions": int(total_interactions),
        "unique_pathogens": int(len(interaction_counts)),
        "top_10_interactions": int(top_10_counts),
        "top_10_percentage": float(round(top_10_percentage, 2)),
        "bias_flag": bias_flag,
        "threshold_percentage": 80.0,
        "top_10_pathogens": interaction_counts.head(10).to_dict(),
        "methodology": "Calculated interaction count per pathogen. Flagged if top 10 pathogens account for >80% of total interactions."
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Bias-awareness report saved to {output_path}")
    logger.info(f"Top 10 pathogens account for {top_10_percentage:.2f}% of interactions. Bias flag: {bias_flag}")
    
    return report

def main() -> None:
    """
    Main entry point for the interpret module.
    Runs SHAP analysis and bias awareness report generation.
    """
    logger.info("Starting interpret module main...")
    
    # Load configuration
    config = load_config_from_json()
    paths = Paths(config)
    thresholds = Thresholds(config)
    
    # Ensure data directories exist
    paths.data_processed.mkdir(parents=True, exist_ok=True)
    paths.data_reports.mkdir(parents=True, exist_ok=True)
    
    # Example usage for bias awareness (would be called from CLI or pipeline)
    interactions_file = paths.data_raw / "interactions_merged.csv"
    bias_report_file = paths.data_reports / "bias_awareness.json"
    
    if interactions_file.exists():
        try:
            generate_bias_awareness_report(interactions_file, bias_report_file)
        except Exception as e:
            logger.error(f"Failed to generate bias awareness report: {e}")
    else:
        logger.warning(f"Interactions file not found at {interactions_file}. Skipping bias awareness report.")
    
    logger.info("Interpret module completed.")

if __name__ == "__main__":
    main()
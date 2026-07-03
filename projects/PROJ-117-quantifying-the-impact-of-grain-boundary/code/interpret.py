"""
Interpretability and sensitivity analysis for grain boundary diffusivity model.

This module implements:
1. SHAP value analysis for feature importance
2. Sensitivity analysis on R² threshold
3. Configuration-based threshold justification
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
from sklearn.metrics import r2_score
import xgboost as xgb

# Import from project modules
from utils import setup_logging, set_random_seed
from config.threshold_config import (
    get_r2_threshold,
    get_threshold_justification,
    get_threshold_reference,
    get_threshold_metadata
)

# Configure logging
logger = setup_logging(__name__)

def load_model(model_path: str) -> xgb.XGBRegressor:
    """Load a trained XGBoost model from JSON."""
    model = xgb.XGBRegressor()
    model_path = Path(model_path)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load model from JSON
    with open(model_path, 'r') as f:
        model_dict = json.load(f)
    
    # Reconstruct model from dictionary
    model.set_params(**{k: v for k, v in model_dict.items() 
                      if k in model.get_params()})
    
    # Load booster if available
    if 'booster' in model_dict:
        booster = xgb.Booster()
        booster.load_model(model_path.with_suffix('.json').as_posix())
        model._Booster = booster
    
    return model

def load_data(data_path: str) -> pd.DataFrame:
    """Load processed dataset."""
    data_path = Path(data_path)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def prepare_features(df: pd.DataFrame, target_col: str = 'diffusivity') -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features and target from dataset."""
    # Exclude target and metadata columns
    exclude_cols = ['diffusivity', 'simulation_method', 'potential_id', 'source_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, 'diffusivity']
    
    return X, y

def generate_shap_analysis(model: xgb.XGBRegressor, X: pd.DataFrame, 
                          output_dir: str) -> Dict[str, Any]:
    """Generate SHAP analysis and plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Generating SHAP analysis...")
    
    # Create SHAP explainer
    explainer = shap.Explainer(model, X)
    shap_values = explainer(X)
    
    # Generate summary plot
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig(output_dir / 'shap_summary_bar.png', dpi=150)
    plt.close()
    
    # Generate dot plot
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X, show=False)
    plt.tight_layout()
    plt.savefig(output_dir / 'shap_summary_dot.png', dpi=150)
    plt.close()
    
    # Extract feature importance
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance': np.abs(shap_values.values).mean(axis=0)
    }).sort_values('importance', ascending=False)
    
    # Save feature importance
    importance_path = output_dir / 'feature_importance.csv'
    importance_df.to_csv(importance_path, index=False)
    
    logger.info(f"SHAP analysis saved to {output_dir}")
    
    return {
        'shap_summary_bar': str(output_dir / 'shap_summary_bar.png'),
        'shap_summary_dot': str(output_dir / 'shap_summary_dot.png'),
        'feature_importance': str(importance_path),
        'importance_values': importance_df.to_dict('records')
    }

def perform_sensitivity_analysis(y_true: pd.Series, y_pred: pd.Series,
                                threshold_range: List[float] = None) -> pd.DataFrame:
    """
    Perform sensitivity analysis on R² threshold.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        threshold_range: List of R² thresholds to test. Defaults to [0.5, 0.6, 0.7, 0.8, 0.9]
    
    Returns:
        DataFrame with threshold and pass rate
    """
    if threshold_range is None:
        threshold_range = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    # Calculate R² for the full dataset
    r2 = r2_score(y_true, y_pred)
    
    # Create sensitivity table
    results = []
    for threshold in threshold_range:
        # For a single model, pass rate is 1.0 if r2 >= threshold, else 0.0
        pass_rate = 1.0 if r2 >= threshold else 0.0
        
        results.append({
            'threshold': threshold,
            'pass_rate': pass_rate,
            'r2_score': r2,
            'model_passes': r2 >= threshold
        })
    
    return pd.DataFrame(results)

def generate_threshold_justification_report(output_dir: str) -> Dict[str, Any]:
    """
    Generate a report with the R² threshold justification from configuration.
    
    This function retrieves the threshold value and its justification from
    the configuration file, ensuring the threshold is well-documented and
    traceable to community standards.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get threshold configuration
    threshold = get_r2_threshold()
    justification = get_threshold_justification()
    reference = get_threshold_reference()
    metadata = get_threshold_metadata()
    
    # Create report
    report = {
        'threshold': threshold,
        'justification': justification,
        'reference_document': reference,
        'metadata': metadata,
        'generated_at': pd.Timestamp.now().isoformat()
    }
    
    # Save report
    report_path = output_dir / 'threshold_justification.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Also create a markdown version for documentation
    md_content = f"""# R² Threshold Justification

## Threshold Value
**R² ≥ {threshold}**

## Justification
{justification}

## Reference
This threshold is documented in: {reference}

## Metadata
- Version: {metadata.get('version', 'N/A')}
- Last Updated: {metadata.get('last_updated', 'N/A')}
- Source: {metadata.get('source', 'N/A')}

## Usage
This threshold is used in the sensitivity analysis to determine model pass/fail criteria.
Models achieving R² above this threshold are considered to have robust predictive capability
for grain boundary diffusivity.
"""
    md_path = output_dir / 'threshold_justification.md'
    with open(md_path, 'w') as f:
        f.write(md_content)
    
    logger.info(f"Threshold justification report saved to {output_dir}")
    
    return {
        'json_report': str(report_path),
        'md_report': str(md_path),
        'threshold': threshold,
        'justification': justification
    }

def run_sensitivity_analysis(model_path: str, data_path: str,
                            output_dir: str, threshold_range: List[float] = None) -> Dict[str, Any]:
    """
    Run complete sensitivity analysis pipeline.
    
    Args:
        model_path: Path to trained model
        data_path: Path to processed dataset
        output_dir: Directory for output artifacts
        threshold_range: Optional list of thresholds to test
    
    Returns:
        Dictionary with analysis results
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading model and data...")
    model = load_model(model_path)
    df = load_data(data_path)
    
    # Prepare features
    X, y = prepare_features(df)
    
    # Make predictions
    logger.info("Making predictions...")
    y_pred = model.predict(X)
    
    # Generate threshold justification report
    logger.info("Generating threshold justification report...")
    justification_report = generate_threshold_justification_report(output_dir)
    
    # Perform sensitivity analysis
    logger.info("Performing sensitivity analysis...")
    sensitivity_df = perform_sensitivity_analysis(y, y_pred, threshold_range)
    
    # Save sensitivity table
    sensitivity_path = output_dir / 'threshold_variation_table.csv'
    sensitivity_df.to_csv(sensitivity_path, index=False)
    
    # Generate sensitivity plot
    plt.figure(figsize=(10, 6))
    plt.plot(sensitivity_df['threshold'], sensitivity_df['pass_rate'], 
            'bo-', linewidth=2, markersize=8)
    plt.axhline(y=justification_report['threshold'], color='r', linestyle='--', 
               label=f"Threshold (R² ≥ {justification_report['threshold']})")
    plt.xlabel('R² Threshold')
    plt.ylabel('Pass Rate')
    plt.title('Threshold Sensitivity Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'threshold_sensitivity_plot.png', dpi=150)
    plt.close()
    
    logger.info(f"Sensitivity analysis saved to {output_dir}")
    
    return {
        'sensitivity_table': str(sensitivity_path),
        'sensitivity_plot': str(output_dir / 'threshold_sensitivity_plot.png'),
        'justification_report': justification_report,
        'results': sensitivity_df.to_dict('records')
    }

def main():
    """Main entry point for interpretability analysis."""
    parser = argparse.ArgumentParser(description='Generate SHAP analysis and sensitivity report')
    parser.add_argument('--model', type=str, required=True, 
                     help='Path to trained model JSON')
    parser.add_argument('--data', type=str, required=True,
                     help='Path to processed dataset')
    parser.add_argument('--output', type=str, required=True,
                     help='Output directory for artifacts')
    parser.add_argument('--seed', type=int, default=42,
                     help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Set random seed
    set_random_seed(args.seed)
    
    # Create output directories
    output_dir = Path(args.output)
    figures_dir = output_dir / 'figures'
    reports_dir = output_dir / 'reports'
    figures_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate SHAP analysis
        shap_results = generate_shap_analysis(
            args.model, 
            pd.read_parquet(args.data) if Path(args.data).suffix == '.parquet' 
            else pd.read_csv(args.data),
            figures_dir
        )
        
        # Run sensitivity analysis
        sensitivity_results = run_sensitivity_analysis(
            args.model,
            args.data,
            reports_dir
        )
        
        # Compile final report
        final_report = {
            'shap_analysis': shap_results,
            'sensitivity_analysis': sensitivity_results,
            'threshold_config': {
                'value': get_r2_threshold(),
                'justification': get_threshold_justification(),
                'reference': get_threshold_reference()
            },
            'execution_status': 'completed'
        }
        
        # Save final report
        report_path = reports_dir / 'interpretability_report.json'
        with open(report_path, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Interpretability analysis complete. Report saved to {report_path}")
        
    except Exception as e:
        logger.error(f"Interpretability analysis failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()
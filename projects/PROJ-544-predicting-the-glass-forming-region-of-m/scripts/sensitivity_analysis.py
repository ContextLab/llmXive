"""
Sensitivity analysis for glass-forming region prediction.

Evaluates model performance across atomic size mismatch (δ) values {0.01, 0.05, 0.1}
as required by FR-005.

The research question is: How sensitive is the model's predictive performance to
variations in the atomic size mismatch descriptor?
The method is: Perturb the atomic size mismatch (δ) values in the feature set by
specified factors and re-evaluate the trained model's ROC-AUC, precision, and recall.
References: This analysis supports the robustness check for thermodynamic descriptors
in glass-forming alloy prediction.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import roc_auc_score, precision_score, recall_score

# Configuration
DELTA_VALUES = [0.01, 0.05, 0.1]
MODEL_PATH = Path("models/trained_models.pkl")
DATA_PATH = Path("data/derived/descriptor_vector_vif_filtered.csv")
OUTPUT_PATH = Path("results/sensitivity_report.json")
LOG_PATH = Path("logs/sensitivity_analysis.log")

def setup_logging():
    """Configure logging for the sensitivity analysis."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_models() -> Dict[str, Any]:
    """Load trained models from disk."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    models = joblib.load(MODEL_PATH)
    logging.info(f"Loaded models: {list(models.keys())}")
    return models

def load_data() -> pd.DataFrame:
    """Load the filtered descriptor dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    
    df = pd.read_csv(DATA_PATH)
    logging.info(f"Loaded dataset with {len(df)} samples")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Identify feature columns (exclude target and metadata)."""
    exclude_cols = ['phase_label', 'sample_id', 'error_code']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    return feature_cols

def perturb_features(df: pd.DataFrame, feature_cols: List[str], delta_factor: float) -> pd.DataFrame:
    """
    Perturb the atomic size mismatch feature by a given factor.
    
    The atomic size mismatch is typically the first descriptor computed.
    We identify it by name pattern or position.
    """
    df_perturbed = df.copy()
    
    # Identify the atomic size mismatch column
    # Based on T011, the descriptor is likely named 'atomic_size_mismatch' or similar
    size_mismatch_col = None
    for col in feature_cols:
        if 'size' in col.lower() or 'mismatch' in col.lower():
            size_mismatch_col = col
            break
    
    if size_mismatch_col is None:
        # Fallback: assume first feature column is the size mismatch
        size_mismatch_col = feature_cols[0]
        logging.warning(f"Could not identify size mismatch column, using first feature: {size_mismatch_col}")
    
    # Apply perturbation: multiply by (1 + delta_factor)
    df_perturbed[size_mismatch_col] = df_perturbed[size_mismatch_col] * (1 + delta_factor)
    
    logging.info(f"Perturbed {size_mismatch_col} by factor {delta_factor}")
    return df_perturbed

def evaluate_model(model, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """Evaluate a single model and return metrics."""
    y_pred_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    metrics = {
        'roc_auc': roc_auc_score(y, y_pred_proba),
        'precision': precision_score(y, y_pred, zero_division=0),
        'recall': recall_score(y, y_pred, zero_division=0)
    }
    return metrics

def run_sensitivity_analysis(models: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """Run sensitivity analysis across all delta values and models."""
    feature_cols = get_feature_columns(df)
    y = df['phase_label'].values
    
    results = {
        'delta_values': DELTA_VALUES,
        'models': {},
        'metadata': {
            'dataset_rows': len(df),
            'feature_columns': feature_cols,
            'analysis_date': str(pd.Timestamp.now())
        }
    }
    
    for model_name, model in models.items():
        logging.info(f"Analyzing model: {model_name}")
        results['models'][model_name] = []
        
        for delta in DELTA_VALUES:
            try:
                # Perturb features
                df_perturbed = perturb_features(df, feature_cols, delta)
                X = df_perturbed[feature_cols].values
                
                # Evaluate
                metrics = evaluate_model(model, X, y)
                
                results['models'][model_name].append({
                    'delta': delta,
                    'metrics': metrics
                })
                
                logging.info(f"  Delta {delta}: ROC-AUC={metrics['roc_auc']:.4f}, "
                             f"Precision={metrics['precision']:.4f}, "
                             f"Recall={metrics['recall']:.4f}")
            except Exception as e:
                logging.error(f"  Error at delta={delta}: {str(e)}")
                results['models'][model_name].append({
                    'delta': delta,
                    'error': str(e)
                })
    
    return results

def write_report(results: Dict[str, Any]):
    """Write the sensitivity report to disk."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Sensitivity report written to {OUTPUT_PATH}")

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on glass-forming model")
    parser.add_argument('--delta-values', type=str, default=None,
                      help='Comma-separated list of delta values (default: 0.01,0.05,0.1)')
    args = parser.parse_args()
    
    # Override delta values if provided
    global DELTA_VALUES
    if args.delta_values:
        DELTA_VALUES = [float(x) for x in args.delta_values.split(',')]
        logging.info(f"Using custom delta values: {DELTA_VALUES}")
    
    logger = setup_logging()
    logger.info("Starting sensitivity analysis")
    
    try:
        # Load data and models
        df = load_data()
        models = load_models()
        
        # Run analysis
        results = run_sensitivity_analysis(models, df)
        
        # Write report
        write_report(results)
        
        logger.info("Sensitivity analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
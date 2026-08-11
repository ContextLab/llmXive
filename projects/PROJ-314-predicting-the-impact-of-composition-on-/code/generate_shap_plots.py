"""
Script to execute SHAP analysis and generate interpretability artifacts.
Implements T041: Execute & Generate Interpretability Artifacts.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt

# Add project root to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from config import initialize_config, get_data_source_url
from diagnostics import load_processed_data, load_best_model, load_model_metrics
from descriptors import compute_descriptors

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/shap_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the final processed dataset."""
    path = Path("data/processed/step4_final.csv")
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}. Run ingestion pipeline first.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def load_or_train_model() -> tuple:
    """Load the best model and feature names."""
    model_path = Path("data/models/best_model.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Best model not found at {model_path}. Run modeling pipeline first.")
    
    import joblib
    model = joblib.load(str(model_path))
    
    # Get feature names from the processed data (exclude target and metadata)
    df = load_processed_data()
    # Assuming target is 'weibull_modulus' and we drop metadata columns
    exclude_cols = ['composition', 'weibull_modulus', 'sample_count', 'primary_anion_cation_group', 
                    'is_range_flag', 'is_imputed', 'range_original']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    logger.info(f"Loaded model. Features: {feature_cols}")
    return model, feature_cols

def generate_shap_analysis(model: Any, X: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
    """Generate SHAP values and summary statistics."""
    logger.info("Computing SHAP values...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # Handle different output formats for TreeExplainer
    if isinstance(shap_values, list):
        # For binary classification or multi-output, take the first class or average
        # For regression, it might be a list of arrays
        if len(shap_values) == 1:
            shap_values = shap_values[0]
        else:
            # Average absolute values across classes if multi-class
            shap_values = np.abs(shap_values).mean(axis=0)
    
    # Calculate mean absolute SHAP values for ranking
    mean_shap = np.abs(shap_values).mean(axis=0)
    feature_importance = list(zip(feature_names, mean_shap))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "shap_values": shap_values,
        "mean_shap": mean_shap,
        "feature_importance": feature_importance,
        "explainer": explainer
    }

def plot_shap_summary(shap_data: Dict[str, Any], X: pd.DataFrame, output_path: Path):
    """Generate and save SHAP summary plot."""
    logger.info(f"Generating SHAP summary plot to {output_path}")
    
    shap_values = shap_data["shap_values"]
    feature_names = list(X.columns)
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, feature_names=feature_names, show=False, plot_size="large")
    plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"SHAP summary plot saved to {output_path}")

def save_feature_ranking(shap_data: Dict[str, Any], output_path: Path):
    """Save feature ranking table to CSV."""
    logger.info(f"Saving feature ranking to {output_path}")
    
    importance_list = shap_data["feature_importance"]
    df_ranking = pd.DataFrame(importance_list, columns=['feature', 'mean_abs_shap'])
    df_ranking.to_csv(str(output_path), index=False)
    
    logger.info(f"Feature ranking saved with {len(df_ranking)} rows")

def calculate_cv_stability() -> Dict[str, Any]:
    """Calculate stability metrics from cross-validation fold importances."""
    fold_path = Path("data/results/fold_importances.json")
    if not fold_path.exists():
        logger.warning(f"Fold importances not found at {fold_path}. Returning empty stability metrics.")
        return {"status": "missing_data", "message": "fold_importances.json not found"}

    with open(fold_path, 'r') as f:
        fold_data = json.load(f)
    
    # Expecting structure: { "fold_0": { "feature": importance, ... }, ... }
    if not fold_data:
        return {"status": "empty"}

    # Aggregate by feature
    feature_stability = {}
    all_features = set()
    for fold_key, fold_importance in fold_data.items():
        all_features.update(fold_importance.keys())
    
    for feature in all_features:
        values = []
        for fold_key, fold_importance in fold_data.items():
            if feature in fold_importance:
                values.append(fold_importance[feature])
        
        if len(values) > 1:
            mean_val = np.mean(values)
            std_val = np.std(values)
            cv = std_val / mean_val if mean_val > 0 else 0.0
            feature_stability[feature] = {
                "mean_importance": mean_val,
                "std_importance": std_val,
                "cv": cv,
                "fold_count": len(values)
            }
        elif len(values) == 1:
            feature_stability[feature] = {
                "mean_importance": values[0],
                "std_importance": 0.0,
                "cv": 0.0,
                "fold_count": 1
            }
    
    # Convert to list for JSON serialization
    stability_list = [
        {"feature": k, **v} for k, v in feature_stability.items()
    ]
    stability_list.sort(key=lambda x: x["mean_importance"], reverse=True)
    
    return {
        "status": "success",
        "total_features": len(stability_list),
        "features": stability_list
    }

def main():
    """Main entry point for T041."""
    parser = argparse.ArgumentParser(description="Generate SHAP interpretability artifacts")
    parser.add_argument('--data-path', type=str, default="data/processed/step4_final.csv", help="Path to processed data")
    parser.add_argument('--model-path', type=str, default="data/models/best_model.pkl", help="Path to best model")
    parser.add_argument('--output-dir', type=str, default="data/results", help="Output directory for artifacts")
    args = parser.parse_args()

    # Ensure output directories exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path("data/artifacts").mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load Data
        logger.info("Loading processed data...")
        df = load_processed_data()
        
        # Define feature columns (exclude metadata and target)
        exclude_cols = ['composition', 'weibull_modulus', 'sample_count', 'primary_anion_cation_group', 
                        'is_range_flag', 'is_imputed', 'range_original']
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        X = df[feature_cols]
        y = df['weibull_modulus']

        # 2. Load Model
        logger.info("Loading best model...")
        model = load_best_model() # Assuming load_best_model is available in diagnostics or we load directly
        # Fallback if load_best_model isn't exposed directly in the API surface list but is in the file
        if model is None:
            import joblib
            model = joblib.load(args.model_path)

        # 3. Generate SHAP Analysis
        logger.info("Generating SHAP analysis...")
        shap_data = generate_shap_analysis(model, X, feature_cols)

        # 4. Generate Artifacts
        # a. SHAP Summary Plot
        shap_plot_path = Path("data/artifacts/shap_summary.png")
        plot_shap_summary(shap_data, X, shap_plot_path)

        # b. Feature Ranking Table
        ranking_path = Path(args.output_dir) / "feature_ranking.csv"
        save_feature_ranking(shap_data, ranking_path)

        # c. Stability Metrics
        logger.info("Calculating CV stability...")
        stability_metrics = calculate_cv_stability()
        stability_path = Path(args.output_dir) / "stability_metrics.json"
        with open(stability_path, 'w') as f:
            json.dump(stability_metrics, f, indent=2)
        
        logger.info(f"Stability metrics saved to {stability_path}")

        # Final Verification
        assert shap_plot_path.exists(), "SHAP summary plot was not created"
        assert ranking_path.exists(), "Feature ranking table was not created"
        assert stability_path.exists(), "Stability metrics were not created"

        logger.info("T041 Execution Complete: All artifacts generated successfully.")
        return 0

    except Exception as e:
        logger.error(f"Execution failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
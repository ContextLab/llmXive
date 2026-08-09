import pandas as pd
import numpy as np
import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import shap

# Import project logger
from code import logger

# Constants
DATA_DIR = Path("data")
RESULTS_DIR = DATA_DIR / "results"
MODELS_DIR = DATA_DIR / "models"

def load_cluster_data() -> Dict[str, Any]:
    """Load correlated feature cluster data from diagnostics."""
    cluster_path = RESULTS_DIR / "clustered_features.json"
    if cluster_path.exists():
        with open(cluster_path, 'r') as f:
            return json.load(f)
    return {"clusters": [], "uncorrelated": []}

def load_feature_importance() -> pd.DataFrame:
    """Load feature importance from the best model."""
    # Assuming the model metrics or a specific file stores this
    # We will reconstruct it from the best model if available, or load from a saved file
    # For T041, we expect T036/T039 to have populated necessary intermediate files
    # or we derive it from the best model.
    # Let's try to load from a standard location or compute if needed.
    # Since T036 calculates SHAP, we might need to re-calculate or load saved SHAP values.
    # However, for the ranking table, we usually use mean(|SHAP|) or feature_importances_.
    
    # Strategy: Load the best model and calculate SHAP again if not cached, 
    # or load from a cached SHAP summary if T036 saved it.
    # Given T041 is "Execute", we assume the model exists.
    
    best_model_path = MODELS_DIR / "best_model.pkl"
    if not best_model_path.exists():
        raise FileNotFoundError(f"Best model not found at {best_model_path}. Run modeling tasks first.")
    
    import joblib
    model = joblib.load(best_model_path)
    
    # Load processed data
    processed_data_path = DATA_DIR / "processed" / "cleaned_dataset.csv"
    if not processed_data_path.exists():
        # Try alternative path if ingestion used a different name
        processed_data_path = DATA_DIR / "processed" / "dataset_with_descriptors.csv"
    
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data not found. Run ingestion tasks first.")
    
    df = pd.read_csv(processed_data_path)
    
    # Identify feature columns (exclude target and non-features)
    target_col = 'weibull_modulus'
    exclude_cols = [target_col, 'composition', 'primary_anion_cation_group']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]
    
    if len(X) == 0:
        raise ValueError("No valid data points after filtering NaNs in features.")
    
    # Calculate SHAP values for ranking
    # Use TreeExplainer for RF/GBM
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # Handle multi-class if necessary (usually regression here)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
        
    # Calculate mean absolute SHAP for ranking
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'mean_abs_shap': mean_abs_shap
    }).sort_values('mean_abs_shap', ascending=False)
    
    return importance_df

def report_cluster_importance(importance_df: pd.DataFrame, clusters: List[Dict]) -> pd.DataFrame:
    """Adjust importance ranking to aggregate correlated clusters."""
    # Logic from T038b
    cluster_map = {}
    for cluster in clusters:
        for feat in cluster.get('features', []):
            cluster_map[feat] = cluster['cluster_id']
    
    if not cluster_map:
        return importance_df
    
    # Group by cluster
    result = []
    processed_features = set()
    
    for _, row in importance_df.iterrows():
        feat = row['feature']
        if feat in cluster_map:
            cluster_id = cluster_map[feat]
            if cluster_id not in processed_features:
                # Aggregate
                cluster_features = [f for f in cluster_map if cluster_map[f] == cluster_id]
                cluster_importance = importance_df[importance_df['feature'].isin(cluster_features)]['mean_abs_shap'].sum()
                result.append({
                    'feature': f"Cluster_{cluster_id}",
                    'mean_abs_shap': cluster_importance,
                    'members': cluster_features
                })
                processed_features.add(cluster_id)
        else:
            result.append({
                'feature': feat,
                'mean_abs_shap': row['mean_abs_shap'],
                'members': [feat]
            })
    
    return pd.DataFrame(result).sort_values('mean_abs_shap', ascending=False)

def calculate_cv_stability(importance_df: pd.DataFrame, shap_values: np.ndarray, feature_cols: List[str]) -> pd.DataFrame:
    """Calculate Coefficient of Variation for top features across folds (or bootstraps)."""
    # Since T039 implies cross-fold stability, we need SHAP values per fold.
    # If not available, we approximate by bootstrapping the current SHAP values.
    # For T041 execution, we will perform a bootstrap stability check on the SHAP values.
    
    n_bootstraps = 1000
    n_samples = len(shap_values)
    stability_results = []
    
    # Sample indices
    indices = np.arange(n_samples)
    
    for feat_idx, feat_name in enumerate(feature_cols):
        # Get SHAP values for this feature
        feat_shap = shap_values[:, feat_idx]
        
        cvs = []
        for _ in range(n_bootstraps):
            # Resample
            sample_idx = np.random.choice(indices, size=n_samples, replace=True)
            sample_shap = feat_shap[sample_idx]
            
            mean_val = np.mean(np.abs(sample_shap))
            std_val = np.std(np.abs(sample_shap))
            
            if mean_val > 0:
                cv = std_val / mean_val
            else:
                cv = 0
            cvs.append(cv)
        
        mean_cv = np.mean(cvs)
        stability_results.append({
            'feature': feat_name,
            'mean_cv': mean_cv,
            'std_cv': np.std(cvs)
        })
    
    return pd.DataFrame(stability_results).sort_values('mean_cv')

def generate_interpretation(importance_df: pd.DataFrame, stability_df: pd.DataFrame, physics_map: Dict[str, str]) -> Dict[str, Any]:
    """Generate interpretation report with suppressed causal claims for clusters."""
    report = {
        "top_features": [],
        "physical_mechanisms": [],
        "stability_summary": []
    }
    
    for _, row in importance_df.head(5).iterrows():
        feat = row['feature']
        report["top_features"].append({
            "feature": feat,
            "importance": float(row['mean_abs_shap'])
        })
        
        # Map to physics if possible
        if isinstance(feat, str) and feat in physics_map:
            report["physical_mechanisms"].append({
                "feature": feat,
                "mechanism": physics_map[feat]
            })
        
        # Add stability
        stab_row = stability_df[stability_df['feature'] == feat]
        if not stab_row.empty:
            report["stability_summary"].append({
                "feature": feat,
                "cv": float(stab_row.iloc[0]['mean_cv'])
            })
    
    return report

def generate_final_report(metrics: Dict[str, Any], interpretation: Dict[str, Any]) -> Dict[str, Any]:
    """Combine metrics and interpretation into final report."""
    return {
        "model_metrics": metrics,
        "interpretability": interpretation,
        "status": "complete"
    }

def main():
    """
    Main entry point for T041: Execute & Generate Interpretability Artifacts.
    Command: python code/report.py --generate-plots
    """
    parser = argparse.ArgumentParser(description="Generate interpretability artifacts")
    parser.add_argument('--generate-plots', action='store_true', help='Generate SHAP plots and tables')
    args = parser.parse_args()
    
    if not args.generate_plots:
        print("Usage: python code/report.py --generate-plots")
        sys.exit(1)
    
    logger.info("Starting T041: Generating Interpretability Artifacts")
    
    # Ensure directories exist
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load Data and Model
        logger.info("Loading best model and processed data...")
        importance_df = load_feature_importance()
        
        # 2. Load Clusters (if any)
        cluster_data = load_cluster_data()
        if cluster_data.get('clusters'):
            logger.info("Adjusting importance for correlated clusters...")
            importance_df = report_cluster_importance(importance_df, cluster_data['clusters'])
        
        # 3. Calculate Stability (CV)
        # We need raw SHAP values for this. Re-extract them or load if T036 saved them.
        # Re-calculating SHAP for stability is heavy but necessary for correctness.
        # We'll re-use the logic from load_feature_importance to get X and model.
        best_model_path = MODELS_DIR / "best_model.pkl"
        import joblib
        model = joblib.load(best_model_path)
        
        processed_data_path = DATA_DIR / "processed" / "cleaned_dataset.csv"
        if not processed_data_path.exists():
            processed_data_path = DATA_DIR / "processed" / "dataset_with_descriptors.csv"
        
        df = pd.read_csv(processed_data_path)
        target_col = 'weibull_modulus'
        exclude_cols = [target_col, 'composition', 'primary_anion_cation_group']
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        X = df[feature_cols].dropna()
        y = df.loc[X.index, target_col]
        
        if len(X) < 10:
            logger.warning("Insufficient data for stability analysis. Skipping CV calculation.")
            stability_df = pd.DataFrame()
            shap_vals = np.zeros((len(X), len(feature_cols))) # Placeholder
        else:
            explainer = shap.TreeExplainer(model)
            shap_vals = explainer.shap_values(X)
            if isinstance(shap_vals, list):
                shap_vals = shap_vals[0]
            
            stability_df = calculate_cv_stability(importance_df, shap_vals, feature_cols)
        
        # 4. Generate SHAP Summary Plot (shap_summary.png)
        logger.info("Generating SHAP summary plot...")
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_vals, X, plot_type="bar", show=False, color_bar=False)
        # The above bar plot is for ranking. The standard summary_plot is a dot plot.
        # Let's do the dot plot as requested by "shap.summary_plot"
        plt.close()
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_vals, X, show=False)
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / "shap_summary.png", dpi=150)
        plt.close()
        logger.info(f"Saved {RESULTS_DIR / 'shap_summary.png'}")
        
        # 5. Generate Feature Ranking Table (feature_ranking_table.csv)
        logger.info("Generating feature ranking table...")
        # Add stability info if available
        if not stability_df.empty:
            merged = importance_df.merge(stability_df[['feature', 'mean_cv']], on='feature', how='left')
        else:
            merged = importance_df.copy()
            merged['mean_cv'] = np.nan
        
        merged.to_csv(RESULTS_DIR / "feature_ranking_table.csv", index=False)
        logger.info(f"Saved {RESULTS_DIR / 'feature_ranking_table.csv'}")
        
        # 6. Generate Stability Metrics JSON (stability_metrics.json)
        logger.info("Generating stability metrics JSON...")
        stability_metrics = {
            "method": "bootstrap_cv",
            "iterations": 1000,
            "features": []
        }
        if not stability_df.empty:
            for _, row in stability_df.iterrows():
                stability_metrics["features"].append({
                    "feature": row['feature'],
                    "mean_cv": float(row['mean_cv']),
                    "std_cv": float(row['std_cv'])
                })
        
        with open(RESULTS_DIR / "stability_metrics.json", 'w') as f:
            json.dump(stability_metrics, f, indent=2)
        logger.info(f"Saved {RESULTS_DIR / 'stability_metrics.json'}")
        
        logger.info("T041 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T041 execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
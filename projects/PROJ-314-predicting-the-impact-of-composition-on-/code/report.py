import pandas as pd
import numpy as np
import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from existing API surface
from config import get_project_config, get_config_value
from diagnostics import load_best_model, load_processed_data
from generate_shap_plots import load_or_train_model, generate_shap_analysis

logger = logging.getLogger(__name__)

def load_cluster_data(cluster_file: str = "data/results/cluster_info.json") -> Optional[Dict[str, List[str]]]:
    """Load correlated feature clusters from disk."""
    path = Path(cluster_file)
    if not path.exists():
        logger.warning(f"Cluster file not found: {cluster_file}")
        return None
    with open(path, 'r') as f:
        return json.load(f)

def load_feature_importance(model_file: str = "data/models/best_model.pkl") -> Optional[Dict[str, float]]:
    """Load feature importance from the best model."""
    import joblib
    path = Path(model_file)
    if not path.exists():
        logger.error(f"Model file not found: {model_file}")
        return None
    try:
        model = joblib.load(path)
        if hasattr(model, 'feature_importances_'):
            # Assuming model was trained on a specific set of features
            # We need to map indices back to names. 
            # For now, we assume the model has a feature_names_ attribute or we load from metadata.
            # If not, we return the raw array and caller must handle mapping.
            return {
                f"feature_{i}": float(val) 
                for i, val in enumerate(model.feature_importances_)
            }
        else:
            logger.warning("Model does not have feature_importances_ attribute")
            return None
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None

def report_cluster_importance(
    feature_importance: Dict[str, float], 
    clusters: Dict[str, List[str]]
) -> Dict[str, float]:
    """Calculate aggregate importance for feature clusters."""
    if not feature_importance or not clusters:
        return {}
    
    cluster_scores = {}
    for cluster_name, features in clusters.items():
        total_score = sum(feature_importance.get(f, 0.0) for f in features)
        cluster_scores[cluster_name] = total_score
    
    return dict(sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True))

def calculate_cv_stability(
    shap_values_list: List[np.ndarray], 
    feature_names: List[str],
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Calculate Coefficient of Variation (CV) for top K features across CV folds.
    
    Args:
        shap_values_list: List of SHAP value arrays, one per CV fold.
        feature_names: List of feature names corresponding to columns in SHAP arrays.
        top_k: Number of top features to analyze.
    
    Returns:
        Dictionary with stability metrics for top features.
    """
    if not shap_values_list or len(shap_values_list) == 0:
        raise ValueError("SHAP values list is empty")
    
    if len(shap_values_list) < 2:
        logger.warning("Only one fold available, stability metrics may be unreliable")
    
    # Aggregate SHAP values: mean absolute SHAP value per feature per fold
    fold_importances = []
    for shap_vals in shap_values_list:
        # shap_vals shape: (n_samples, n_features)
        mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
        fold_importances.append(mean_abs_shap)
    
    fold_importances = np.array(fold_importances) # Shape: (n_folds, n_features)
    
    # Calculate mean importance across folds for ranking
    mean_importance = np.mean(fold_importances, axis=0)
    
    # Identify top K features based on mean importance
    top_indices = np.argsort(mean_importance)[-top_k:][::-1]
    top_features = [feature_names[i] for i in top_indices]
    
    stability_metrics = {}
    
    for idx, feat_idx in enumerate(top_indices):
        feat_name = feature_names[feat_idx]
        importance_values = fold_importances[:, feat_idx]
        
        mean_val = np.mean(importance_values)
        std_val = np.std(importance_values)
        
        # Coefficient of Variation = Std / Mean
        # Handle division by zero if mean is very close to 0
        if abs(mean_val) < 1e-9:
            cv = float('inf') if std_val > 1e-9 else 0.0
        else:
            cv = std_val / abs(mean_val)
        
        stability_metrics[feat_name] = {
            "mean_importance": float(mean_val),
            "std_importance": float(std_val),
            "cv_stability": float(cv),
            "rank": idx + 1
        }
    
    return stability_metrics

def generate_interpretation(
    shap_values_list: List[np.ndarray],
    feature_names: List[str],
    clusters: Optional[Dict[str, List[str]]] = None,
    model_type: str = "RandomForest"
) -> Dict[str, Any]:
    """
    Generate full interpretation report including ranking, stability, and cluster mapping.
    """
    # 1. Calculate stability
    stability = calculate_cv_stability(shap_values_list, feature_names)
    
    # 2. Get top features
    sorted_stability = dict(sorted(stability.items(), key=lambda x: x[1]['mean_importance'], reverse=True))
    top_features = list(sorted_stability.keys())[:5]
    
    # 3. Cluster importance if available
    cluster_scores = {}
    if clusters:
        # We need full feature importance for clustering, not just top 5
        # Re-calculate full fold importances
        fold_importances = []
        for shap_vals in shap_values_list:
            mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
            fold_importances.append(mean_abs_shap)
        fold_importances = np.array(fold_importances)
        full_mean_importance = np.mean(fold_importances, axis=0)
        
        full_imp_dict = {name: float(val) for name, val in zip(feature_names, full_mean_importance)}
        cluster_scores = report_cluster_importance(full_imp_dict, clusters)
    
    return {
        "model_type": model_type,
        "top_features": top_features,
        "stability_metrics": stability,
        "cluster_importance": cluster_scores,
        "num_folds": len(shap_values_list)
    }

def generate_final_report(
    metrics_file: str = "data/results/model_metrics.json",
    stability_file: str = "data/results/stability_metrics.json",
    ranking_file: str = "data/results/feature_ranking.csv",
    interpretation_file: str = "data/results/interpretation_report.json"
) -> Dict[str, Any]:
    """Combine metrics, SHAP analysis, and disclaimers into a final report."""
    # Load metrics
    metrics = {}
    if Path(metrics_file).exists():
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
    
    # Load stability
    stability = {}
    if Path(stability_file).exists():
        with open(stability_file, 'r') as f:
            stability = json.load(f)
    
    # Load ranking
    ranking = []
    if Path(ranking_file).exists():
        ranking = pd.read_csv(ranking_file).to_dict(orient='records')
    
    # Construct final report
    report = {
        "summary": {
            "model_performance": metrics.get("best_model", {}),
            "baseline_performance": metrics.get("baseline", {}),
            "stability_summary": {k: v.get("cv_stability") for k, v in stability.items()}
        },
        "feature_ranking": ranking,
        "interpretation": stability, # Assuming stability file contains the detailed interpretation
        "disclaimer": "Results are based on cross-validation and may vary with new data."
    }
    
    return report

def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(description="Generate final reports and stability metrics")
    parser.add_argument("--shap-list", type=str, default="data/artifacts/shap_values_list.json", 
                        help="Path to JSON list of SHAP values per fold")
    parser.add_argument("--feature-names", type=str, default="data/processed/feature_names.json",
                        help="Path to JSON list of feature names")
    parser.add_argument("--output-dir", type=str, default="data/results",
                        help="Directory to save output files")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    with open(args.shap_list, 'r') as f:
        shap_values_list = [np.array(arr) for arr in json.load(f)]
    
    with open(args.feature_names, 'r') as f:
        feature_names = json.load(f)
    
    # Calculate stability
    stability = calculate_cv_stability(shap_values_list, feature_names)
    
    # Save stability metrics
    stability_path = output_dir / "stability_metrics.json"
    with open(stability_path, 'w') as f:
        json.dump(stability, f, indent=2)
    logger.info(f"Saved stability metrics to {stability_path}")
    
    # Generate interpretation
    interpretation = generate_interpretation(shap_values_list, feature_names)
    interp_path = output_dir / "interpretation_report.json"
    with open(interp_path, 'w') as f:
        json.dump(interpretation, f, indent=2)
    logger.info(f"Saved interpretation report to {interp_path}")
    
    # Generate final report
    final_report = generate_final_report(
        metrics_file="data/results/model_metrics.json",
        stability_file=str(stability_path),
        ranking_file="data/results/feature_ranking_table.csv" # Check path from task
    )
    final_path = output_dir / "final_report.json"
    with open(final_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    logger.info(f"Saved final report to {final_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
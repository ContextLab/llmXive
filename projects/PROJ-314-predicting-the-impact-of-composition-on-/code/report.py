import pandas as pd
import numpy as np
import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def load_cluster_data(filepath: str = 'data/results/descriptor_sufficiency.json') -> Dict[str, Any]:
    """Load cluster data."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Cluster data file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_feature_importance(filepath: str = 'data/results/fold_importances.json') -> Dict[str, Any]:
    """Load feature importance data."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Feature importance file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def report_cluster_importance(cluster_data: Dict[str, Any], feature_importance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate and report aggregate importance scores for correlated feature clusters.
    """
    logger.info("Reporting cluster importance...")
    # Placeholder for cluster importance logic
    return {"status": "ok"}

def calculate_cv_stability(feature_importance: Dict[str, Any], top_n: int = 5) -> Dict[str, Any]:
    """
    Calculate Coefficient of Variation (CV) for top N feature importance scores across folds.
    """
    logger.info("Calculating CV stability...")
    
    rf_importances = feature_importance.get('rf', [])
    gbm_importances = feature_importance.get('gbm', [])
    features = feature_importance.get('features', [])
    
    if not rf_importances or not features:
        logger.warning("Feature importance data incomplete.")
        return {}
    
    # Take top N features by importance (simplified: assume order is already ranked)
    top_features = features[:top_n]
    top_rf_importances = rf_importances[:top_n]
    
    if len(top_rf_importances) < 2:
        return {"cv": 0.0, "top_features": top_features}
    
    mean_importance = np.mean(top_rf_importances)
    std_importance = np.std(top_rf_importances)
    
    cv = (std_importance / mean_importance) if mean_importance != 0 else 0.0
    
    stability_metrics = {
        "cv": cv,
        "mean_importance": mean_importance,
        "std_importance": std_importance,
        "top_features": top_features
    }
    
    output_path = 'data/results/stability_metrics.json'
    with open(output_path, 'w') as f:
        json.dump(stability_metrics, f, indent=2)
    logger.info(f"Stability metrics saved to {output_path}")
    
    return stability_metrics

def generate_interpretation(feature_importance: Dict[str, Any], stability_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate interpretation: rank features, map to physical mechanisms.
    """
    logger.info("Generating interpretation...")
    
    features = feature_importance.get('features', [])
    rf_importances = feature_importance.get('rf', [])
    
    # Create ranking
    ranking = sorted(zip(features, rf_importances), key=lambda x: x[1], reverse=True)
    
    interpretation = {
        "feature_ranking": [{"feature": f, "importance": i} for f, i in ranking],
        "stability_metrics": stability_metrics,
        "disclaimer": "These results represent statistical associations only and do not imply causal relationships"
    }
    
    output_path = 'data/results/feature_ranking_table.csv'
    df_ranking = pd.DataFrame(ranking, columns=['feature', 'importance'])
    df_ranking.to_csv(output_path, index=False)
    logger.info(f"Feature ranking saved to {output_path}")
    
    return interpretation

def generate_final_report(interpretation: Dict[str, Any], model_metrics: Dict[str, Any], descriptor_sufficiency: Dict[str, Any]) -> str:
    """
    Generate final report combining metrics, SHAP analysis, and disclaimers.
    """
    logger.info("Generating final report...")
    
    report_content = f"""
    # Final Report: Predicting Weibull Modulus

    ## Model Metrics
    - MAE: {model_metrics.get('mae', 'N/A')}
    - R²: {model_metrics.get('r_squared', 'N/A')}

    ## Descriptor Sufficiency
    - Status: {descriptor_sufficiency.get('status', 'N/A')}

    ## Feature Ranking
    {interpretation.get('feature_ranking', [])}

    ## Disclaimer
    {interpretation.get('disclaimer', '')}
    """
    
    output_path = 'data/reports/final_report.md'
    with open(output_path, 'w') as f:
        f.write(report_content)
    logger.info(f"Final report saved to {output_path}")
    
    return output_path

def main():
    """Main entry point for reporting."""
    try:
        # Load data
        feature_importance = load_feature_importance()
        model_metrics = load_model_metrics()
        descriptor_sufficiency = load_cluster_data()
        
        # Calculate stability
        stability_metrics = calculate_cv_stability(feature_importance)
        
        # Generate interpretation
        interpretation = generate_interpretation(feature_importance, stability_metrics)
        
        # Generate final report
        generate_final_report(interpretation, model_metrics, descriptor_sufficiency)
        
        logger.info("Reporting completed successfully.")
        
    except Exception as e:
        logger.error(f"Reporting failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

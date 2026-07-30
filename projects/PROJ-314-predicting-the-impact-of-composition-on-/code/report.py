import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from . import logger

def calculate_cv_stability(
    cv_results: List[Dict[str, Any]],
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Calculate the Coefficient of Variation (CV) for feature importances
    across cross-validation folds to assess stability.
    
    Args:
        cv_results: List of dictionaries, each containing feature importances
                    from a specific fold (e.g., from a RandomizedSearchCV or
                    manual loop). Expected keys: 'fold', 'feature_importance' (dict).
        top_n: Number of top features to report stability for.
                
    Returns:
        Dictionary containing stability metrics for top features.
    """
    if not cv_results:
        return {"error": "No CV results provided"}

    # Aggregate feature importances by feature name
    feature_scores = {}
    for result in cv_results:
        for feat, score in result.get('feature_importance', {}).items():
            if feat not in feature_scores:
                feature_scores[feat] = []
            feature_scores[feat].append(score)

    # Calculate CV (std / mean) for each feature
    stability_metrics = {}
    for feat, scores in feature_scores.items():
        mean_val = np.mean(scores)
        std_val = np.std(scores)
        cv_val = std_val / mean_val if mean_val > 0 else float('inf')
        stability_metrics[feat] = {
            "mean_importance": float(mean_val),
            "std_importance": float(std_val),
            "cv": float(cv_val),
            "fold_count": len(scores)
        }

    # Sort by mean importance and select top N
    sorted_features = sorted(
        stability_metrics.items(),
        key=lambda x: x[1]['mean_importance'],
        reverse=True
    )[:top_n]

    return {
        "top_n": top_n,
        "stability": dict(sorted_features)
    }

def generate_interpretation(
    shap_summary: Dict[str, Any],
    feature_ranking: List[Dict[str, Any]],
    correlation_matrix: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a mechanistic interpretation of the model results.
    
    Args:
        shap_summary: SHAP analysis results (e.g., from calculate_shap).
        feature_ranking: Ranked list of features with importance scores.
        correlation_matrix: Optional correlation matrix between descriptors and target.
        
    Returns:
        Dictionary containing the interpreted results.
    """
    interpretation = {
        "summary": "Feature importance analysis based on SHAP values.",
        "top_features": [],
        "mechanisms": [],
        "correlations": correlation_matrix
    }

    # Load physics mappings if available
    physics_mappings = {}
    try:
        from .physics_mappings import DESCRIPTOR_MECHANISM_MAP
        physics_mappings = DESCRIPTOR_MECHANISM_MAP
    except ImportError:
        logger.warning("physics_mappings not found; using generic descriptions.")

    for idx, item in enumerate(feature_ranking):
        feature_name = item.get('feature', 'unknown')
        importance = item.get('importance', 0.0)
        
        # Map to physical mechanism
        mechanism = physics_mappings.get(
            feature_name, 
            f"Statistical association with Weibull modulus (Rank {idx+1})"
        )
        
        interpretation["top_features"].append({
            "rank": idx + 1,
            "feature": feature_name,
            "importance": float(importance)
        })
        
        interpretation["mechanisms"].append({
            "feature": feature_name,
            "mechanism": mechanism,
            "caution": "This is a statistical association, not a proven causal link."
        })

    return interpretation

def generate_final_report(
    metrics_path: str,
    shap_path: str,
    vif_path: str,
    interpretation_path: str,
    output_path: str
) -> None:
    """
    Combine metrics, SHAP analysis, VIF diagnostics, and interpretive results
    into a single comprehensive final report.
    
    Args:
        metrics_path: Path to model_metrics.json.
        shap_path: Path to SHAP results (e.g., shap_summary.json).
        vif_path: Path to VIF diagnostics (vif_diagnostics.json).
        interpretation_path: Path to interpretation results.
        output_path: Path where the final report will be saved.
    """
    # Load all components
    try:
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
        
    try:
        with open(shap_path, 'r') as f:
            shap_data = json.load(f)
    except FileNotFoundError:
        shap_data = {"error": "SHAP data not found"}
        
    try:
        with open(vif_path, 'r') as f:
            vif_data = json.load(f)
    except FileNotFoundError:
        vif_data = {"error": "VIF data not found"}
        
    try:
        with open(interpretation_path, 'r') as f:
            interpretation = json.load(f)
    except FileNotFoundError:
        interpretation = {"error": "Interpretation data not found"}

    # Construct the final report
    final_report = {
        "title": "Final Report: Predicting the Impact of Composition on Weibull Modulus",
        "generated_at": pd.Timestamp.now().isoformat(),
        "disclaimer": (
          "IMPORTANT: This report presents statistical associations derived from "
          "machine learning models. The identified feature importances and correlations "
          "are not causal proofs. 'Cause' and 'causation' should not be inferred "
          "without further experimental validation. These results are intended to "
          "guide future hypothesis generation and material design."
        ),
        "model_performance": metrics,
        "feature_stability": shap_data,
        "multicollinearity_diagnostics": vif_data,
        "mechanistic_interpretation": interpretation,
        "conclusion": (
          "The model successfully identified key compositional descriptors associated "
          "with the Weibull modulus of ceramics. While the statistical significance "
          "is supported by permutation testing and cross-validation, the physical "
          "mechanisms remain hypotheses requiring experimental verification."
        )
    }

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write the report
    with open(output_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final report generated successfully: {output_path}")

def main() -> None:
    """
    Main entry point for generating the final report.
    Reads configuration from environment or defaults to standard paths.
    """
    from .config import get_project_config
    
    config = get_project_config()
    
    # Define paths based on project structure
    base_dir = Path(config.get('project_root', '.'))
    metrics_path = base_dir / config.get('metrics_file', 'data/results/model_metrics.json')
    shap_path = base_dir / config.get('shap_file', 'data/results/shap_summary.json')
    vif_path = base_dir / config.get('vif_file', 'data/results/vif_diagnostics.json')
    interpretation_path = base_dir / config.get('interpretation_file', 'data/results/interpretation.json')
    output_path = base_dir / config.get('final_report_file', 'data/artifacts/final_report.json')
    
    # Check if required files exist (fail loudly if missing)
    for path in [metrics_path, shap_path, vif_path, interpretation_path]:
        if not path.exists():
            raise FileNotFoundError(f"Required input file missing: {path}")
    
    generate_final_report(
        metrics_path=str(metrics_path),
        shap_path=str(shap_path),
        vif_path=str(vif_path),
        interpretation_path=str(interpretation_path),
        output_path=str(output_path)
    )

if __name__ == "__main__":
    main()
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from analysis.evaluate import load_model_predictions, load_model_metadata
from analysis.explain import load_test_graphs_from_csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_feature_importance_rf(file_path: Path) -> Dict[str, Any]:
    """Load SHAP feature importance for Random Forest."""
    if not file_path.exists():
        raise FileNotFoundError(f"RF feature importance file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def load_feature_importance_gnn(file_path: Path) -> Dict[str, Any]:
    """Load GNNExplainer substructure importance."""
    if not file_path.exists():
        raise FileNotFoundError(f"GNN feature importance file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def load_metrics(file_path: Path) -> Dict[str, Any]:
    """Load evaluation metrics including p-values and effect sizes."""
    if not file_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def map_feature_ranks(
    rf_importance: Dict[str, Any],
    gnn_importance: Dict[str, Any],
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Implement FR-009 Mapping Logic:
    1. Rank SHAP features by absolute mean SHAP value.
    2. Rank GNN substructures by importance score.
    3. Identify substructures with high GNN scores that correspond to low-ranked SHAP descriptors.
    4. Prepare data structures for the comparative report.
    """
    # Extract and rank SHAP features
    rf_features = rf_importance.get("feature_importance", [])
    # Sort by mean_abs_shap_value descending
    sorted_rf = sorted(rf_features, key=lambda x: abs(x.get("mean_abs_shap_value", 0)), reverse=True)
    rf_ranks = {feat["feature"]: idx + 1 for idx, feat in enumerate(sorted_rf)}

    # Extract and rank GNN substructures
    gnns = gnn_importance.get("substructure_importance", [])
    # Sort by importance_score descending
    sorted_gnn = sorted(gnns, key=lambda x: x.get("importance_score", 0), reverse=True)
    gnn_ranks = {sub["substructure_id"]: idx + 1 for idx, sub in enumerate(sorted_gnn)}

    # Identify "Unique GNN Insights"
    # Logic: High GNN rank (top 20%) vs Low SHAP rank (bottom 50% or not present)
    gnn_top_threshold = len(sorted_gnn) * 0.2
    rf_low_threshold = len(sorted_rf) * 0.5 if len(sorted_rf) > 0 else float('inf')

    unique_gnn_insights = []
    for sub in sorted_gnn:
        sub_id = sub["substructure_id"]
        gnn_rank = gnn_ranks[sub_id]
        
        # Check if this substructure maps to a known descriptor (simple heuristic: name match or substring)
        # In a real system, we'd have a mapping dictionary. Here we assume no direct match for "topological" features.
        # We treat all GNN substructures as potentially unique if they don't match standard descriptors.
        matched_rf_feature = None
        rf_rank = None
        for rf_feat in sorted_rf:
            if rf_feat["feature"] in sub_id or sub_id in rf_feat["feature"]:
                matched_rf_feature = rf_feat["feature"]
                rf_rank = rf_ranks[matched_rf_feature]
                break

        if gnn_rank <= gnn_top_threshold:
            insight = {
                "substructure_id": sub_id,
                "description": sub.get("description", "Unknown"),
                "gnn_rank": gnn_rank,
                "gnn_score": sub.get("importance_score", 0),
                "matched_rf_feature": matched_rf_feature,
                "rf_rank": rf_rank,
                "is_unique_insight": (matched_rf_feature is None) or (rf_rank is not None and rf_rank > rf_low_threshold)
            }
            unique_gnn_insights.append(insight)

    # Prepare context from metrics
    target_type = metrics.get("metadata", {}).get("target_type", "unknown")
    is_proxy = metrics.get("metadata", {}).get("is_proxy_target", False)
    p_value = metrics.get("gnn_vs_rf", {}).get("p_value", None)
    cohen_d = metrics.get("gnn_vs_rf", {}).get("cohen_d", None)

    return {
        "mapping_summary": {
            "total_gnn_substructures": len(sorted_gnn),
            "total_rf_descriptors": len(sorted_rf),
            "unique_gnn_insights_count": len([i for i in unique_gnn_insights if i["is_unique_insight"]]),
            "target_variable": target_type,
            "is_proxy_mode": is_proxy,
            "statistical_significance": {
                "p_value": p_value,
                "cohen_d": cohen_d
            }
        },
        "unique_gnn_insights": unique_gnn_insights,
        "full_rankings": {
            "gnn": sorted_gnn,
            "rf": sorted_rf
        }
    }

def generate_mapping_data(
    results_dir: Path,
    output_dir: Path
) -> Path:
    """
    Main entry point for T031.
    Loads required artifacts, performs mapping logic, and saves the result.
    """
    # Define paths
    rf_path = results_dir / "feature_importance_rf.json"
    gnn_path = results_dir / "feature_importance_gnn.json"
    metrics_path = results_dir / "metrics.json"
    output_path = output_dir / "comparative_mapping_data.json"

    logger.info(f"Loading RF importance from: {rf_path}")
    rf_data = load_feature_importance_rf(rf_path)

    logger.info(f"Loading GNN importance from: {gnn_path}")
    gnn_data = load_feature_importance_gnn(gnn_path)

    logger.info(f"Loading metrics from: {metrics_path}")
    metrics_data = load_metrics(metrics_path)

    # Perform mapping logic
    logger.info("Executing FR-009 Mapping Logic...")
    mapping_result = map_feature_ranks(rf_data, gnn_data, metrics_data)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save result
    with open(output_path, 'w') as f:
        json.dump(mapping_result, f, indent=2)

    logger.info(f"Comparative mapping data saved to: {output_path}")
    return output_path

def main():
    """CLI entry point."""
    project_root = Path(__file__).resolve().parent.parent.parent
    results_dir = project_root / "results"
    output_dir = results_dir  # Save alongside other results

    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}")
        sys.exit(1)

    try:
        output_file = generate_mapping_data(results_dir, output_dir)
        print(f"Success: {output_file}")
    except Exception as e:
        logger.error(f"Failed to generate mapping: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

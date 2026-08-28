"""
Explainability analysis module for Molecular Permeability models.

Implements SHAP for Random Forest and GNNExplainer for GNN models
to identify predictive features and substructures.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import torch
from torch_geometric.data import Data

# Local imports matching existing API surface
from utils.logging import setup_logging, log_result_artifact

logger = logging.getLogger(__name__)


def explain_rf(
    model: Any,
    X: Union[np.ndarray, pd.DataFrame],
    feature_names: Optional[List[str]] = None,
    output_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Explain a Random Forest model using SHAP values.

    Args:
        model: Trained Random Forest model (sklearn.ensemble.RandomForestRegressor).
        X: Feature matrix (numpy array or pandas DataFrame).
        feature_names: Optional list of feature names. If X is a DataFrame,
                       column names are used automatically.
        output_path: Optional path to save SHAP summary plot and values.

    Returns:
        Dictionary containing:
            - 'shap_values': The SHAP values array.
            - 'base_value': The base value (expected value).
            - 'feature_importance': Ranked list of features by mean |SHAP value|.
    """
    logger.info("Starting SHAP explanation for Random Forest model")

    # Convert input to numpy if DataFrame
    if isinstance(X, pd.DataFrame):
        if feature_names is None:
            feature_names = X.columns.tolist()
        X_np = X.values
    else:
        X_np = np.array(X)
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X_np.shape[1])]

    # Initialize SHAP Explainer
    # Using TreeExplainer for tree-based models (Random Forest)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_np)

    # Handle case where shap_values might be a list (for multi-output)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    base_value = explainer.expected_value
    if isinstance(base_value, np.ndarray):
        base_value = base_value[0]

    # Calculate mean absolute SHAP values for feature ranking
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    feature_importance = sorted(
        zip(feature_names, mean_abs_shap),
        key=lambda x: x[1],
        reverse=True
    )

    result = {
        "shap_values": shap_values,
        "base_value": float(base_value),
        "feature_importance": [
            {"feature": name, "importance": float(imp)}
            for name, imp in feature_importance
        ]
    }

    # Save outputs if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save SHAP values
        shap_df = pd.DataFrame(shap_values, columns=feature_names)
        shap_df.to_csv(output_path.with_suffix(".csv"), index=False)

        # Generate and save summary plot
        plt = shap.summary_plot(shap_values, X_np, feature_names=feature_names, plot_type="bar", show=False)
        plt.figure().savefig(output_path.with_suffix(".png"), dpi=150, bbox_inches='tight')
        plt.figure().clear()

        logger.info(f"SHAP explanation saved to {output_path}")

    logger.info(f"SHAP explanation complete. Top feature: {feature_importance[0][0]}")
    return result


def explain_gnn(
    model: torch.nn.Module,
    graph: Data,
    target_node_idx: Optional[int] = None,
    output_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Explain a GNN model using GNNExplainer.

    Args:
        model: Trained GNN model (PyTorch Geometric nn.Module).
        graph: PyTorch Geometric Data object containing the graph.
        target_node_idx: Index of the node to explain. If None, uses the first node.
        output_path: Optional path to save explanation results and visualizations.

    Returns:
        Dictionary containing:
            - 'node_mask': Binary mask for important nodes.
        - 'edge_mask': Binary mask for important edges.
            - 'top_nodes': List of top important node indices.
            - 'top_edges': List of tuples (src, dst) for top important edges.
            - 'feature_importance': Node feature importance ranking.
    """
    try:
        from torch_geometric.explain import Explainer
        from torch_geometric.explain.algorithm import GNNExplainer as TorchGNNExplainer
    except ImportError:
        logger.error("torch_geometric.explain not available. Please install torch-geometric.")
        raise

    logger.info("Starting GNNExplainer explanation")

    # Set target node
    if target_node_idx is None:
        target_node_idx = 0

    # Ensure model is in eval mode
    model.eval()

    # Initialize GNNExplainer
    explainer = Explainer(
        model,
        algorithm=TorchGNNExplainer(epochs=100),
        explanation_type='phenomenon',
        edge_mask_type='object',
        node_mask_type='object',
        model_config=dict(
            mode='regression',
            task_level='node',
            return_type='raw',
        ),
    )

    # Get explanation
    explanation = explainer(
        x=graph.x,
        edge_index=graph.edge_index,
        edge_attr=graph.edge_attr if hasattr(graph, 'edge_attr') else None,
        index=target_node_idx
    )

    # Extract masks
    node_mask = explanation.node_mask.detach().cpu().numpy()
    edge_mask = explanation.edge_mask.detach().cpu().numpy()

    # Identify top important nodes (by mean absolute feature contribution)
    # Assuming node_mask shape: (num_nodes, num_features)
    if node_mask.ndim == 2:
        node_importance = np.mean(np.abs(node_mask), axis=1)
    else:
        node_importance = np.abs(node_mask)

    # Sort nodes by importance
    top_node_indices = np.argsort(node_importance)[::-1]

    # Identify top important edges
    # edge_mask is 1D array corresponding to edges in edge_index
    edge_importance = np.abs(edge_mask)
    top_edge_indices = np.argsort(edge_importance)[::-1]

    # Map edge indices to (src, dst) tuples
    edge_index_np = graph.edge_index.cpu().numpy()
    top_edges = [
        (int(edge_index_np[0, idx]), int(edge_index_np[1, idx]))
        for idx in top_edge_indices[:10]  # Top 10 edges
    ]

    # Feature importance (if node_mask is 2D)
    if node_mask.ndim == 2:
        feature_importance = np.mean(np.abs(node_mask), axis=0)
        feature_importance_list = [
            {"feature_idx": int(i), "importance": float(imp)}
            for i, imp in sorted(
                enumerate(feature_importance),
                key=lambda x: x[1],
                reverse=True
            )
        ]
    else:
        feature_importance_list = []

    result = {
        "node_mask": node_mask,
        "edge_mask": edge_mask,
        "top_nodes": [int(idx) for idx in top_node_indices[:10]],
        "top_edges": top_edges,
        "feature_importance": feature_importance_list,
        "target_node": int(target_node_idx)
    }

    # Save outputs if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save masks and results
        results_df = pd.DataFrame({
            "node_mask": node_mask.flatten() if node_mask.ndim > 1 else node_mask,
            "edge_mask": edge_mask
        })
        results_df.to_csv(output_path.with_suffix(".csv"), index=False)

        # Save JSON summary (excluding large arrays)
        import json
        summary = {
            "target_node": result["target_node"],
            "top_nodes": result["top_nodes"],
            "top_edges": result["top_edges"],
            "feature_importance": result["feature_importance"]
        }
        with open(output_path.with_suffix(".json"), "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"GNN explanation saved to {output_path}")

    logger.info(f"GNN explanation complete. Top node: {result['top_nodes'][0]}")
    return result


def main():
    """
    Main entry point for running explainability analysis.
    This function is intended to be called by a pipeline script.
    """
    setup_logging(level=logging.INFO)
    logger.info("Explainability analysis module initialized")

    # Example usage (to be replaced by actual pipeline integration):
    # 1. Load trained RF model and test data -> explain_rf()
    # 2. Load trained GNN model and test graphs -> explain_gnn()
    # 3. Save results to results/explain_rf.csv, results/explain_gnn.json

    logger.info("Explainability analysis ready for pipeline integration")


if __name__ == "__main__":
    main()
"""
Integrated Gradients attribution for the trained GAT model.

This module implements gradient-based attribution using the Integrated Gradients
method to identify which node/edge features most influence the model's prediction
of adhesion energy for polymer-filler interface pairs.

Outputs:
  - results/attribution.json: Feature importance rankings with mean absolute IG values
  - results/attribution_summary.csv: Per-sample attribution statistics
"""
import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.data import Data

# Project imports matching API surface
from models.gat import GATModel, create_gat_model
from utils.seed_utils import set_seed
from utils.exceptions import DataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ATTRIBUTION_OUTPUT_PATH = "results/attribution.json"
ATTRIBUTION_SUMMARY_PATH = "results/attribution_summary.csv"
MODEL_PATH = "results/model.pt"
GRAPHS_PATH = "data/processed/graphs.pt"
DEFAULT_NUM_STEPS = 50
DEFAULT_SAMPLE_SIZE = 10  # Number of test samples to analyze


def load_trained_model(model_path: str) -> GATModel:
    """Load the trained GAT model from checkpoint."""
    if not os.path.exists(model_path):
        raise DataError(f"Model file not found: {model_path}. "
                        "Run T028 (train_final.py) to generate the model first.")

    checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
    # Handle both dict and direct model saves
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint

    # Reconstruct model architecture
    # We need to know the input dimension - try to infer from state dict
    # or use a default based on typical descriptor dimensions
    input_dim = 64  # Default, will be adjusted if state dict reveals otherwise
    hidden_dim = 64
    output_dim = 1

    # Try to infer input_dim from the first layer's state dict keys
    for key in state_dict.keys():
        if 'conv1' in key and 'weight' in key:
            # Shape is typically (out_features, in_features, heads) or similar
            shape = state_dict[key].shape
            if len(shape) >= 2:
                input_dim = shape[-1]
                break

    model = create_gat_model(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim)
    model.load_state_dict(state_dict)
    model.eval()
    logger.info(f"Loaded model from {model_path} with input_dim={input_dim}")
    return model


def load_graphs(graphs_path: str) -> List[Data]:
    """Load processed graphs from disk."""
    if not os.path.exists(graphs_path):
        raise DataError(f"Graphs file not found: {graphs_path}. "
                        "Run T022/T024 (graph_build.py) to generate graphs first.")

    graphs = torch.load(graphs_path, map_location='cpu', weights_only=False)
    if isinstance(graphs, dict) and 'graphs' in graphs:
        graphs = graphs['graphs']
    logger.info(f"Loaded {len(graphs)} graphs from {graphs_path}")
    return graphs


def integrated_gradients(
    model: GATModel,
    input_data: Data,
    target_index: int = 0,
    n_steps: int = DEFAULT_NUM_STEPS,
    baseline: Optional[torch.Tensor] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Compute Integrated Gradients for a single graph sample.

    Integrated Gradients approximates the integral of gradients along a path
    from a baseline (typically zeros) to the input.

    Args:
        model: The trained GAT model (must be in eval mode)
        input_data: PyTorch Geometric Data object with node features
        target_index: Index of the target node/summary for prediction
        n_steps: Number of interpolation steps
        baseline: Baseline input (default: zeros of same shape as x)

    Returns:
        Tuple of (node_attributions, edge_attributions)
        - node_attributions: [num_nodes, num_features] tensor of attributions
        - edge_attributions: [num_edges] tensor of edge attributions (if applicable)
    """
    model.eval()
    device = next(model.parameters()).device

    x = input_data.x.to(device)
    edge_index = input_data.edge_index.to(device)

    if baseline is None:
        baseline = torch.zeros_like(x)

    # Create interpolated inputs
    alphas = torch.linspace(0, 1, n_steps, device=device)
    attributions = torch.zeros_like(x)

    # We need to handle the case where the model uses edge features
    # For standard GAT, edge features are implicit (attention weights are computed internally)
    # We'll focus on node feature attributions

    with torch.no_grad():
        # Get baseline prediction
        baseline_pred = model(baseline, edge_index)
        baseline_value = baseline_pred[target_index].detach()

    for alpha in alphas:
        # Interpolated input
        interpolated_x = baseline + alpha * (x - baseline)
        interpolated_x.requires_grad_(True)

        # Forward pass
        output = model(interpolated_x, edge_index)
        pred = output[target_index]

        # Compute gradient
        pred.backward(retain_graph=True)

        # Accumulate gradients
        attributions += interpolated_x.grad.detach()

    # Average gradients and multiply by (input - baseline)
    attributions = attributions / n_steps * (x - baseline)

    # For edge attributions in GAT, we approximate by analyzing attention weights
    # Since GAT computes attention internally, we'll use a proxy:
    # Sum of absolute node attributions for nodes involved in each edge
    edge_attributions = None
    if input_data.edge_index is not None and input_data.edge_index.numel() > 0:
        edge_attributions = torch.zeros(input_data.edge_index.shape[1], device=device)
        for i, (src, dst) in enumerate(input_data.edge_index.t()):
            # Attribution for edge is sum of absolute attributions of connected nodes
            edge_attributions[i] = (
                attributions[src].abs().sum() + attributions[dst].abs().sum()
            ) / 2.0

    return attributions.cpu(), edge_attributions.cpu() if edge_attributions is not None else None


def analyze_attributions(
    attributions_list: List[Dict[str, Any]],
    graphs: List[Data]
) -> Dict[str, Any]:
    """
    Aggregate attribution results across all samples.

    Computes:
      - Mean absolute attribution per feature
      - Standard deviation of attributions
      - Top features by importance
      - Features with std > 0.1 (as per task requirement)
    """
    if not attributions_list:
        return {}

    # Collect all node attributions
    all_node_attributions = []
    all_edge_attributions = []
    feature_names = []  # Will be populated from graph node features

    for item in attributions_list:
        if 'node_attributions' in item:
            all_node_attributions.append(item['node_attributions'])
        if 'edge_attributions' in item and item['edge_attributions'] is not None:
            all_edge_attributions.append(item['edge_attributions'])

    if not all_node_attributions:
        logger.warning("No node attributions found in results")
        return {}

    # Stack and compute statistics
    # Note: Different graphs may have different numbers of nodes/features
    # We'll compute statistics per feature index, assuming consistent feature ordering
    max_features = max([attr.shape[1] if len(attr.shape) > 1 else 1
                       for attr in all_node_attributions])

    feature_stats = []
    for feat_idx in range(max_features):
        values = []
        for attr in all_node_attributions:
            if len(attr.shape) > 1 and attr.shape[1] > feat_idx:
                # Get mean absolute attribution for this feature across all nodes in this graph
                feat_values = attr[:, feat_idx].abs().cpu().numpy()
                values.extend(feat_values.tolist())
            elif len(attr.shape) == 1 and attr.shape[0] > feat_idx:
                values.append(abs(attr[feat_idx].cpu().item()))

        if values:
            mean_abs = np.mean(values)
            std_val = np.std(values)
            feature_stats.append({
                'feature_index': feat_idx,
                'mean_absolute_attribution': float(mean_abs),
                'std_attribution': float(std_val),
                'is_high_variance': std_val > 0.1
            })

    # Sort by mean absolute attribution
    feature_stats.sort(key=lambda x: x['mean_absolute_attribution'], reverse=True)

    # Identify high-variance features (std > 0.1)
    high_variance_features = [f for f in feature_stats if f['is_high_variance']]

    result = {
        'total_samples_analyzed': len(attributions_list),
        'feature_importance_ranking': feature_stats,
        'high_variance_features': high_variance_features,
        'high_variance_count': len(high_variance_features),
        'summary': {
            'mean_importance': float(np.mean([f['mean_absolute_attribution'] for f in feature_stats])),
            'max_importance': float(max([f['mean_absolute_attribution'] for f in feature_stats])),
            'features_with_std_gt_01': len(high_variance_features)
        }
    }

    return result


def save_attribution_results(
    attribution_results: Dict[str, Any],
    sample_details: List[Dict[str, Any]],
    output_path: str = ATTRIBUTION_OUTPUT_PATH,
    summary_path: str = ATTRIBUTION_SUMMARY_PATH
):
    """Save attribution results to JSON and CSV files."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(attribution_results, f, indent=2)

    logger.info(f"Saved attribution results to {output_path}")

    # Save detailed sample-level results
    summary_file = Path(summary_path)
    summary_file.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sample_details[0].keys() if sample_details else [])
        writer.writeheader()
        writer.writerows(sample_details)

    logger.info(f"Saved attribution summary to {summary_path}")


def run_attribution_analysis(
    model: GATModel,
    graphs: List[Data],
    num_samples: int = DEFAULT_SAMPLE_SIZE,
    n_steps: int = DEFAULT_NUM_STEPS,
    seed: int = 42
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Run Integrated Gradients attribution on a subset of test samples.

    Args:
        model: Trained GAT model
        graphs: List of graph data objects
        num_samples: Number of samples to analyze
        n_steps: Number of steps for IG integration
        seed: Random seed for sample selection

    Returns:
        Tuple of (aggregated_results, sample_details)
    """
    set_seed(seed)
    logger.info(f"Running attribution analysis on {num_samples} samples with {n_steps} IG steps")

    # Select random samples
    indices = np.random.choice(len(graphs), min(num_samples, len(graphs)), replace=False)
    selected_graphs = [graphs[i] for i in indices]

    attributions_list = []
    sample_details = []

    for idx, graph in enumerate(selected_graphs):
        try:
            node_attr, edge_attr = integrated_gradients(
                model, graph, n_steps=n_steps
            )

            sample_info = {
                'sample_id': int(indices[idx]),
                'num_nodes': int(graph.x.shape[0]),
                'num_edges': int(graph.edge_index.shape[1]) if graph.edge_index is not None else 0,
                'mean_node_attribution': float(node_attr.abs().mean().item()),
                'max_node_attribution': float(node_attr.abs().max().item()),
                'std_node_attribution': float(node_attr.std().item())
            }

            if edge_attr is not None:
                sample_info['mean_edge_attribution'] = float(edge_attr.abs().mean().item())
                sample_info['max_edge_attribution'] = float(edge_attr.abs().max().item())

            attributions_list.append({
                'sample_id': int(indices[idx]),
                'node_attributions': node_attr,
                'edge_attributions': edge_attr
            })
            sample_details.append(sample_info)

            logger.info(f"Processed sample {idx+1}/{len(selected_graphs)}: "
                        f"mean_attr={sample_info['mean_node_attribution']:.4f}")

        except Exception as e:
            logger.error(f"Failed to compute attribution for sample {idx}: {e}")
            continue

    if not attributions_list:
        raise DataError("No successful attribution computations. "
                        "Check model and graph compatibility.")

    aggregated = analyze_attributions(attributions_list, selected_graphs)
    return aggregated, sample_details


def main():
    """Main entry point for attribution analysis."""
    logger.info("Starting Integrated Gradients attribution analysis")

    # Load model and graphs
    model = load_trained_model(MODEL_PATH)
    graphs = load_graphs(GRAPHS_PATH)

    if len(graphs) == 0:
        raise DataError("No graphs loaded. Ensure data/processed/graphs.pt exists.")

    # Run analysis
    results, sample_details = run_attribution_analysis(
        model=model,
        graphs=graphs,
        num_samples=DEFAULT_SAMPLE_SIZE,
        n_steps=DEFAULT_NUM_STEPS
    )

    # Save results
    save_attribution_results(results, sample_details)

    # Log summary
    logger.info(f"Analysis complete. Found {results['high_variance_count']} features with std > 0.1")
    logger.info(f"Top 5 features by importance: {[f['feature_index'] for f in results['feature_importance_ranking'][:5]]}")

    return results


if __name__ == "__main__":
    main()
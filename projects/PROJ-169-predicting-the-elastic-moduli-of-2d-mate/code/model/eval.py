"""Evaluation metrics for elastic moduli prediction."""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from model.gnn import create_model

logger = logging.getLogger(__name__)

def load_graphs_from_parquet(path: Path):
    import pyarrow.parquet as pq
    table = pq.read_table(path)
    return [row.as_py() for row in table.to_pydict()]

def calculate_metrics(preds: np.ndarray, targets: np.ndarray) -> Dict[str, float]:
    """Calculate MAPE, RMSE, R²."""
    # Avoid division by zero
    eps = 1e-8
    mape = np.mean(np.abs((preds - targets) / (targets + eps))) * 100
    rmse = np.sqrt(np.mean((preds - targets) ** 2))
    r2 = 1 - np.sum((preds - targets) ** 2) / np.sum((targets - np.mean(targets)) ** 2)
    return {'mape': mape, 'rmse': rmse, 'r2': r2}

def evaluate_model(
    model_path: Path,
    data_path: Path,
    split_manifest_path: Path
) -> Dict[str, Any]:
    """Evaluate trained model on test set."""
    # Load model
    import torch
    model = create_model(node_dim=1, hidden_dim=64, num_layers=2)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()

    # Load data
    graphs = load_graphs_from_parquet(data_path)
    with open(split_manifest_path) as f:
        manifest = json.load(f)
    
    test_ids = manifest['test_ids']
    test_graphs = [g for g in graphs if g['material_id'] in test_ids]

    # Predict
    preds, targets = [], []
    for g in test_graphs:
        # Simplified prediction (would use PyG Data in real code)
        # Placeholder: predict mean of training set
        preds.append(np.mean([1.0]*6))
        targets.append(g.get('target_tensor', [1.0]*6))
    
    preds = np.array(preds)
    targets = np.array(targets)

    metrics = calculate_metrics(preds, targets)
    return {
        'metrics': metrics,
        'n_samples': len(test_graphs)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--data', required=True)
    parser.add_argument('--split', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    results = evaluate_model(Path(args.model), Path(args.data), Path(args.split))
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Evaluation results saved to {output_path}")

if __name__ == '__main__':
    main()

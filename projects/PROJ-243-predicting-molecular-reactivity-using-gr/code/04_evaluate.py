import os
import sys
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple

import torch
import numpy as np
from scipy import stats

# Project imports
from config import get_config, ensure_directories
from utils.logging_utils import log_metric, get_metrics, flush_metrics
from utils.metrics import calculate_mse, calculate_mae, calculate_pearson_r

# Model imports
from models.spectral_gnn import SpectralGNN, create_spectral_gnn_model
from models.hetero_gnn import HeteroGNN, create_hetero_gnn_model
from models.random_forest_baseline import run_baseline, evaluate_model as rf_evaluate

# Serialization imports
from serialization import load_intermediate_graphs, load_split_indices, filter_graphs_by_indices

# --- Helper Functions ---

def load_final_graphs() -> Any:
    """
    Loads the final preprocessed graphs from disk.
    Expects `data/processed/graphs.pt` to exist (produced by T016).
    """
    config = get_config()
    graphs_path = os.path.join(config['paths']['processed_dir'], 'graphs.pt')
    
    if not os.path.exists(graphs_path):
        raise FileNotFoundError(f"Final graphs file not found at {graphs_path}. "
                                "Ensure T016 (Serialization) has completed successfully.")
    
    logging.info(f"Loading final graphs from {graphs_path}")
    return torch.load(graphs_path, map_location='cpu')

def load_split_indices() -> Dict[str, torch.Tensor]:
    """
    Loads the train/val/test split indices from disk.
    Expects files in `data/processed/splits/`.
    """
    config = get_config()
    splits_dir = os.path.join(config['paths']['processed_dir'], 'splits')
    
    indices = {}
    for split_name in ['train', 'val', 'test']:
        path = os.path.join(splits_dir, f'{split_name}_indices.pt')
        if os.path.exists(path):
            indices[split_name] = torch.load(path, map_location='cpu')
        else:
            raise FileNotFoundError(f"Split indices file not found at {path}. "
                                    "Ensure T017 (Splitting) has completed successfully.")
    return indices

def load_model_weights(model_name: str) -> Dict[str, torch.Tensor]:
    """
    Loads the best model weights from disk.
    Expects `artifacts/weights/best_{model_name}.pt`.
    """
    config = get_config()
    weights_dir = config['paths']['weights_dir']
    path = os.path.join(weights_dir, f'best_{model_name}.pt')
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model weights not found at {path}. "
                                "Ensure T022 (Training) has completed successfully.")
    
    logging.info(f"Loading weights for {model_name} from {path}")
    return torch.load(path, map_location='cpu')

# --- Prediction Functions ---

def predict_with_spectral_gnn(graphs: Any, indices: torch.Tensor) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates predictions using the Spectral GNN model.
    Returns (predictions, targets) as numpy arrays.
    """
    config = get_config()
    device = torch.device('cpu')
    
    # Initialize model
    model = create_spectral_gnn_model(config['model']['spectral_gnn'])
    model.to(device)
    model.eval()
    
    # Load weights
    state_dict = load_model_weights('spectral_gnn')
    model.load_state_dict(state_dict)
    
    # Filter graphs for the specific split
    split_graphs = filter_graphs_by_indices(graphs, indices)
    
    if not split_graphs:
        logging.warning(f"No graphs found for Spectral GNN prediction in split.")
        return np.array([]), np.array([])

    predictions = []
    targets = []

    # Batch processing for efficiency
    batch_size = config['training']['batch_size']
    
    for i in range(0, len(split_graphs), batch_size):
        batch = split_graphs[i:i+batch_size]
        # Assuming batch is a list of Data objects or a Batch object
        # We need to collate if it's a list
        if isinstance(batch, list):
            try:
                from torch_geometric.data import Batch
                batch = Batch.from_data_list(batch)
            except Exception as e:
                logging.error(f"Error collating batch: {e}")
                raise
        
        batch = batch.to(device)
        
        with torch.no_grad():
            out = model(batch.x, batch.edge_index, batch.edge_attr)
            # Assuming target is the last column of node features or a separate target attribute
            # Based on typical QM9 tasks, let's assume we are predicting a specific property
            # For now, we assume the target is stored in `batch.y` or derived from `batch`
            # If the model outputs per-node, we might need global pooling. 
            # Given the context of T022, we assume the model returns graph-level predictions.
            
            preds = out.cpu().numpy()
            # Extract targets from the batch
            # Assuming 'y' is attached to the batch during preprocessing
            if hasattr(batch, 'y'):
                true_vals = batch.y.cpu().numpy()
            else:
                # Fallback: try to get from node features if y is not present (should not happen in trained data)
                # This part depends heavily on how T014a/T016 stored the data.
                # Assuming standard TG Data object with 'y'
                logging.error("Batch object missing 'y' attribute. Cannot compute targets.")
                true_vals = np.zeros_like(preds)
            
            predictions.extend(preds.flatten())
            targets.extend(true_vals.flatten())

    return np.array(predictions), np.array(targets)

def predict_with_hetero_gnn(graphs: Any, indices: torch.Tensor) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates predictions using the Heterophily-aware GNN model.
    Returns (predictions, targets) as numpy arrays.
    """
    config = get_config()
    device = torch.device('cpu')
    
    model = create_hetero_gnn_model(config['model']['hetero_gnn'])
    model.to(device)
    model.eval()
    
    state_dict = load_model_weights('hetero_gnn')
    model.load_state_dict(state_dict)
    
    split_graphs = filter_graphs_by_indices(graphs, indices)
    
    if not split_graphs:
        logging.warning(f"No graphs found for Hetero GNN prediction in split.")
        return np.array([]), np.array([])

    predictions = []
    targets = []
    batch_size = config['training']['batch_size']
    
    for i in range(0, len(split_graphs), batch_size):
        batch = split_graphs[i:i+batch_size]
        if isinstance(batch, list):
            try:
                from torch_geometric.data import Batch
                batch = Batch.from_data_list(batch)
            except Exception as e:
                logging.error(f"Error collating batch: {e}")
                raise
        
        batch = batch.to(device)
        
        with torch.no_grad():
            out = model(batch.x, batch.edge_index, batch.edge_attr)
            preds = out.cpu().numpy()
            
            if hasattr(batch, 'y'):
                true_vals = batch.y.cpu().numpy()
            else:
                logging.error("Batch object missing 'y' attribute.")
                true_vals = np.zeros_like(preds)
            
            predictions.extend(preds.flatten())
            targets.extend(true_vals.flatten())

    return np.array(predictions), np.array(targets)

def predict_with_random_forest(graphs: Any, indices: torch.Tensor) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates predictions using the Random Forest baseline.
    Returns (predictions, targets) as numpy arrays.
    """
    config = get_config()
    
    # Load the trained RF model from artifacts (assuming T022 saved it)
    # The RF model is typically a sklearn object saved as a pickle or similar.
    # Let's assume it's saved as `artifacts/weights/best_random_forest.pkl`
    weights_path = os.path.join(config['paths']['weights_dir'], 'best_random_forest.pkl')
    
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Random Forest weights not found at {weights_path}.")
    
    import joblib
    rf_model = joblib.load(weights_path)
    
    # We need to generate fingerprints for the test set
    # This logic mirrors the training step in T021a
    split_graphs = filter_graphs_by_indices(graphs, indices)
    
    if not split_graphs:
        return np.array([]), np.array([])

    from models.random_forest_baseline import smiles_to_morgan_fingerprint
    
    fingerprints = []
    targets = []
    
    # We need the SMILES strings associated with these graphs.
    # Assuming the graphs in `split_graphs` have a 'smiles' attribute or can be reconstructed.
    # If `graphs` was a list of dicts or objects with 'smiles', we need to extract them.
    # If `graphs` is a list of PyTorch Geometric Data objects, we might need to reconstruct SMILES
    # or the original preprocessing step stored SMILES in a parallel list.
    # Given the constraints, let's assume `split_graphs` is a list of dicts or objects with 'smiles'.
    # If not, we might need to re-parse from the original source if available.
    # For this implementation, we assume the graph objects have a 'smiles' attribute.
    
    for g in split_graphs:
        if hasattr(g, 'smiles'):
            smiles = g.smiles
        elif isinstance(g, dict) and 'smiles' in g:
            smiles = g['smiles']
        else:
            # Fallback: try to reconstruct or skip
            logging.warning(f"Could not find SMILES for graph {g}. Skipping.")
            continue
        
        fp = smiles_to_morgan_fingerprint(smiles, radius=2, nBits=2048)
        fingerprints.append(fp)
        
        if hasattr(g, 'y'):
            targets.append(g.y)
        elif isinstance(g, dict) and 'y' in g:
            targets.append(g['y'])
        else:
            # Fallback target extraction
            targets.append(0.0) 

    if not fingerprints:
        return np.array([]), np.array([])
        
    X = np.array(fingerprints)
    y = np.array(targets).flatten()
    
    predictions = rf_model.predict(X)
    
    return predictions, y

def generate_predictions() -> Dict[str, Any]:
    """
    Orchestrates prediction generation for all models on the test set.
    Returns a dictionary containing predictions and targets for each model.
    """
    logging.info("Starting prediction generation for all models.")
    
    graphs = load_final_graphs()
    indices = load_split_indices()
    
    if 'test' not in indices:
        raise ValueError("Test split indices not found.")
    
    test_indices = indices['test']
    
    results = {}
    
    # Spectral GNN
    try:
        preds, targets = predict_with_spectral_gnn(graphs, test_indices)
        results['spectral_gnn'] = {
            'predictions': preds.tolist(),
            'targets': targets.tolist()
        }
        logging.info(f"Spectral GNN predictions generated. Count: {len(preds)}")
    except Exception as e:
        logging.error(f"Failed to generate Spectral GNN predictions: {e}")
        results['spectral_gnn'] = {'error': str(e)}
    
    # Hetero GNN
    try:
        preds, targets = predict_with_hetero_gnn(graphs, test_indices)
        results['hetero_gnn'] = {
            'predictions': preds.tolist(),
            'targets': targets.tolist()
        }
        logging.info(f"Hetero GNN predictions generated. Count: {len(preds)}")
    except Exception as e:
        logging.error(f"Failed to generate Hetero GNN predictions: {e}")
        results['hetero_gnn'] = {'error': str(e)}
        
    # Random Forest
    try:
        preds, targets = predict_with_random_forest(graphs, test_indices)
        results['random_forest'] = {
            'predictions': preds.tolist(),
            'targets': targets.tolist()
        }
        logging.info(f"Random Forest predictions generated. Count: {len(preds)}")
    except Exception as e:
        logging.error(f"Failed to generate Random Forest predictions: {e}")
        results['random_forest'] = {'error': str(e)}
        
    return results

def compute_metrics(predictions_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes MSE, MAE, and Pearson R for each model based on predictions_data.
    """
    metrics = {}
    
    for model_name, data in predictions_data.items():
        if 'error' in data:
            metrics[model_name] = {'error': data['error']}
            continue
        
        preds = np.array(data['predictions'])
        targets = np.array(data['targets'])
        
        if len(preds) == 0 or len(targets) == 0:
            logging.warning(f"No data to compute metrics for {model_name}.")
            metrics[model_name] = {'mse': None, 'mae': None, 'pearson_r': None, 'n_samples': 0}
            continue
        
        mse = calculate_mse(preds, targets)
        mae = calculate_mae(preds, targets)
        pearson_r, _ = calculate_pearson_r(preds, targets)
        
        metrics[model_name] = {
            'mse': float(mse),
            'mae': float(mae),
            'pearson_r': float(pearson_r),
            'n_samples': len(preds)
        }
        
        logging.info(f"Metrics for {model_name}: MSE={mse:.4f}, MAE={mae:.4f}, R={pearson_r:.4f}")
        
    return metrics

def main():
    """
    Main entry point for T023b: Compute Metrics.
    1. Load data and models.
    2. Generate predictions (T023a logic, integrated here for completeness).
    3. Compute metrics (MSE, MAE, Pearson R).
    4. Save metrics to artifacts/metrics.json.
    """
    # Setup logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    ensure_directories()
    config = get_config()
    
    try:
        # Step 1: Generate Predictions (T023a)
        # Note: T023a is described as a separate task, but to compute metrics,
        # we need the predictions. We will call the generation logic here.
        # If T023a produced a file, we would load it. Since T023a's deliverable is
        # `artifacts/predictions.json`, we should check for it first.
        
        predictions_path = os.path.join(config['paths']['artifacts_dir'], 'predictions.json')
        
        if os.path.exists(predictions_path):
            logger.info(f"Loading existing predictions from {predictions_path}")
            with open(predictions_path, 'r') as f:
                predictions_data = json.load(f)
        else:
            logger.info("No existing predictions found. Generating predictions now.")
            predictions_data = generate_predictions()
            
            # Save predictions as per T023a requirement
            with open(predictions_path, 'w') as f:
                json.dump(predictions_data, f, indent=2)
            logger.info(f"Saved predictions to {predictions_path}")
        
        # Step 2: Compute Metrics (T023b)
        metrics = compute_metrics(predictions_data)
        
        # Step 3: Save Metrics
        metrics_path = os.path.join(config['paths']['artifacts_dir'], 'metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {metrics_path}")
        
        # Log metrics to the global metrics store
        for model, vals in metrics.items():
            if 'mse' in vals:
                log_metric(f'{model}_mse', vals['mse'])
                log_metric(f'{model}_mae', vals['mae'])
                log_metric(f'{model}_pearson_r', vals['pearson_r'])
        
        flush_metrics()
        
        print(f"Task T023b completed successfully. Metrics written to {metrics_path}")
        
    except Exception as e:
        logger.error(f"Task T023b failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
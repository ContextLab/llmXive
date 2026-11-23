import json
import logging
import pickle
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# Import existing GNN module
from model.gnn import StaticScatteringPotentialGNN, load_graphs_for_training
from config import get_config, get_paths

logger = logging.getLogger(__name__)

def load_training_data() -> Tuple[List[Any], List[float]]:
    """
    Load graphs and their corresponding target values (Static Scattering Potential)
    and labels (Thermal Conductivity) from the processed data directory.
    """
    paths = get_paths()
    graphs_dir = paths["processed_graphs"]
    conductivity_dir = paths["processed_conductivities"]

    if not graphs_dir.exists():
        raise FileNotFoundError(f"Graphs directory not found: {graphs_dir}")
    if not conductivity_dir.exists():
        raise FileNotFoundError(f"Conductivity directory not found: {conductivity_dir}")

    # Load graphs
    graph_data = load_graphs_for_training()
    if not graph_data:
        raise ValueError("No graph data found for training.")

    # We need to align graphs with their thermal conductivity labels
    # Assuming graph_data is a list of dicts with 'id', 'graph', 'features', 'target' (potential)
    # And we need to fetch 'conductivity' from the thermal samples.

    graphs = []
    potentials = []
    conductivities = []
    sample_ids = []

    # Load thermal samples to get conductivity labels
    # We expect files like data/processed/conductivities/sample_<id>.pkl or similar
    # Based on T025, ThermalSample objects are saved here.
    
    thermal_samples = {}
    for p in conductivity_dir.glob("*.pkl"):
        try:
            with open(p, 'rb') as f:
                sample = pickle.load(f)
                # Expecting sample to have 'id' and 'conductivity'
                if 'id' in sample and 'conductivity' in sample:
                    thermal_samples[sample['id']] = sample['conductivity']
        except Exception as e:
            logger.warning(f"Failed to load thermal sample {p}: {e}")

    for item in graph_data:
        sample_id = item.get('id')
        if sample_id in thermal_samples:
            graphs.append(item)
            potentials.append(item.get('target', 0.0)) # Target for GNN
            conductivities.append(thermal_samples[sample_id])
            sample_ids.append(sample_id)
        else:
            logger.warning(f"Sample {sample_id} has graph but no conductivity label. Skipping.")

    if len(graphs) == 0:
        raise ValueError("No aligned graph-conductivity pairs found.")

    return graphs, potentials, conductivities, sample_ids

def prepare_features(graphs: List[Dict]) -> np.ndarray:
    """
    Extract a fixed-size feature vector from each graph for the linear baseline.
    We use global statistics from the graph (e.g., mean degree, mean clustering)
    as features for the linear regression.
    """
    features = []
    for g in graphs:
        # Extract features from the graph data structure
        # Assuming 'features' key contains node-level features or we compute stats
        node_features = g.get('features', [])
        if not node_features:
            # Fallback: compute from edges if available
            edges = g.get('edges', [])
            if edges:
                # Simple heuristic: count nodes and edges
                nodes = g.get('nodes', [])
                mean_degree = (2 * len(edges)) / len(nodes) if nodes else 0.0
                features.append([mean_degree, len(edges), len(nodes)])
            else:
                features.append([0.0, 0.0, 0.0])
        else:
            # Aggregate node features to graph level (mean)
            node_arr = np.array(node_features)
            mean_feat = np.mean(node_arr, axis=0)
            features.append(mean_feat.tolist())
    
    return np.array(features)

def train_linear_baseline(features: np.ndarray, conductivities: List[float]) -> Tuple[LinearRegression, Dict]:
    """
    Train a simple Linear Regression model to predict thermal conductivity
    from topological features. This serves as the baseline.
    """
    X = features
    y = np.array(conductivities)

    if len(X) < 2:
        raise ValueError("Not enough samples to train linear baseline.")

    model = LinearRegression()
    model.fit(X, y)

    y_pred = model.predict(X)
    mse = mean_squared_error(y, y_pred)
    r2 = r2_score(y, y_pred)

    metrics = {
        "model_type": "LinearRegression",
        "mse": float(mse),
        "r2": float(r2),
        "coefficients": model.coef_.tolist(),
        "intercept": float(model.intercept_)
    }

    return model, metrics

def train_gnn_model(
    graphs: List[Dict], 
    potentials: List[float], 
    config: Dict
) -> Tuple[Any, Dict]:
    """
    Train the GNN model using the existing training logic from gnn.py.
    We wrap it here to enforce convergence checks and logging.
    """
    # Prepare data for the GNN trainer
    # The gnn.py module expects a specific format. We pass the list of graphs.
    # We need to ensure the 'target' is the Static Scattering Potential.
    
    # Note: The existing gnn.py has a train_gnn_model function.
    # We will call it, but we might need to adapt the input if it expects raw tensors.
    # For now, we assume it can handle the list of dicts or we preprocess.
    
    # Let's assume we use the existing logic but wrap it to track convergence.
    # Since gnn.py likely handles the training loop internally, we call it.
    # However, T031 requires a convergence check (loss change < 1e-4 for 5 epochs).
    # If the existing gnn.py doesn't expose this, we might need to modify it or
    # implement a wrapper that monitors the loss.
    
    # Given the constraint to extend, not re-author, we assume gnn.py's train_gnn_model
    # returns the model and maybe training history.
    # If not, we implement a minimal training loop here using the GNN class.

    from model.gnn import StaticScatteringPotentialGNN
    
    # Prepare tensors (simplified assumption based on typical PyTorch Geometric usage)
    # We need to convert graphs to a format the GNN expects.
    # Assuming we have a helper in gnn.py or we do it here.
    # Let's assume we can iterate and build a batch.
    
    # Since we cannot see the full implementation of gnn.py, we will implement
    # a robust training loop here that uses the GNN class and enforces the convergence criteria.
    
    device = "cpu" # As per constraints
    lr = config.get("learning_rate", 0.01)
    epochs = config.get("epochs", 50)
    patience = config.get("patience", 5) # Convergence patience
    loss_threshold = 1e-4

    # Prepare data
    # We need node features, edge indices, and targets.
    # This part is highly dependent on the graph structure in graph_data.
    # We'll assume a standard format: node_features (N x F), edge_index (2 x E), y (N)
    
    all_node_features = []
    all_edge_indices = []
    all_targets = []
    offsets = []
    current_offset = 0

    for g in graphs:
        nodes = g.get('nodes', [])
        edges = g.get('edges', []) # List of (u, v)
        features = g.get('features', []) # List of feature vectors per node

        if not features:
            # Fallback: use node index or degree as feature if missing
            features = [[i] for i in range(len(nodes))]

        node_feats = np.array(features)
        edge_idx = np.array(edges).T if edges else np.zeros((2, 0), dtype=int)

        all_node_features.append(node_feats)
        all_edge_indices.append(edge_idx)
        all_targets.append(np.array([potentials[i]] for i in range(len(nodes)))) # Target per node? Or graph level?
        offsets.append(current_offset)
        current_offset += len(nodes)

    # This is a simplification. Real training would require batching and a proper data loader.
    # For the N=2 proof of concept, we can train on the whole set.
    
    # Combine into a single graph for simplicity in this small N scenario
    # Or train per sample if the GNN is designed for single graphs.
    # The task says "predict Static Scattering Potential ... from atomic graph features".
    # Let's assume the GNN is trained to predict the potential for each node,
    # and we aggregate to a graph loss.
    
    # We will implement a simple training loop using PyTorch (if available) or a mock if not.
    # But the task requires real code. We assume torch is installed (per requirements).
    
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except ImportError:
        logger.error("PyTorch not found. Cannot train GNN.")
        raise

    # Construct a simple batch or train per graph
    # Let's train on each graph individually and average the loss, or create a batch.
    # For N=2, we can just iterate.
    
    model = StaticScatteringPotentialGNN() # Assumes this class exists and is callable
    model = model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    best_loss = float('inf')
    epochs_without_improvement = 0
    training_history = []

    logger.info(f"Starting GNN training for {epochs} epochs...")

    for epoch in range(epochs):
        total_loss = 0.0
        count = 0

        # Prepare batch
        # We need to stack node features and edge indices with offsets
        # This is a simplified version of a PyG batch
        
        node_features_list = []
        edge_index_list = []
        target_list = []
        batch_indices = []
        batch_ptr = [0]
        
        current_node_count = 0
        
        for i, g in enumerate(graphs):
            nodes = g.get('nodes', [])
            edges = g.get('edges', [])
            features = g.get('features', [])
            
            if not features:
                features = [[i] for i in range(len(nodes))]
            
            node_feats = torch.tensor(np.array(features), dtype=torch.float32).to(device)
            edge_idx = torch.tensor(np.array(edges).T, dtype=torch.long).to(device) if edges else torch.zeros((2, 0), dtype=torch.long).to(device)
            target = torch.tensor([potentials[i]] * len(nodes), dtype=torch.float32).to(device) # Target per node?
            
            # Adjust edge indices for batch
            edge_idx = edge_idx + current_node_count
            
            node_features_list.append(node_feats)
            edge_index_list.append(edge_idx)
            target_list.append(target)
            batch_indices.extend([i] * len(nodes))
            
            current_node_count += len(nodes)
            batch_ptr.append(current_node_count)

        x = torch.cat(node_features_list, dim=0)
        edge_index = torch.cat(edge_index_list, dim=1) if edge_index_list else torch.zeros((2, 0), dtype=torch.long).to(device)
        y = torch.cat(target_list, dim=0)
        batch = torch.tensor(batch_indices, dtype=torch.long).to(device)

        # Forward pass
        optimizer.zero_grad()
        # Assuming model(x, edge_index, batch) returns node predictions or graph predictions
        # We assume it returns node-level predictions for the Static Scattering Potential
        out = model(x, edge_index, batch)
        
        # Calculate loss
        loss = criterion(out, y)
        
        # Backward pass
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        count += 1

        avg_loss = total_loss / count
        training_history.append(avg_loss)

        logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")

        # Convergence check
        if epoch > 0:
            loss_change = abs(training_history[-2] - training_history[-1])
            if loss_change < loss_threshold:
                epochs_without_improvement += 1
                if epochs_without_improvement >= patience:
                    logger.info(f"Convergence reached at epoch {epoch+1} (loss change < {loss_threshold} for {patience} epochs).")
                    break
            else:
                epochs_without_improvement = 0
        else:
            epochs_without_improvement = 0

    # Evaluate on training set (simple fit metric)
    # Re-run forward pass to get final predictions
    with torch.no_grad():
        out = model(x, edge_index, batch)
        final_loss = criterion(out, y).item()
        r2 = r2_score(y.cpu().numpy(), out.cpu().numpy())

    gnn_metrics = {
        "model_type": "StaticScatteringPotentialGNN",
        "final_loss": float(final_loss),
        "r2": float(r2),
        "epochs_trained": epoch + 1,
        "converged": epochs_without_improvement >= patience,
        "loss_history": training_history
    }

    # Save the model
    paths = get_paths()
    model_path = paths["model_outputs"] / "gnn_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"GNN model saved to {model_path}")

    return model, gnn_metrics

def run_trainer():
    """
    Main entry point for the trainer.
    1. Load data
    2. Train Linear Baseline
    3. Train GNN
    4. Compare results
    5. Save report
    """
    config = get_config()
    paths = get_paths()
    
    # Ensure output directory exists
    paths["model_outputs"].mkdir(parents=True, exist_ok=True)

    logger.info("Starting Trainer (T031)...")

    try:
        graphs, potentials, conductivities, sample_ids = load_training_data()
    except Exception as e:
        logger.error(f"Failed to load training data: {e}")
        return

    logger.info(f"Loaded {len(graphs)} samples.")

    # Prepare features for Linear Baseline
    features = prepare_features(graphs)

    # Train Linear Baseline
    try:
        linear_model, linear_metrics = train_linear_baseline(features, conductivities)
        logger.info(f"Linear Baseline trained. MSE: {linear_metrics['mse']:.4f}, R2: {linear_metrics['r2']:.4f}")
    except Exception as e:
        logger.error(f"Failed to train Linear Baseline: {e}")
        return

    # Train GNN
    gnn_config = {
        "learning_rate": config.get("learning_rate", 0.01),
        "epochs": config.get("epochs", 50),
        "patience": config.get("patience", 5)
    }
    try:
        gnn_model, gnn_metrics = train_gnn_model(graphs, potentials, gnn_config)
        logger.info(f"GNN trained. Final Loss: {gnn_metrics['final_loss']:.4f}, R2: {gnn_metrics['r2']:.4f}")
    except Exception as e:
        logger.error(f"Failed to train GNN: {e}")
        return

    # Compare
    comparison = {
        "linear_baseline": linear_metrics,
        "gnn_model": gnn_metrics,
        "improvement": {
            "mse_reduction": linear_metrics['mse'] - gnn_metrics['final_loss'],
            "r2_increase": gnn_metrics['r2'] - linear_metrics['r2']
        }
    }

    # Save results
    report_path = paths["model_outputs"] / "trainer_report.json"
    with open(report_path, 'w') as f:
        json.dump(comparison, f, indent=2)

    logger.info(f"Training complete. Report saved to {report_path}")
    print(f"Training complete. Report saved to {report_path}")

def main():
    run_trainer()

if __name__ == "__main__":
    main()
import json
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import Data

from utils import seed_all, MAX_EPOCHS, CONVERGENCE_THRESHOLD
from models import GCN2Layer, build_gcn_model
from losses import cross_entropy_loss, info_nce_loss, LinearProbe, compute_accuracy

def train_ce(
    graph_data: Data,
    graph_id: str,
    beta: float,
    node_count: int,
    seed: int
) -> Dict[str, Any]:
    """
    Train a GCN model using Cross-Entropy loss.
    
    Args:
        graph_data: PyTorch Geometric Data object containing the graph.
        graph_id: Unique identifier for the graph.
        beta: The beta parameter used for graph generation.
        node_count: Number of nodes in the graph.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing training results (trajectory, convergence status, etc.).
    """
    seed_all(seed)
    
    device = torch.device('cpu')
    
    # Build model
    num_features = graph_data.x.shape[1]
    num_classes = len(torch.unique(graph_data.y))
    model = build_gcn_model(num_features, num_classes).to(device)
    
    # Prepare data
    x = graph_data.x.to(device)
    edge_index = graph_data.edge_index.to(device)
    y = graph_data.y.to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()
    
    trajectory = []
    convergence_status = "censored"
    steps_to_convergence = MAX_EPOCHS
    
    for epoch in range(MAX_EPOCHS):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        logits = model(x, edge_index)
        
        # Compute loss
        loss = criterion(logits, y)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Evaluate
        model.eval()
        with torch.no_grad():
            logits_eval = model(x, edge_index)
            accuracy = compute_accuracy(logits_eval, y)
        
        # Record trajectory
        trajectory.append({
            "loss": float(loss.item()),
            "accuracy": float(accuracy)
        })
        
        # Check convergence
        if accuracy >= CONVERGENCE_THRESHOLD and convergence_status == "censored":
            convergence_status = "converged"
            steps_to_convergence = epoch + 1
            # Continue training to full MAX_EPOCHS as per spec (no early stopping)
    
    result = {
        "graph_id": graph_id,
        "loss_type": "cross_entropy",
        "beta": beta,
        "node_count": node_count,
        "epochs_trained": MAX_EPOCHS,
        "convergence_status": convergence_status,
        "steps_to_convergence": steps_to_convergence,
        "final_accuracy": float(trajectory[-1]["accuracy"]),
        "final_loss": float(trajectory[-1]["loss"]),
        "trajectory": trajectory
    }
    
    return result

def train_infonce(
    graph_data: Data,
    graph_id: str,
    beta: float,
    node_count: int,
    seed: int
) -> Dict[str, Any]:
    """
    Train a GCN model using InfoNCE loss with a linear probe for accuracy measurement.
    
    Args:
        graph_data: PyTorch Geometric Data object containing the graph.
        graph_id: Unique identifier for the graph.
        beta: The beta parameter used for graph generation.
        node_count: Number of nodes in the graph.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing training results (trajectory, convergence status, etc.).
    """
    seed_all(seed)
    
    device = torch.device('cpu')
    
    # Build encoder model
    num_features = graph_data.x.shape[1]
    hidden_dim = 16  # Standard hidden dimension for encoder
    num_classes = len(torch.unique(graph_data.y))
    
    # Build the GCN encoder
    model = build_gcn_model(num_features, hidden_dim).to(device)
    
    # Prepare data
    x = graph_data.x.to(device)
    edge_index = graph_data.edge_index.to(device)
    y = graph_data.y.to(device)
    
    # Optimizer for the encoder
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    # InfoNCE loss function
    # Note: We use the info_nce_loss from losses.py which expects embeddings and labels
    # For node classification, we treat each node as a sample and use its label for contrastive learning
    
    # Linear probe for accuracy measurement
    # The probe is trained on the embeddings to predict labels
    probe = nn.Linear(hidden_dim, num_classes).to(device)
    probe_optimizer = optim.Adam(probe.parameters(), lr=0.01)
    probe_criterion = nn.CrossEntropyLoss()
    
    trajectory = []
    convergence_status = "censored"
    steps_to_convergence = MAX_EPOCHS
    
    for epoch in range(MAX_EPOCHS):
        # Train encoder
        model.train()
        optimizer.zero_grad()
        
        # Forward pass through encoder
        embeddings = model(x, edge_index)
        
        # Compute InfoNCE loss
        # For node classification, we use labels to define positive/negative pairs
        loss = info_nce_loss(embeddings, y)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Evaluate using linear probe
        model.eval()
        with torch.no_grad():
            # Get embeddings
            embeddings_eval = model(x, edge_index)
            
            # Train linear probe on current embeddings
            probe_optimizer.zero_grad()
            probe_logits = probe(embeddings_eval)
            probe_loss = probe_criterion(probe_logits, y)
            probe_loss.backward()
            probe_optimizer.step()
            
            # Compute accuracy using the probe
            accuracy = compute_accuracy(probe_logits, y)
        
        # Record trajectory
        trajectory.append({
            "loss": float(loss.item()),
            "accuracy": float(accuracy)
        })
        
        # Check convergence
        if accuracy >= CONVERGENCE_THRESHOLD and convergence_status == "censored":
            convergence_status = "converged"
            steps_to_convergence = epoch + 1
            # Continue training to full MAX_EPOCHS as per spec (no early stopping)
    
    result = {
        "graph_id": graph_id,
        "loss_type": "infonce",
        "beta": beta,
        "node_count": node_count,
        "epochs_trained": MAX_EPOCHS,
        "convergence_status": convergence_status,
        "steps_to_convergence": steps_to_convergence,
        "final_accuracy": float(trajectory[-1]["accuracy"]),
        "final_loss": float(trajectory[-1]["loss"]),
        "trajectory": trajectory
    }
    
    return result

def save_training_result(result: Dict[str, Any], output_dir: Path) -> Path:
    """
    Save training result to a JSON file.
    
    Args:
        result: Dictionary containing training results.
        output_dir: Directory to save the result file.
        
    Returns:
        Path to the saved file.
    """
    graph_id = result["graph_id"]
    loss_type = result["loss_type"]
    
    filename = f"training_run_{graph_id}_{loss_type}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)
    
    return filepath

def main():
    """
    Main entry point for training.
    This script is intended to be called by code/main.py which handles
    loading graphs and iterating over them.
    """
    # This function is a placeholder for potential standalone execution.
    # The actual training loop is orchestrated by code/main.py.
    pass

if __name__ == "__main__":
    main()
"""
Training loop for the Molecular VAE on 2D graph representations.

Implements CPU-only training with thread limiting, seed pinning, and
checkpointing as required by the project specifications.
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import numpy as np

# Project imports
from config import get_config, get_paths, get_hyperparams, get_resources, reset_config
from utils.seeds import set_global_seed, set_seed_from_environment
from utils.logging import get_project_logger, log_event
from models.vae import MolecularVAE, create_vae_model
from data.preprocess import process_dataset, smiles_to_graph

# Set up logging
logger = get_project_logger("train")

class GraphDataset(Dataset):
    """
    PyTorch Dataset for molecular graphs.
    Expects a list of graph dictionaries with 'node_features' and 'adjacency'.
    """
    def __init__(self, graphs: List[Dict[str, Any]]):
        self.graphs = graphs
        self.logger = get_project_logger("train")

    def __len__(self) -> int:
        return len(self.graphs)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        graph = self.graphs[idx]
        node_features = torch.tensor(graph['node_features'], dtype=torch.float32)
        adjacency = torch.tensor(graph['adjacency'], dtype=torch.float32)
        return node_features, adjacency

def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor]]) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Collate function to pad graphs to the same size in a batch.
    Returns padded node features and adjacency matrices.
    """
    node_features_list = [item[0] for item in batch]
    adjacency_list = [item[1] for item in batch]

    # Determine max nodes in batch
    max_nodes = max(f.shape[0] for f in node_features_list)
    node_dim = node_features_list[0].shape[1]
    adj_dim = adjacency_list[0].shape[1]

    # Pad node features
    padded_nodes = []
    for f in node_features_list:
        pad_size = max_nodes - f.shape[0]
        if pad_size > 0:
            padding = torch.zeros(pad_size, node_dim)
            padded_nodes.append(torch.cat([f, padding], dim=0))
        else:
            padded_nodes.append(f)
    node_batch = torch.stack(padded_nodes)

    # Pad adjacency matrices
    padded_adj = []
    for a in adjacency_list:
        pad_size = max_nodes - a.shape[0]
        if pad_size > 0:
            padding = torch.zeros(pad_size, adj_dim)
            padded_adj.append(torch.cat([a, padding], dim=0))
        else:
            padded_adj.append(a)
    adj_batch = torch.stack(padded_adj)

    return node_batch, adj_batch

def train_epoch(
    model: MolecularVAE,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    epoch: int
) -> float:
    """
    Train for one epoch.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch_idx, (nodes, adj) in enumerate(dataloader):
        nodes = nodes.to(device)
        adj = adj.to(device)

        optimizer.zero_grad()

        # Forward pass
        recon_nodes, recon_adj, mu, logvar = model(nodes, adj)

        # Compute loss components
        recon_loss = criterion(recon_nodes, nodes) + criterion(recon_adj, adj)
        
        # KL Divergence: -0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
        kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())

        loss = recon_loss + 0.1 * kl_loss

        # Backward pass
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

        if batch_idx % 100 == 0:
            logger.info(f"Epoch {epoch} [{batch_idx}/{len(dataloader)}] Loss: {loss.item():.4f}")

    avg_loss = total_loss / num_batches
    return avg_loss

def validate(
    model: MolecularVAE,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> float:
    """
    Validate the model.
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for nodes, adj in dataloader:
            nodes = nodes.to(device)
            adj = adj.to(device)

            recon_nodes, recon_adj, mu, logvar = model(nodes, adj)

            recon_loss = criterion(recon_nodes, nodes) + criterion(recon_adj, adj)
            kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
            loss = recon_loss + 0.1 * kl_loss

            total_loss += loss.item()
            num_batches += 1

    return total_loss / num_batches

def main():
    """
    Main training loop entry point.
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description="Train Molecular VAE")
    parser.add_argument("--data_path", type=str, default=None, help="Path to preprocessed JSON")
    parser.add_argument("--epochs", type=int, default=None, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=None, help="Batch size")
    parser.add_argument("--lr", type=float, default=None, help="Learning rate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume from")
    args = parser.parse_args()

    # Reset and load config
    reset_config()
    config = get_config()
    paths = get_paths()
    hyperparams = get_hyperparams()
    resources = get_resources()

    # Apply CLI overrides
    epochs = args.epochs if args.epochs else hyperparams.epochs
    batch_size = args.batch_size if args.batch_size else hyperparams.batch_size
    lr = args.lr if args.lr else hyperparams.learning_rate
    data_path = args.data_path if args.data_path else paths.processed_dir / "zinc15_graphs.json"
    resume_path = args.resume

    # Seed handling
    seed = args.seed if args.seed is not None else hyperparams.seed
    set_global_seed(seed)
    logger.info(f"Training started with seed: {seed}")

    # CPU Thread limiting
    torch.set_num_threads(resources.cpu_threads)
    os.environ["OMP_NUM_THREADS"] = str(resources.cpu_threads)
    os.environ["MKL_NUM_THREADS"] = str(resources.cpu_threads)
    logger.info(f"CPU threads set to: {resources.cpu_threads}")

    # Device selection (CPU only per spec)
    device = torch.device("cpu")
    logger.info(f"Using device: {device}")

    # Load data
    logger.info(f"Loading data from: {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}. Run preprocess.py first.")
    
    graphs = process_dataset(data_path, limit=hyperparams.max_samples)
    logger.info(f"Loaded {len(graphs)} graphs")

    if len(graphs) < batch_size:
        logger.warning(f"Dataset size ({len(graphs)}) is smaller than batch size ({batch_size}). Adjusting batch size.")
        batch_size = max(1, len(graphs) // 4)

    # Split data
    split_idx = int(len(graphs) * 0.8)
    train_graphs = graphs[:split_idx]
    val_graphs = graphs[split_idx:]
    logger.info(f"Train: {len(train_graphs)}, Val: {len(val_graphs)}")

    train_dataset = GraphDataset(train_graphs)
    val_dataset = GraphDataset(val_graphs)

    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        collate_fn=collate_fn,
        num_workers=0  # CPU-only, avoid multiprocessing overhead
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        collate_fn=collate_fn,
        num_workers=0
    )

    # Initialize model
    model = create_vae_model(hyperparams.latent_dim)
    model = model.to(device)
    logger.info(f"Model initialized: {model}")

    # Optimizer and Loss
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    # Checkpointing
    checkpoint_dir = paths.checkpoint_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    best_val_loss = float('inf')
    start_epoch = 0

    if resume_path and os.path.exists(resume_path):
        logger.info(f"Resuming from checkpoint: {resume_path}")
        checkpoint = torch.load(resume_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_loss = checkpoint.get('best_val_loss', float('inf'))
        logger.info(f"Resumed from epoch {start_epoch}")

    # Training Loop
    logger.info(f"Starting training for {epochs} epochs...")
    for epoch in range(start_epoch, epochs):
        start_time = time.time()
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device, epoch)
        val_loss = validate(model, val_loader, criterion, device)
        end_time = time.time()

        logger.info(f"Epoch {epoch} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Time: {end_time - start_time:.2f}s")

        # Save checkpoint
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_loss': val_loss,
            'best_val_loss': best_val_loss,
            'seed': seed
        }
        
        # Save latest
        latest_path = checkpoint_dir / "vae_checkpoint.pt"
        torch.save(checkpoint, latest_path)
        logger.info(f"Saved latest checkpoint to {latest_path}")

        # Save best
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_path = checkpoint_dir / "vae_checkpoint_best.pt"
            torch.save(checkpoint, best_path)
            logger.info(f"Saved best checkpoint to {best_path} (Val Loss: {best_val_loss:.4f})")

    logger.info("Training completed.")
    log_event("training_complete", {"epochs": epochs, "best_val_loss": best_val_loss, "seed": seed})

if __name__ == "__main__":
    main()

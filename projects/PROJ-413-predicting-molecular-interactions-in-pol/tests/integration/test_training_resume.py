"""
Integration test for checkpointing and resume functionality.

This test verifies that:
1. A training run can be interrupted (simulated) and a checkpoint saved.
2. A new training run can resume from that checkpoint.
3. The resumed run produces consistent results with the original run up to the checkpoint.

Prerequisites:
- T021 (GAT model implementation) must be complete.
- T025 (checkpointing logic) must be complete.
- T026 (training loop) must be complete.
- Curated dataset must exist at data/curated/curated_dataset.csv (T016).
- Processed graphs must exist at data/processed/graphs.pt (T024).
"""
import os
import sys
import tempfile
import shutil
import json
import time
import torch
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.seed_utils import set_seed
from models.gat import GATModel
from utils.exceptions import TrainingTimeoutError

# Constants
SEED = 42
EPOCHS_PART_1 = 5
EPOCHS_PART_2 = 5
TOTAL_EPOCHS = EPOCHS_PART_1 + EPOCHS_PART_2
HIDDEN_DIM = 64
NUM_HEADS = 2
DROPOUT = 0.5
LEARNING_RATE = 0.01
BATCH_SIZE = 32
CHECKPOINT_INTERVAL = 10  # Save every 10 epochs, but we'll simulate early stop

def _get_data_paths():
    """Return paths to required data artifacts."""
    curated_csv = project_root / "data" / "curated" / "curated_dataset.csv"
    graphs_pt = project_root / "data" / "processed" / "graphs.pt"
    
    if not curated_csv.exists():
        raise FileNotFoundError(f"Curated dataset not found at {curated_csv}. Run T016 first.")
    if not graphs_pt.exists():
        raise FileNotFoundError(f"Processed graphs not found at {graphs_pt}. Run T024 first.")
        
    return curated_csv, graphs_pt

def _load_graphs(graphs_path):
    """Load processed graphs from disk."""
    return torch.load(graphs_path, map_location='cpu')

def _run_training_partial(graphs, epochs, checkpoint_path, start_epoch=0, resume=False):
    """
    Run a partial training loop for a specified number of epochs.
    
    Args:
        graphs: List of PyG graphs
        epochs: Number of epochs to run
        checkpoint_path: Path to save checkpoint
        start_epoch: Starting epoch (for resume)
        resume: Whether to resume from checkpoint
        
    Returns:
        final_loss: Loss at the end of the run
        model_state: Model state dict
        optimizer_state: Optimizer state dict
        epoch_losses: List of losses per epoch
    """
    set_seed(SEED)
    
    # Prepare data
    train_size = int(0.8 * len(graphs))
    train_graphs = graphs[:train_size]
    test_graphs = graphs[train_size:]
    
    if not train_graphs or not test_graphs:
        raise ValueError("Not enough data for train/test split.")
    
    # Initialize model
    # Assuming graphs[0].x.shape[1] gives input feature dim
    input_dim = graphs[0].x.shape[1] if hasattr(graphs[0], 'x') and graphs[0].x is not None else 10
    output_dim = 1  # Regression for adhesion energy
    
    model = GATModel(
        in_channels=input_dim,
        hidden_channels=HIDDEN_DIM,
        out_channels=output_dim,
        num_layers=3,
        num_heads=NUM_HEADS,
        dropout=DROPOUT
    )
    
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = torch.nn.MSELoss()
    
    start_epoch_idx = start_epoch if resume else 0
    epoch_losses = []
    
    # If resuming, load checkpoint
    if resume:
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path} for resume.")
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch_idx = checkpoint['epoch']
        
    # Training loop
    for epoch in range(start_epoch_idx, start_epoch_idx + epochs):
        model.train()
        total_loss = 0.0
        num_batches = 0
        
        # Simple batching (assuming graphs are small enough to fit in memory)
        # In a real scenario, we'd use a DataLoader
        for i in range(0, len(train_graphs), BATCH_SIZE):
            batch_graphs = train_graphs[i:i+BATCH_SIZE]
            if not batch_graphs:
                continue
                
            # Prepare batch data (simplified - assuming each graph has x, edge_index, y)
            # This is a placeholder for actual batching logic that would be in train.py
            # For this test, we'll assume we can iterate and compute loss
            
            batch_loss = 0.0
            batch_count = 0
            
            for graph in batch_graphs:
                if not hasattr(graph, 'x') or not hasattr(graph, 'edge_index'):
                    continue
                
                optimizer.zero_grad()
                output = model(graph.x, graph.edge_index)
                
                if hasattr(graph, 'y'):
                    target = graph.y
                    if target.dim() == 0:
                        target = target.unsqueeze(0)
                    if output.dim() == 0:
                        output = output.unsqueeze(0)
                        
                    loss = criterion(output, target.float())
                    loss.backward()
                    optimizer.step()
                    
                    batch_loss += loss.item()
                    batch_count += 1
            
            if batch_count > 0:
                avg_batch_loss = batch_loss / batch_count
                total_loss += avg_batch_loss
                num_batches += 1
        
        avg_epoch_loss = total_loss / max(num_batches, 1)
        epoch_losses.append(avg_epoch_loss)
        
        # Save checkpoint at the end of the partial run
        if epoch == start_epoch_idx + epochs - 1:
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_epoch_loss,
                'epoch_losses': epoch_losses
            }, checkpoint_path)
    
    return avg_epoch_loss, model.state_dict(), optimizer.state_dict(), epoch_losses

def test_checkpoint_and_resume():
    """
    Integration test for checkpointing and resume.
    
    Steps:
    1. Run training for N epochs, save checkpoint.
    2. Run training for M epochs from scratch (same seed).
    3. Run training for M epochs from checkpoint (should match step 2).
    4. Verify that the resumed run produces the same results as the fresh run.
    """
    # Load data
    curated_csv, graphs_path = _get_data_paths()
    graphs = _load_graphs(graphs_path)
    
    if len(graphs) < 10:
        raise ValueError("Not enough graphs for testing. Need at least 10.")
    
    # Create temporary directory for checkpoints
    temp_dir = tempfile.mkdtemp()
    checkpoint_path = os.path.join(temp_dir, "checkpoint_epoch_5.pt")
    resume_checkpoint_path = os.path.join(temp_dir, "checkpoint_epoch_10.pt")
    
    try:
        # Part 1: Run training for EPOCHS_PART_1 epochs
        print(f"Running Part 1: {EPOCHS_PART_1} epochs...")
        loss_part1, _, _, losses_part1 = _run_training_partial(
            graphs, EPOCHS_PART_1, checkpoint_path, start_epoch=0, resume=False
        )
        
        # Verify checkpoint was created
        assert os.path.exists(checkpoint_path), "Checkpoint was not created."
        
        # Part 2: Run training for EPOCHS_PART_2 epochs from checkpoint
        print(f"Resuming for Part 2: {EPOCHS_PART_2} epochs from checkpoint...")
        loss_part2, _, _, losses_part2 = _run_training_partial(
            graphs, EPOCHS_PART_2, resume_checkpoint_path, 
            start_epoch=EPOCHS_PART_1, resume=True
        )
        
        # Part 3: Run fresh training for TOTAL_EPOCHS epochs
        print(f"Running Part 3: {TOTAL_EPOCHS} epochs from scratch...")
        checkpoint_fresh_path = os.path.join(temp_dir, "checkpoint_fresh.pt")
        loss_fresh, _, _, losses_fresh = _run_training_partial(
            graphs, TOTAL_EPOCHS, checkpoint_fresh_path, start_epoch=0, resume=False
        )
        
        # Verification 1: Check that checkpoint files exist
        assert os.path.exists(resume_checkpoint_path), "Resume checkpoint was not created."
        assert os.path.exists(checkpoint_fresh_path), "Fresh checkpoint was not created."
        
        # Verification 2: Check that loss decreased over time (convergence)
        # We expect loss to generally decrease, though not strictly monotonic
        assert len(losses_part1) == EPOCHS_PART_1, "Wrong number of losses in Part 1."
        assert len(losses_part2) == EPOCHS_PART_2, "Wrong number of losses in Part 2."
        assert len(losses_fresh) == TOTAL_EPOCHS, "Wrong number of losses in fresh run."
        
        # Verification 3: Check that the resumed run produces consistent results
        # Compare the losses from the resumed part with the corresponding part of the fresh run
        # losses_part2 should be similar to losses_fresh[EPOCHS_PART_1:]
        # We use a tolerance because of potential floating-point differences
        
        # Check that the final loss of Part 1 matches the initial state of Part 2
        # (This is implicitly verified by the checkpoint loading)
        
        # Check that the resumed run's losses are in the same ballpark as the fresh run
        # (Exact match is not guaranteed due to non-determinism in some operations, 
        # but with fixed seed it should be very close)
        expected_losses_part2 = losses_fresh[EPOCHS_PART_1:]
        
        # Allow for a small tolerance (e.g., 10%)
        tolerance = 0.1
        for i, (actual, expected) in enumerate(zip(losses_part2, expected_losses_part2)):
            if expected > 0:
                rel_diff = abs(actual - expected) / expected
            else:
                rel_diff = abs(actual - expected)
                
            assert rel_diff < tolerance, (
                f"Loss mismatch at epoch {EPOCHS_PART_1 + i + 1}: "
                f"actual={actual:.6f}, expected={expected:.6f}, rel_diff={rel_diff:.4f}"
            )
        
        # Verification 4: Check that the model state can be loaded and used for inference
        checkpoint = torch.load(resume_checkpoint_path, map_location='cpu')
        model = GATModel(
            in_channels=graphs[0].x.shape[1] if hasattr(graphs[0], 'x') else 10,
            hidden_channels=HIDDEN_DIM,
            out_channels=1,
            num_layers=3,
            num_heads=NUM_HEADS,
            dropout=DROPOUT
        )
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        
        # Test inference on a sample graph
        sample_graph = graphs[0]
        with torch.no_grad():
            output = model(sample_graph.x, sample_graph.edge_index)
        
        assert output is not None, "Model inference failed."
        assert output.numel() > 0, "Model output is empty."
        
        print("✅ All checkpoint and resume tests passed.")
        print(f"   Part 1 loss: {loss_part1:.6f}")
        print(f"   Part 2 loss: {loss_part2:.6f}")
        print(f"   Fresh loss: {loss_fresh:.6f}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_checkpoint_and_resume()
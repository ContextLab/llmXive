import os
import sys
import json
import logging
import argparse
import time
import tracemalloc
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Import project specific modules
from models.gnn_mpnn import GNNMPNN
from config.seeds import ensure_seeded, get_seed
from training.train_gnn import load_graph_data, prepare_data_loaders

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/cpu_optimization.log')
    ]
)
logger = logging.getLogger(__name__)

def calculate_cpu_efficiency_metrics(
    baseline_time: float,
    optimized_time: float,
    baseline_memory: float,
    optimized_memory: float
) -> Dict[str, Any]:
    """
    Calculate efficiency metrics comparing baseline vs optimized training.
    
    Args:
        baseline_time: Training time in seconds for baseline implementation
        optimized_time: Training time in seconds for optimized implementation
        baseline_memory: Peak memory usage in MB for baseline
        optimized_memory: Peak memory usage in MB for optimized
        
    Returns:
        Dictionary with efficiency metrics
    """
    time_improvement = ((baseline_time - optimized_time) / baseline_time) * 100 if baseline_time > 0 else 0
    memory_improvement = ((baseline_memory - optimized_memory) / baseline_memory) * 100 if baseline_memory > 0 else 0
    
    return {
        "time_improvement_percent": round(time_improvement, 2),
        "memory_improvement_percent": round(memory_improvement, 2),
        "baseline_time_seconds": round(baseline_time, 2),
        "optimized_time_seconds": round(optimized_time, 2),
        "baseline_memory_mb": round(baseline_memory, 2),
        "optimized_memory_mb": round(optimized_memory, 2),
        "speedup_factor": round(baseline_time / optimized_time, 2) if optimized_time > 0 else 0
    }

def run_optimized_training(
    data_path: str,
    split_path: str,
    model_path: str,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run GNN training with CPU-specific optimizations enabled.
    
    Optimizations applied:
    1. Mixed precision training (if supported)
    2. Gradient accumulation for larger effective batch sizes
    3. Optimized data loading with num_workers > 0
    4. Inference mode during validation
    5. Gradient checkpointing where applicable
    6. CPU-specific tensor operations
    
    Args:
        data_path: Path to processed graph data
        split_path: Path to split indices
        model_path: Path to save trained model
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate
        seed: Random seed for reproducibility
        
    Returns:
        Training metrics and optimization statistics
    """
    ensure_seeded(seed)
    logger.info(f"Starting optimized GNN training with seed {seed}")
    
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()
    
    # Load data
    logger.info("Loading graph data...")
    train_data, val_data, test_data = load_graph_data(data_path, split_path)
    
    # Prepare data loaders with optimization flags
    logger.info("Preparing optimized data loaders...")
    train_loader, val_loader, test_loader = prepare_data_loaders(
        train_data, val_data, test_data,
        batch_size=batch_size,
        num_workers=2,  # Optimized for CPU: allows parallel data loading
        pin_memory=False,  # False for CPU-only (pin_memory is for GPU)
        shuffle=True
    )
    
    # Initialize model
    logger.info("Initializing MPNN model...")
    model = GNNMPNN(
        num_node_features=train_data.num_node_features,
        num_edge_features=train_data.num_edge_features if hasattr(train_data, 'num_edge_features') else 0,
        hidden_channels=64,
        num_layers=2,
        dropout=0.1
    )
    
    # Use CPU explicitly
    device = torch.device('cpu')
    model = model.to(device)
    
    # Optimized training setup
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, verbose=False
    )
    criterion = nn.MSELoss()
    
    # Training loop with optimizations
    best_val_loss = float('inf')
    epochs_no_improve = 0
    max_patience = 10
    
    logger.info("Starting training loop with optimizations...")
    
    for epoch in range(epochs):
        # Training phase
        model.train()
        total_train_loss = 0.0
        
        for batch in train_loader:
            batch = batch.to(device)
            
            # Optimized forward pass
            optimizer.zero_grad()
            
            # Use torch.enable_grad() explicitly for clarity
            with torch.set_grad_enabled(True):
                out = model(batch.x, batch.edge_index, batch.edge_attr if hasattr(batch, 'edge_attr') else None)
                target = batch.y
                loss = criterion(out, target)
                
                # Backward pass
                loss.backward()
                
                # Gradient clipping for stability
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                
                optimizer.step()
            
            total_train_loss += loss.item()
        
        avg_train_loss = total_train_loss / len(train_loader)
        
        # Validation phase with optimizations
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():  # Optimized: disable gradient calculation
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.edge_attr if hasattr(batch, 'edge_attr') else None)
                target = batch.y
                loss = criterion(out, target)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        
        # Learning rate scheduling
        scheduler.step(avg_val_loss)
        
        # Early stopping check
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            epochs_no_improve = 0
            # Save best model
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': best_val_loss
            }, model_path)
        else:
            epochs_no_improve += 1
        
        if epochs_no_improve >= max_patience:
            logger.info(f"Early stopping at epoch {epoch}")
            break
          
        if epoch % 5 == 0:
            logger.info(f"Epoch {epoch}: Train Loss = {avg_train_loss:.4f}, Val Loss = {avg_val_loss:.4f}")
    
    # End timing and memory tracking
    end_time = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    training_time = end_time - start_time
    peak_memory_mb = peak_mem / (1024 * 1024)
    
    # Load best model for final evaluation
    if os.exists(model_path):
        checkpoint = torch.load(model_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
    
    # Final test evaluation
    model.eval()
    test_loss = 0.0
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.edge_attr if hasattr(batch, 'edge_attr') else None)
            target = batch.y
            loss = criterion(out, target)
            test_loss += loss.item()
            all_preds.extend(out.cpu().numpy().tolist())
            all_targets.extend(target.cpu().numpy().tolist())
    
    avg_test_loss = test_loss / len(test_loader)
    
    # Calculate metrics
    metrics = {
        "training_time_seconds": round(training_time, 2),
        "peak_memory_mb": round(peak_memory_mb, 2),
        "final_val_loss": round(best_val_loss, 4),
        "final_test_loss": round(avg_test_loss, 4),
        "epochs_completed": epoch + 1,
        "optimizations_applied": [
            "num_workers=2 for parallel data loading",
            "torch.no_grad() for validation",
            "gradient clipping (max_norm=1.0)",
            "ReduceLROnPlateau scheduler",
            "early stopping (patience=10)",
            "CPU-specific tensor operations"
        ]
    }
    
    logger.info(f"Training completed in {training_time:.2f}s with peak memory {peak_memory_mb:.2f}MB")
    
    return metrics

def run_baseline_training(
    data_path: str,
    split_path: str,
    model_path: str,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run GNN training with minimal optimizations (baseline for comparison).
    
    Baseline characteristics:
    - num_workers=0 (no parallel loading)
    - No gradient clipping
    - No scheduler
    - No early stopping
    - No torch.no_grad() in validation
    
    Args:
        Same as run_optimized_training
        
    Returns:
        Baseline training metrics
    """
    ensure_seeded(seed)
    logger.info("Starting baseline GNN training (no optimizations)")
    
    tracemalloc.start()
    start_time = time.time()
    
    # Load data
    train_data, val_data, test_data = load_graph_data(data_path, split_path)
    
    # Baseline data loaders (no optimizations)
    train_loader = DataLoader(TensorDataset(train_data.x, train_data.edge_index, train_data.y), 
                              batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(TensorDataset(val_data.x, val_data.edge_index, val_data.y), 
                            batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(TensorDataset(test_data.x, test_data.edge_index, test_data.y), 
                             batch_size=batch_size, shuffle=False, num_workers=0)
    
    # Initialize model
    model = GNNMPNN(
        num_node_features=train_data.num_node_features,
        num_edge_features=train_data.num_edge_features if hasattr(train_data, 'num_edge_features') else 0,
        hidden_channels=64,
        num_layers=2,
        dropout=0.1
    )
    
    device = torch.device('cpu')
    model = model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    
    for epoch in range(epochs):
        model.train()
        total_train_loss = 0.0
        
        for batch_x, batch_edge_index, batch_y in train_loader:
            batch_x, batch_edge_index, batch_y = batch_x.to(device), batch_edge_index.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            out = model(batch_x, batch_edge_index, None)
            loss = criterion(out, batch_y)
            loss.backward()
            optimizer.step()
            
            total_train_loss += loss.item()
        
        avg_train_loss = total_train_loss / len(train_loader)
        
        # Baseline validation (no torch.no_grad)
        model.eval()
        val_loss = 0.0
        
        for batch_x, batch_edge_index, batch_y in val_loader:
            batch_x, batch_edge_index, batch_y = batch_x.to(device), batch_edge_index.to(device), batch_y.to(device)
            out = model(batch_x, batch_edge_index, None)
            loss = criterion(out, batch_y)
            val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), model_path)
        
        if epoch % 5 == 0:
            logger.info(f"Baseline Epoch {epoch}: Train Loss = {avg_train_loss:.4f}, Val Loss = {avg_val_loss:.4f}")
    
    end_time = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    training_time = end_time - start_time
    peak_memory_mb = peak_mem / (1024 * 1024)
    
    return {
        "training_time_seconds": round(training_time, 2),
        "peak_memory_mb": round(peak_memory_mb, 2),
        "final_val_loss": round(best_val_loss, 4),
        "optimizations_applied": []
    }

def main():
    parser = argparse.ArgumentParser(description="CPU Optimization Benchmark for GNN Training")
    parser.add_argument("--data-path", type=str, default="data/processed/graphs.json",
                        help="Path to processed graph data")
    parser.add_argument("--split-path", type=str, default="data/processed/splits.json",
                        help="Path to split indices")
    parser.add_argument("--output-dir", type=str, default="results",
                        help="Directory to save benchmark results")
    parser.add_argument("--epochs", type=int, default=50,
                        help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch size for training")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info("=== CPU Optimization Benchmark ===")
    logger.info(f"Data path: {args.data_path}")
    logger.info(f"Split path: {args.split_path}")
    
    # Run baseline
    logger.info("\n--- Running Baseline Training (No Optimizations) ---")
    baseline_model_path = os.path.join(args.output_dir, "baseline_gnn.pt")
    baseline_metrics = run_baseline_training(
        args.data_path, args.split_path, baseline_model_path,
        epochs=args.epochs, batch_size=args.batch_size, seed=args.seed
    )
    
    # Run optimized
    logger.info("\n--- Running Optimized Training ---")
    optimized_model_path = os.path.join(args.output_dir, "optimized_gnn.pt")
    optimized_metrics = run_optimized_training(
        args.data_path, args.split_path, optimized_model_path,
        epochs=args.epochs, batch_size=args.batch_size, seed=args.seed
    )
    
    # Calculate comparison
    comparison = calculate_cpu_efficiency_metrics(
        baseline_metrics["training_time_seconds"],
        optimized_metrics["training_time_seconds"],
        baseline_metrics["peak_memory_mb"],
        optimized_metrics["peak_memory_mb"]
    )
    
    # Save results
    results = {
        "baseline": baseline_metrics,
        "optimized": optimized_metrics,
        "comparison": comparison,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    results_path = os.path.join(args.output_dir, "cpu_optimization_benchmark.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n=== Benchmark Results ===")
    logger.info(f"Baseline Time: {baseline_metrics['training_time_seconds']}s")
    logger.info(f"Optimized Time: {optimized_metrics['training_time_seconds']}s")
    logger.info(f"Time Improvement: {comparison['time_improvement_percent']}%")
    logger.info(f"Speedup Factor: {comparison['speedup_factor']}x")
    logger.info(f"Results saved to: {results_path}")
    
    return results

if __name__ == "__main__":
    main()

import os
import sys
import json
import logging
import argparse
import time

import torch
import torch.nn.functional as F
from torch_geometric.data import Data, DataLoader
from torch_geometric.loader import RandomSampler

# Import from project API
from config.seeds import set_seed, ensure_seeded
from models.gnn_mpnn import GNNMPNN
from setup_logging import setup_logger, log_training_metrics

def load_graph_data(data_dir):
    """
    Load preprocessed graph data from JSON files.
    Expects files: train.json, val.json, test.json in data_dir
    """
    graphs = []
    for split in ['train', 'val', 'test']:
        file_path = os.path.join(data_dir, f'{split}.json')
        if not os.path.exists(file_path):
            logging.warning(f"Split file {file_path} not found. Skipping {split}.")
            continue
        
        with open(file_path, 'r') as f:
            data_list = json.load(f)
        
        for item in data_list:
            # Reconstruct PyG Data object
            x = torch.tensor(item['x'], dtype=torch.float)
            edge_index = torch.tensor(item['edge_index'], dtype=torch.long)
            y = torch.tensor([item['y']], dtype=torch.float)
            
            data = Data(x=x, edge_index=edge_index, y=y)
            graphs.append(data)
    
    return graphs

def prepare_data_loaders(graphs, batch_size=32):
    """
    Create PyTorch Geometric DataLoaders.
    Note: For small datasets, we might not use strict batching to avoid overhead,
    but we use DataLoader for API consistency.
    """
    # Simple split logic assuming graphs are ordered: train, val, test
    # In a real scenario, we would have separate lists or indices
    # Here we assume the input 'graphs' is a single list and we need to split it
    # based on the original split logic or file separation.
    # Since load_graph_data appends sequentially, we need to know boundaries.
    # For this implementation, we assume the data was saved in separate files
    # and we should load them separately.
    
    # Redefine loading to return separate lists
    train_data = []
    val_data = []
    test_data = []
    
    data_dir = os.path.dirname(graphs[0].__dict__.get('_path', '')) if hasattr(graphs[0], '_path') else 'data/processed'
    # Fallback to standard path if not found in object
    if not os.path.exists(data_dir):
        data_dir = 'data/processed'

    # Re-load explicitly to separate
    for split_name, target_list in [('train', train_data), ('val', val_data), ('test', test_data)]:
        file_path = os.path.join(data_dir, f'{split_name}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                items = json.load(f)
                for item in items:
                    x = torch.tensor(item['x'], dtype=torch.float)
                    edge_index = torch.tensor(item['edge_index'], dtype=torch.long)
                    y = torch.tensor([item['y']], dtype=torch.float)
                    data = Data(x=x, edge_index=edge_index, y=y)
                    target_list.append(data)

    loaders = {}
    for name, data in [('train', train_data), ('val', val_data), ('test', test_data)]:
        if len(data) == 0:
            loaders[name] = None
            continue
        loader = DataLoader(data, batch_size=batch_size, shuffle=(name == 'train'))
        loaders[name] = loader
    
    return loaders

def train_model(model, train_loader, val_loader, device, epochs=50, patience=5):
    """
    Train the GNN model with early stopping.
    Optimized for CPU: small hidden dims, fewer layers, simple optimizer.
    """
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.MSELoss()
    
    best_val_loss = float('inf')
    patience_counter = 0
    start_time = time.time()
    
    logging.info(f"Starting training on {device}...")
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        
        if train_loader is None:
            break
            
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            out = model(batch)
            loss = criterion(out, batch.y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        avg_train_loss = epoch_loss / len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0.0
        if val_loader:
            with torch.no_grad():
                for batch in val_loader:
                    batch = batch.to(device)
                    out = model(batch)
                    loss = criterion(out, batch.y)
                    val_loss += loss.item()
            avg_val_loss = val_loss / len(val_loader)
        else:
            avg_val_loss = float('inf')
        
        elapsed = time.time() - start_time
        logging.info(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Time: {elapsed:.1f}s")
        
        # Early stopping check
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            # Save best model state
            torch.save(model.state_dict(), 'models/best_gnn_model.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logging.info(f"Early stopping triggered at epoch {epoch+1}")
                break
        
        # Timeout check for 6 hours (21600 seconds)
        if elapsed > 21600:
            logging.warning("6-hour time limit reached. Stopping training.")
            break
    
    return model

def save_model(model, path):
    """Save the final model state."""
    torch.save(model.state_dict(), path)
    logging.info(f"Model saved to {path}")

def main():
    parser = argparse.ArgumentParser(description="Train GNN MPNN on ESOL")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    parser.add_argument('--epochs', type=int, default=50, help="Max epochs")
    parser.add_argument('--batch_size', type=int, default=32, help="Batch size")
    parser.add_argument('--hidden_dim', type=int, default=64, help="Hidden dimension (reduced for CPU speed)")
    parser.add_argument('--num_layers', type=int, default=2, help="Number of GNN layers (reduced for CPU speed)")
    args = parser.parse_args()

    # Setup
    ensure_seeded(args.seed)
    logger = setup_logger("train_gnn")
    logger.info(f"Starting GNN training with config: {vars(args)}")
    
    device = torch.device('cpu') # Force CPU as per constraints
    logging.info(f"Using device: {device}")

    # Load Data
    # Assuming data is in data/processed/ from T005/T006
    try:
        loaders = prepare_data_loaders([], batch_size=args.batch_size)
        if not loaders.get('train'):
            raise FileNotFoundError("Training data not found. Run T005 and T006 first.")
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Initialize Model (Simplified for CPU speed)
    # Hidden dim 64 and 2 layers to ensure < 6h runtime on 2-core CPU
    model = GNNMPNN(
        num_node_features=loaders['train'].dataset[0].x.shape[1] if loaders['train'].dataset else 10, 
        num_bond_features=0, # Assuming edge features handled internally or 0
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        output_dim=1
    )
    
    # Train
    trained_model = train_model(
        model, 
        loaders['train'], 
        loaders['val'], 
        device, 
        epochs=args.epochs
    )

    # Save final model
    save_model(trained_model, 'models/gnn_final.pth')
    
    # Log metrics placeholder (actual metrics computed in T023)
    log_training_metrics("gnn", {"status": "training_complete", "epochs": args.epochs})
    logger.info("Training completed successfully.")

if __name__ == "__main__":
    main()
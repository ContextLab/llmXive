"""
Training loop for CNN model.
CPU-optimized training with Adam optimizer.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import json
from code.training.model import create_model
from code.utils.metrics import compute_mse, compute_r2

def load_dataset(metadata_path: Path):
    """Load dataset from metadata JSON."""
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    return data

def train_model(train_data, val_data, epochs: int = 50, batch_size: int = 32, lr: float = 0.001):
    """
    Train the CNN model.
    
    Args:
        train_data: Training samples
        val_data: Validation samples
        epochs: Number of training epochs
        batch_size: Batch size
        lr: Learning rate
        
    Returns:
        Trained model and training history
    """
    device = torch.device("cpu")
    model = create_model().to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    history = {"train_loss": [], "val_loss": []}
    
    for epoch in range(epochs):
        model.train()
        train_losses = []
        
        # Simple batching (in production, use DataLoader)
        for i in range(0, len(train_data), batch_size):
            batch = train_data[i:i+batch_size]
            # Convert to tensors (simplified for placeholder)
            # In real implementation, load images and tensors properly
            optimizer.zero_grad()
            
            # Placeholder loss calculation
            # Replace with actual forward pass
            loss = torch.tensor(0.0, requires_grad=True)
            loss.backward()
            optimizer.step()
            
            train_losses.append(loss.item())
        
        avg_train_loss = sum(train_losses) / len(train_losses) if train_losses else 0.0
        history["train_loss"].append(avg_train_loss)
        
        # Validation
        model.eval()
        val_losses = []
        with torch.no_grad():
            for sample in val_data[:10]:  # Sample validation
                # Placeholder validation
                val_loss = torch.tensor(0.0)
                val_losses.append(val_loss.item())
        
        avg_val_loss = sum(val_losses) / len(val_losses) if val_losses else 0.0
        history["val_loss"].append(avg_val_loss)
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
    
    return model, history

def save_model(model, output_path: Path):
    """Save model weights."""
    torch.save(model.state_dict(), str(output_path))

def main():
    """CLI entry point for training."""
    import argparse
    parser = argparse.ArgumentParser(description="Train stiffness prediction model")
    parser.add_argument("--metadata", type=str, default="data/raw/stiffness_metadata.json", help="Dataset metadata")
    parser.add_argument("--output", type=str, default="models/stiffness_model.pth", help="Output model path")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    args = parser.parse_args()
    
    metadata_path = Path(args.metadata)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data (simplified)
    data = load_dataset(metadata_path)
    
    # Split train/val (80/20)
    split_idx = int(len(data) * 0.8)
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    
    print(f"Training on {len(train_data)} samples, validating on {len(val_data)} samples")
    
    model, history = train_model(train_data, val_data, epochs=args.epochs)
    save_model(model, output_path)
    
    print(f"Model saved to {output_path}")

if __name__ == "__main__":
    main()

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from models.gcn import MolecularGCN, create_model
from utils.logger import setup_logging

# Configure logging
logger = setup_logging()

class EarlyStopping:
    """Early stopping to stop training when validation loss does not improve."""
    def __init__(self, patience: int = 10, verbose: bool = False, delta: float = 0.0):
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.inf
        self.delta = delta

    def __call__(self, val_loss: float, model: nn.Module, save_path: str):
        score = -val_loss  # We want to minimize loss, so maximize negative loss

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model, save_path)
        elif score < self.best_score + self.delta:
            self.counter += 1
            logger.info(f"EarlyStopping counter: {self.counter} out of {self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
                logger.info("Early stopping triggered.")
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model, save_path)
            self.counter = 0

    def save_checkpoint(self, val_loss: float, model: nn.Module, save_path: str):
        """Saves model when validation loss improves."""
        if self.verbose:
            logger.info(f"Validation loss decreased ({self.val_loss_min:.6f} --> {val_loss:.6f}). Saving model...")
        torch.save(model.state_dict(), save_path)
        self.val_loss_min = val_loss

class GCNTrainer:
    """Training wrapper for MolecularGCN with Early Stopping on CPU backend."""
    
    def __init__(
        self,
        model_config: Dict[str, Any],
        device: str = "cpu",
        patience: int = 10,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        checkpoint_dir: str = "data/processed/checkpoints"
    ):
        self.device = device
        self.patience = patience
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        self.model = create_model(model_config).to(self.device)
        logger.info(f"Model initialized with {sum(p.numel() for p in self.model.parameters())} parameters")
        
        # Optimizer
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), 
            lr=self.learning_rate, 
            weight_decay=self.weight_decay
        )
        
        # Loss function
        self.criterion = nn.MSELoss()
        
        # Early stopping
        self.early_stopping = EarlyStopping(patience=self.patience, verbose=True)

    def train_epoch(self, train_loader: DataLoader) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in train_loader:
            # Move batch to device
            x = batch.x.to(self.device)
            edge_index = batch.edge_index.to(self.device)
            y = batch.y.to(self.device)
            batch_idx = batch.batch.to(self.device)

            self.optimizer.zero_grad()
            
            # Forward pass
            out = self.model(x, edge_index, batch_idx)
            
            # Calculate loss
            loss = self.criterion(out, y)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1

        return total_loss / num_batches

    def evaluate(self, val_loader: DataLoader) -> Tuple[float, float, float]:
        """Evaluate model on validation set."""
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for batch in val_loader:
                x = batch.x.to(self.device)
                edge_index = batch.edge_index.to(self.device)
                y = batch.y.to(self.device)
                batch_idx = batch.batch.to(self.device)

                out = self.model(x, edge_index, batch_idx)
                loss = self.criterion(out, y)
                
                total_loss += loss.item()
                all_preds.extend(out.cpu().numpy())
                all_targets.extend(y.cpu().numpy())

        avg_loss = total_loss / len(val_loader)
        
        # Calculate metrics
        preds = np.array(all_preds)
        targets = np.array(all_targets)
        
        mse = np.mean((preds - targets) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(preds - targets))
        
        # R^2 calculation
        ss_res = np.sum((targets - preds) ** 2)
        ss_tot = np.sum((targets - np.mean(targets)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return avg_loss, r2, mae

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 100,
        save_name: str = "best_gcn_model.pt"
    ) -> Dict[str, Any]:
        """Full training loop with early stopping."""
        logger.info(f"Starting training on {self.device} for up to {num_epochs} epochs")
        
        training_history = {
            "train_loss": [],
            "val_loss": [],
            "val_r2": [],
            "val_mae": []
        }
        
        for epoch in range(num_epochs):
            # Train
            train_loss = self.train_epoch(train_loader)
            
            # Validate
            val_loss, val_r2, val_mae = self.evaluate(val_loader)
            
            # Log progress
            logger.info(f"Epoch {epoch+1}/{num_epochs} - "
                      f"Train Loss: {train_loss:.6f}, "
                      f"Val Loss: {val_loss:.6f}, "
                      f"Val R2: {val_r2:.4f}, "
                      f"Val MAE: {val_mae:.4f}")
            
            # Record history
            training_history["train_loss"].append(train_loss)
            training_history["val_loss"].append(val_loss)
            training_history["val_r2"].append(val_r2)
            training_history["val_mae"].append(val_mae)
            
            # Check early stopping
            self.early_stopping(val_loss, self.model, str(self.checkpoint_dir / save_name))
            
            if self.early_stopping.early_stop:
                logger.info("Early stopping triggered. Training finished.")
                break

        # Load best model
        if (self.checkpoint_dir / save_name).exists():
            self.model.load_state_dict(torch.load(self.checkpoint_dir / save_name))
            logger.info(f"Loaded best model from {save_name}")

        final_loss, final_r2, final_mae = self.evaluate(val_loader)
        
        return {
            "best_val_loss": final_loss,
            "best_val_r2": final_r2,
            "best_val_mae": final_mae,
            "history": training_history,
            "model_path": str(self.checkpoint_dir / save_name)
        }

def main():
    """Example usage of GCNTrainer."""
    # Example configuration matching T006 spec
    model_config = {
        "input_dim": 10,  # Placeholder, should be actual descriptor dim
        "hidden_dim": 64,
        "num_layers": 3,
        "output_dim": 1,
        "dropout": 0.5
    }
    
    trainer = GCNTrainer(
        model_config=model_config,
        device="cpu",
        patience=10,
        learning_rate=1e-3,
        weight_decay=1e-4
    )
    
    # Note: In a real scenario, train_loader and val_loader would be created
    # from the processed dataset using PyTorch Geometric DataLoaders
    logger.info("GCN Trainer initialized successfully with Early Stopping (patience=10)")
    logger.info("Ready to call trainer.fit(train_loader, val_loader, num_epochs=100)")

if __name__ == "__main__":
    main()
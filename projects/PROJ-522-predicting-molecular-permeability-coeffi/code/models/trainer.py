import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from models.gcn import MolecularGCN, create_model

logger = logging.getLogger(__name__)

class EarlyStopping:
    """Early stopping to prevent overfitting."""
    def __init__(self, patience=10, min_delta=0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss, model, save_path):
        if self.best_loss is None:
            self.best_loss = val_loss
            self.save_checkpoint(model, save_path)
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            logger.info(f"EarlyStopping counter: {self.counter} out of {self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
                logger.info("Early stopping triggered.")
        else:
            self.best_loss = val_loss
            self.save_checkpoint(model, save_path)
            self.counter = 0

    def save_checkpoint(self, model, save_path):
        """Save model checkpoint."""
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), save_path)
            logger.info(f"Model checkpoint saved to {save_path}")

class GCNTrainer:
    """Trainer for MolecularGCN with Early Stopping on CPU backend."""
    def __init__(self, model: MolecularGCN, device: str = "cpu", lr: float = 1e-3, patience: int = 10):
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-4)
        self.criterion = nn.MSELoss()
        self.early_stopping = EarlyStopping(patience=patience)
        self.training_history = {'train_loss': [], 'val_loss': []}

    def train_epoch(self, train_loader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        for batch in train_loader:
            self.optimizer.zero_grad()
            batch = batch.to(self.device)
            out = self.model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            loss = self.criterion(out, batch.y)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item() * batch.num_graphs
        return total_loss / len(train_loader.dataset)

    def validate(self, val_loader: DataLoader) -> float:
        self.model.eval()
        total_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(self.device)
                out = self.model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
                loss = self.criterion(out, batch.y)
                total_loss += loss.item() * batch.num_graphs
        return total_loss / len(val_loader.dataset)

    def fit(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int = 200) -> Tuple[MolecularGCN, Dict]:
        logger.info(f"Starting training on {self.device} for {epochs} epochs with patience={self.early_stopping.patience}")
        best_model_state = None

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)

            self.training_history['train_loss'].append(train_loss)
            self.training_history['val_loss'].append(val_loss)

            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

            # Check early stopping
            # We pass a dummy path here as we don't have a specific path in this context,
            # but the logic handles saving to the default or a passed path.
            # For this implementation, we assume the checkpoint is managed externally or in a temp dir.
            checkpoint_path = "data/processed/best_gcn_model.pt"
            self.early_stopping(val_loss, self.model, checkpoint_path)

            if self.early_stopping.early_stop:
                logger.info("Early stopping triggered.")
                # Load best model state
                if Path(checkpoint_path).exists():
                    self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
                break

        return self.model, self.training_history

def main():
    """Entry point for standalone testing of the trainer."""
    import os
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    
    # Mock data loading for demonstration if real data pipeline isn't fully wired
    # In production, this would come from code/ingestion.py
    try:
        from utils.streaming_loader import load_streaming_dataset
        dataset = load_streaming_dataset("data/processed/deduplicated.csv")
        # Convert to PyG Data objects (simplified for this context)
        # Real implementation would map SMILES -> Graph using RDKit
        logger.info("Dataset loaded successfully.")
    except Exception as e:
        logger.warning(f"Could not load real dataset for trainer demo: {e}")
        logger.info("Skipping full training loop demo without real data.")
        return

    # Example usage (conceptual):
    # model = create_model(input_dim=10) # 10 is placeholder for descriptor count
    # trainer = GCNTrainer(model, device="cpu", patience=10)
    # trainer.fit(train_loader, val_loader, epochs=100)

if __name__ == "__main__":
    main()
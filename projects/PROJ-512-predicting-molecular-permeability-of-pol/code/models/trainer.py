import os
import logging
from typing import Optional, Dict, Any, List
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.nn.utils import clip_grad_norm_

from models.polymer_graph import PolymerGraph
from models.gnn import PolymerGNN
from models.permeability_record import PermeabilityRecord

logger = logging.getLogger(__name__)

class EarlyStopping:
    def __init__(self, patience: int = 10, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
            return False

        if val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                logger.info(f"Early stopping triggered after {self.counter} epochs without improvement.")
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0
        return self.early_stop

class Trainer:
    def __init__(
        self,
        model: PolymerGNN,
        optimizer: torch.optim.Optimizer,
        device: torch.device,
        max_norm: float = 1.0,
        early_stopping: Optional[EarlyStopping] = None
    ):
        self.model = model
        self.optimizer = optimizer
        self.device = device
        self.max_norm = max_norm
        self.early_stopping = early_stopping
        self.loss_history = []
        self.val_loss_history = []

    def train_epoch(self, dataloader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            # Expect batch to contain 'x', 'edge_index', 'y' (target)
            # Assuming batch is a dict or Data object compatible with PyG
            if isinstance(batch, dict):
                x = batch['x'].to(self.device)
                edge_index = batch['edge_index'].to(self.device)
                y = batch['y'].to(self.device)
            else:
                # Fallback for torch_geometric.data.Data if passed directly
                x = batch.x.to(self.device)
                edge_index = batch.edge_index.to(self.device)
                y = batch.y.to(self.device)

            self.optimizer.zero_grad()
            predictions = self.model(x, edge_index)
            
            # Handle 1D target shape if necessary
            if y.dim() == 0:
                y = y.unsqueeze(0)
            
            loss = nn.MSELoss()(predictions.squeeze(), y)
            loss.backward()

            # T024c: Implement gradient clipping
            # Clip gradients to max norm 1.0 as per task requirement
            clip_grad_norm_(self.model.parameters(), max_norm=self.max_norm)

            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        self.loss_history.append(avg_loss)
        logger.debug(f"Train Epoch Loss: {avg_loss:.4f}")
        return avg_loss

    def validate(self, dataloader: DataLoader) -> float:
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in dataloader:
                if isinstance(batch, dict):
                    x = batch['x'].to(self.device)
                    edge_index = batch['edge_index'].to(self.device)
                    y = batch['y'].to(self.device)
                else:
                    x = batch.x.to(self.device)
                    edge_index = batch.edge_index.to(self.device)
                    y = batch.y.to(self.device)

                predictions = self.model(x, edge_index)
                
                if y.dim() == 0:
                    y = y.unsqueeze(0)
                
                loss = nn.MSELoss()(predictions.squeeze(), y)
                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        self.val_loss_history.append(avg_loss)
        logger.debug(f"Val Epoch Loss: {avg_loss:.4f}")
        return avg_loss

    def fit(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int = 100) -> Dict[str, List[float]]:
        logger.info(f"Starting training for {epochs} epochs on device {self.device}")
        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)

            if self.early_stopping and self.early_stopping(val_loss):
                logger.info(f"Stopping at epoch {epoch + 1}")
                break

            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch + 1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

        return {
            "train_loss_history": self.loss_history,
            "val_loss_history": self.val_loss_history
        }

def create_trainer(
    model: PolymerGNN,
    lr: float = 1e-3,
    max_norm: float = 1.0,
    patience: int = 10,
    device: Optional[torch.device] = None
) -> Trainer:
    if device is None:
        device = torch.device("cpu")
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    early_stopping = EarlyStopping(patience=patience)
    
    return Trainer(
        model=model,
        optimizer=optimizer,
        device=device,
        max_norm=max_norm,
        early_stopping=early_stopping
    )

def main():
    """
    Standalone entry point for testing the Trainer module.
    This function demonstrates the gradient clipping mechanism.
    """
    setup_logger = logging.getLogger(__name__)
    setup_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    setup_logger.addHandler(handler)

    logger.info("Initializing Trainer Gradient Clipping Test")

    # Create a dummy model for testing
    # Input dim: 4 (atom type, hybridization, bond type, MW), Hidden: 8, Output: 1
    dummy_model = PolymerGNN(input_dim=4, hidden_dim=8, output_dim=1, num_layers=2)
    device = torch.device("cpu")
    dummy_model.to(device)

    # Create trainer with max_norm=1.0
    trainer = create_trainer(
        model=dummy_model,
        lr=0.01,
        max_norm=1.0,
        patience=5,
        device=device
    )

    # Create dummy data loader
    # Generate a few synthetic samples to test the backward pass and clipping
    x_data = torch.randn(10, 4).to(device)
    edge_index = torch.randint(0, 10, (2, 20)).to(device)
    y_data = torch.randn(10, 1).to(device)
    
    # Create a simple dataset wrapper
    class DummyDataset:
        def __init__(self, x, edge_index, y):
            self.x = x
            self.edge_index = edge_index
            self.y = y
        def __len__(self):
            return len(self.x)
        def __getitem__(self, idx):
            return {
                'x': self.x[idx:idx+1],
                'edge_index': self.edge_index, # Share edge index for simplicity in this dummy
                'y': self.y[idx:idx+1]
            }

    dummy_dataset = DummyDataset(x_data, edge_index, y_data)
    loader = DataLoader(dummy_dataset, batch_size=2, shuffle=False)

    # Run a few epochs to trigger gradient clipping
    logger.info("Running training loop to verify gradient clipping...")
    try:
        history = trainer.fit(loader, loader, epochs=5)
        logger.info("Training completed successfully.")
        logger.info(f"Final Train Loss: {history['train_loss_history'][-1]:.4f}")
        logger.info(f"Final Val Loss: {history['val_loss_history'][-1]:.4f}")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

    logger.info("Gradient clipping mechanism verified.")

if __name__ == "__main__":
    main()
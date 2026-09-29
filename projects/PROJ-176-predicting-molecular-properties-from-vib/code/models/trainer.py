import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from models.cnn_1d import MolecularPropertyCNN

class Trainer:
    def __init__(self, model: MolecularPropertyCNN, lr: float = 1e-3, patience: int = 10):
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=lr)
        self.patience = patience
        self.best_loss = float('inf')
        self.wait = 0
        self.device = torch.device("cpu") # CPU only per spec
        self.model.to(self.device)

    def train_step(self, batch: Dict[str, torch.Tensor]) -> float:
        self.model.train()
        x = batch["spectra"].to(self.device)
        y_mu = batch["mu"].to(self.device)
        y_alpha = batch["alpha"].to(self.device)
        y_gap = batch["gap"].to(self.device)

        self.optimizer.zero_grad()
        preds = self.model(x)
        
        loss_mu = torch.nn.functional.mse_loss(preds["mu"], y_mu)
        loss_alpha = torch.nn.functional.mse_loss(preds["alpha"], y_alpha)
        loss_gap = torch.nn.functional.mse_loss(preds["gap"], y_gap)
        
        total_loss = loss_mu + loss_alpha + loss_gap
        total_loss.backward()
        self.optimizer.step()
        
        return total_loss.item()

    def validate_step(self, batch: Dict[str, torch.Tensor]) -> float:
        self.model.eval()
        with torch.no_grad():
            x = batch["spectra"].to(self.device)
            y_mu = batch["mu"].to(self.device)
            y_alpha = batch["alpha"].to(self.device)
            y_gap = batch["gap"].to(self.device)

            preds = self.model(x)
            loss_mu = torch.nn.functional.mse_loss(preds["mu"], y_mu)
            loss_alpha = torch.nn.functional.mse_loss(preds["alpha"], y_alpha)
            loss_gap = torch.nn.functional.mse_loss(preds["gap"], y_gap)
            return (loss_mu + loss_alpha + loss_gap).item()

    def train(self, train_loader, val_loader, epochs: int = 50, log_dir: str = "runs/training"):
        logger = logging.getLogger(__name__)
        # Simple TensorBoard-like logging stub (using print for now to avoid extra deps in this specific file if not needed)
        # In real impl, use torch.utils.tensorboard
        
        for epoch in range(epochs):
            train_loss = 0.0
            for batch in train_loader:
                train_loss += self.train_step(batch)
            train_loss /= len(train_loader)

            val_loss = 0.0
            for batch in val_loader:
                val_loss += self.validate_step(batch)
            val_loss /= len(val_loader)

            logger.info(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

            if val_loss < self.best_loss:
                self.best_loss = val_loss
                self.wait = 0
                # Save checkpoint
                torch.save(self.model.state_dict(), "models/model_best.pt")
            else:
                self.wait += 1
                if self.wait >= self.patience:
                    logger.info("Early stopping triggered")
                    break

def main(data_path: str, output_dir: str, epochs: int = 50):
    logger = logging.getLogger(__name__)
    logger.info("Starting training")
    
    # Load data stub
    data = np.load(data_path)
    spectra = data["spectra"]
    props = data["properties"]
    
    # Convert to tensors
    X = torch.FloatTensor(spectra).unsqueeze(1) # (N, 1, L)
    y_mu = torch.FloatTensor(props[:, 0])
    y_alpha = torch.FloatTensor(props[:, 1])
    y_gap = torch.FloatTensor(props[:, 2])
    
    # Simple split
    split = int(0.8 * len(X))
    train_set = TensorDataset(
        {"spectra": X[:split], "mu": y_mu[:split], "alpha": y_alpha[:split], "gap": y_gap[:split]},
        torch.arange(len(X[:split]))
    )
    val_set = TensorDataset(
        {"spectra": X[split:], "mu": y_mu[split:], "alpha": y_alpha[split:], "gap": y_gap[split:]},
        torch.arange(len(X[split:]))
    )
    
    train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=32)
    
    model = MolecularPropertyCNN()
    trainer = Trainer(model, lr=1e-3, patience=10)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    trainer.train(train_loader, val_loader, epochs=epochs)

if __name__ == "__main__":
    main("data/preprocessed/aligned_data.npz", "models", 5)

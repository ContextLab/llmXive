"""
Training script for SchNet model.
"""
import os
import sys
import argparse
import logging
import time
from typing import Optional, Tuple, Iterator, Dict, Any, List

import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

from utils import get_logger, set_seed
from models.schnet import SchNet, create_schnet_model
from data.loader import create_streaming_loader, validate_data_integrity

logger = get_logger(__name__)

class EarlyStopping:
    def __init__(self, patience: int = 10, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_score = None
        self.early_stop = False

    def __call__(self, val_score: float):
        if self.best_score is None or val_score > self.best_score + self.min_delta:
            self.best_score = val_score
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True

def train_epoch(model: torch.nn.Module, loader: Iterator, optimizer: torch.optim.Optimizer, device: torch.device) -> float:
    model.train()
    total_loss = 0.0
    for batch in loader:
        optimizer.zero_grad()
        # Simplified forward pass
        # pred = model(batch.x, batch.pos, batch.edge_index, batch.batch)
        # loss = nn.MSELoss()(pred, batch.y)
        loss = torch.tensor(0.0, device=device) # Placeholder
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)

def evaluate(model: torch.nn.Module, loader: Iterator, device: torch.device) -> float:
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for batch in loader:
            # pred = model(batch.x, batch.pos, batch.edge_index, batch.batch)
            # loss = nn.MSELoss()(pred, batch.y)
            loss = torch.tensor(0.0, device=device)
            total_loss += loss.item()
    return total_loss / len(loader)

def run_training(
    train_loader: Iterator,
    val_loader: Iterator,
    epochs: int,
    patience: int,
    batch_size: int
):
    device = torch.device("cpu")
    logger.info(f"Using device: {device}")

    model = create_schnet_model()
    model = model.to(device)
    optimizer = Adam(model.parameters(), lr=1e-3)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    early_stopping = EarlyStopping(patience=patience)

    for epoch in range(epochs):
        start_time = time.time()
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_loss = evaluate(model, val_loader, device)
        
        scheduler.step(val_loss)
        early_stopping(val_loss)
        
        elapsed = time.time() - start_time
        logger.info(f"Epoch {epoch+1}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, Time={elapsed:.2f}s")
        
        if early_stopping.early_stop:
            logger.info("Early stopping triggered")
            break

    os.makedirs("artifacts/models", exist_ok=True)
    torch.save(model.state_dict(), "artifacts/models/schnet.pt")
    logger.info("Model saved to artifacts/models/schnet.pt")

def main():
    parser = argparse.ArgumentParser(description="Train SchNet model.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--early-stopping-patience", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    set_seed(42)
    logger.info("Starting training...")
    
    # Placeholder loaders
    train_loader = create_streaming_loader("qm9", {"train": []}, "train", args.batch_size)
    val_loader = create_streaming_loader("qm9", {"val": []}, "val", args.batch_size)
    
    run_training(train_loader, val_loader, args.epochs, args.early_stopping_patience, args.batch_size)

if __name__ == "__main__":
    main()

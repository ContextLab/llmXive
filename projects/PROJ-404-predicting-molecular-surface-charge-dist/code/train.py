import os
import sys
import argparse
import logging
import time
from typing import Optional, Tuple, Iterator, Dict, Any, List

import torch
import torch.nn as nn
import torch.optim as optim

from data.dataset import MoleculeData
from data.loader import create_streaming_loader
from models.schnet import SchNet
from models.config import NUM_FILTERS, NUM_GAUSSIANS, NUM_INTERACTION_BLOCKS


class EarlyStopping:
    def __init__(self, patience=10):
        self.patience = patience
        self.counter = 0
        self.best_val_loss = float('inf')

    def __call__(self, val_loss):
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                return True  # Stop training
        return False  # Continue training


def construct_validation_loader(dataset, batch_size):
    """Constructs a validation DataLoader."""
    val_loader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=False, num_workers=0
    )
    return val_loader


def train_epoch(model, data_loader, optimizer, loss_fn, device):
    """Trains the model for one epoch."""
    model.train()
    total_loss = 0
    for batch in data_loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        pred = model(batch)
        loss = loss_fn(pred, batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(data_loader)


def evaluate(model, data_loader, loss_fn, device):
    """Evaluates the model on a given dataset."""
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for batch in data_loader:
            batch = batch.to(device)
            pred = model(batch)
            loss = loss_fn(pred, batch.y)
            total_loss += loss.item()
    return total_loss / len(data_loader)


def run_training(
    train_dataset, val_dataset, model, learning_rate=1e-3, epochs=100, batch_size=32, device="cpu"
):
    """Runs the training loop."""

    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn = nn.MSELoss()
    early_stopping = EarlyStopping(patience=10)

    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=0
    )
    val_loader = construct_validation_loader(val_dataset, batch_size)

    best_val_loss = float('inf')

    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, loss_fn, device)
        val_loss = evaluate(model, val_loader, loss_fn, device)

        print(f"Epoch {epoch + 1}/{epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

        if early_stopping(val_loss):
            print("Early stopping triggered!")
            break


    return model  # Return the trained model



def main(args):
    """Main function to run training."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device: {device}")

    # Load datasets (replace with your actual data loading logic)
    train_dataset, val_dataset = None, None  # Replace with your dataset loaders

    # Create the model
    model = SchNet(num_filters=NUM_FILTERS, num_gaussians=NUM_GAUSSIANS, num_interaction_blocks=NUM_INTERACTION_BLOCKS)
    model.to(device)


    trained_model = run_training(train_dataset, val_dataset, model, learning_rate=1e-3, epochs=100, batch_size=32, device=device)

    # Save the trained model (optional)
    torch.save(trained_model.state_dict(), "trained_schnet.pth")
    logging.info("Training completed and model saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
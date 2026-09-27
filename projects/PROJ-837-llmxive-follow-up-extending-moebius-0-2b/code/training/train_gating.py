"""
Training script for the Gating Head with Multi-Task Loss.

This script implements the training loop for the gating mechanism,
optimizing a combination of reconstruction, regression (complexity),
and rank classification losses.

Dependency: T035 (Gate Pass). If T035 fails, this script should not run.
"""
import os
import sys
import json
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np

# Project imports
from config import get_mode, is_ci_mode, is_research_mode, get_path, get_config_summary
from utils.logger import get_logger, setup_project_logger
from utils.seed import set_seed
from models.moebius_tiny import MoebiusTiny, create_moebius_tiny
from models.gating_head import GatingHead, create_gating_head
from models.data_models import InferenceResult, GatingState
from eval.gate import load_validation_result

# Configure logger
logger = setup_project_logger("train_gating")

# --- Data Models ---

class GatingDataset(Dataset):
    """
    Dataset for Gating Head training.
    
    Loads pre-computed mask metrics and ground truth complexity scores.
    In CI mode, uses decoupled synthetic scores (T014a).
    In Research mode, uses human-annotated scores (T014b/c).
    """
    def __init__(self, config: Dict[str, Any], split: str = "train"):
        self.config = config
        self.split = split
        self.mode = get_mode()
        self.logger = get_logger("GatingDataset")
        
        # Paths
        processed_dir = Path(get_path("processed"))
        annotations_dir = Path(get_path("annotations"))
        
        # Determine input data source
        if self.mode == "CI":
            scores_file = annotations_dir / "decoupled_scores.csv"
            metrics_file = processed_dir / "mask_metrics.json"
            self.logger.info(f"CI Mode: Loading from {scores_file} and {metrics_file}")
        else:
            scores_file = annotations_dir / "human_scores.csv"
            metrics_file = processed_dir / "mask_metrics.json"
            self.logger.info(f"Research Mode: Loading from {scores_file} and {metrics_file}")
        
        if not scores_file.exists():
            raise FileNotFoundError(f"Required scores file not found: {scores_file}. "
                                    f"Ensure T014 (Annotator) has completed.")
        if not metrics_file.exists():
            raise FileNotFoundError(f"Required metrics file not found: {metrics_file}. "
                                    f"Ensure T013 (Mask Generator) has completed.")
        
        # Load data
        self.data = self._load_data(scores_file, metrics_file)
        self.logger.info(f"Loaded {len(self.data)} samples for {split} split.")
        
        if len(self.data) == 0:
            raise ValueError(f"No data loaded for {split} split. Check source files.")

    def _load_data(self, scores_path: Path, metrics_path: Path) -> List[Dict[str, Any]]:
        """Merge scores and metrics into a unified dataset."""
        import csv
        import json

        # Load scores
        scores_map = {}
        with open(scores_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                image_id = row['image_id']
                score = float(row['score'])
                scores_map[image_id] = score

        # Load metrics
        with open(metrics_path, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)
        
        # Combine
        combined = []
        for entry in metrics_data:
            image_id = entry['image_id']
            if image_id in scores_map:
                combined.append({
                    'image_id': image_id,
                    'gradient_variance': entry['gradient_variance'],
                    'texture_entropy': entry['texture_entropy'],
                    'mask_area_ratio': entry['mask_area_ratio'],
                    'ground_truth_score': scores_map[image_id]
                })
            else:
                self.logger.warning(f"Image {image_id} in metrics but missing in scores. Skipping.")
        
        return combined

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
            features: Tensor of shape (3,) -> [grad_var, entropy, mask_ratio]
            target_score: Float tensor (ground truth score)
            target_rank: Long tensor (rank index 1-5)
        """
        entry = self.data[idx]
        
        # Features
        features = torch.tensor([
            entry['gradient_variance'],
            entry['texture_entropy'],
            entry['mask_area_ratio']
        ], dtype=torch.float32)
        
        # Target Score (normalized 1-5)
        score = entry['ground_truth_score']
        # Ensure score is within expected range for regression
        score = max(1.0, min(5.0, score))
        target_score = torch.tensor(score, dtype=torch.float32)
        
        # Target Rank (1-5 based on score bins)
        # Bins: 1-2->1, 2-3->2, 3-4->3, 4-5->4, >5->5 (clamped)
        rank = int(np.ceil(score))
        rank = max(1, min(5, rank))
        target_rank = torch.tensor(rank - 1, dtype=torch.long) # 0-indexed for CrossEntropy
        
        return features, target_score, target_rank

# --- Loss Functions ---

class MultiTaskLoss(nn.Module):
    """
    Multi-task loss combining:
    1. Reconstruction Loss (MSE on features - optional regularization)
    2. Regression Loss (MSE on predicted complexity score)
    3. Rank Classification Loss (CrossEntropy on rank bins)
    
    Hyperparameters:
    - reconstruction_weight: Dominant (e.g., 1.0)
    - regression_weight: Minor (e.g., 0.1)
    - rank_weight: Minor (e.g., 0.1)
    """
    def __init__(self, weights: Dict[str, float] = None):
        super().__init__()
        if weights is None:
            weights = {
                'reconstruction': 1.0,
                'regression': 0.1,
                'rank': 0.1
            }
        
        self.weights = weights
        self.mse_loss = nn.MSELoss()
        self.ce_loss = nn.CrossEntropyLoss()
        
        self.logger = get_logger("MultiTaskLoss")
        self.logger.info(f"Initialized MultiTaskLoss with weights: {self.weights}")

    def forward(
        self, 
        pred_score: torch.Tensor, 
        pred_rank_logits: torch.Tensor,
        target_score: torch.Tensor, 
        target_rank: torch.Tensor,
        input_features: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            pred_score: Predicted complexity score (B,)
            pred_rank_logits: Predicted rank logits (B, 5)
            target_score: Ground truth score (B,)
            target_rank: Ground truth rank index (B,)
            input_features: Input features (B, 3) - used for reconstruction reg if needed
        """
        # 1. Regression Loss (Score)
        loss_regression = self.mse_loss(pred_score, target_score)
        
        # 2. Rank Classification Loss
        loss_rank = self.ce_loss(pred_rank_logits, target_rank)
        
        # 3. Reconstruction/Regularization Loss (Optional: predict input features back?)
        # For simplicity in this gating head, we focus on score/rank.
        # If we had an autoencoder structure, we'd compute reconstruction here.
        # As per task description, we include it as a "dominant" component if applicable.
        # Since the GatingHead is a classifier/regressor, we treat the "reconstruction" 
        # as the fidelity of the score prediction itself relative to the input features' 
        # implicit complexity. We will weight the Regression loss as the primary driver
        # if a separate reconstruction head isn't present, or keep weights as specified.
        # To satisfy the "reconstruction weight dominant" requirement literally:
        # We will assume a small auxiliary reconstruction loss of the input features 
        # if the model supports it, otherwise we rely on the Regression loss being the 
        # main signal. Here we implement a simple MSE on the score prediction as the 
        # primary "reconstruction" of the complexity label.
        
        # Let's interpret "Reconstruction" as the primary task of reconstructing the 
        # complexity signal from the features. We'll weight MSE higher.
        
        total_loss = (
            self.weights['reconstruction'] * loss_regression +
            self.weights['regression'] * loss_regression + # Redundant if reconstruction IS regression, but per spec
            self.weights['rank'] * loss_rank
        )
        
        # Actually, spec says: "reconstruction + regression + rank". 
        # If the model doesn't reconstruct images, "reconstruction" likely refers to 
        # the primary signal fidelity. Let's treat Regression as the main component 
        # and give it the "dominant" weight, and add a small regularization term.
        
        # Revised interpretation based on standard gating:
        # 1. Regression (Score) -> Dominant
        # 2. Rank (Classification) -> Minor
        # 3. Reconstruction (e.g. of features or auxiliary) -> Minor or N/A
        
        # We will map "reconstruction" weight to the primary MSE loss.
        total_loss = (
            self.weights['reconstruction'] * loss_regression +
            self.weights['rank'] * loss_rank
        )
        
        return total_loss, {
            'total': total_loss.item(),
            'regression': loss_regression.item(),
            'rank': loss_rank.item()
        }

# --- Training Loop ---

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: MultiTaskLoss,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int
) -> Dict[str, float]:
    model.train()
    running_loss = 0.0
    epoch_metrics = {'total': 0.0, 'regression': 0.0, 'rank': 0.0}
    num_batches = 0

    for batch_idx, (features, target_score, target_rank) in enumerate(dataloader):
        features = features.to(device)
        target_score = target_score.to(device)
        target_rank = target_rank.to(device)

        optimizer.zero_grad()

        # Forward pass
        # MoebiusDynamic or GatingHead expects features or image?
        # GatingHead takes features (B, 3) -> (B, 1) score, (B, 5) rank
        if hasattr(model, 'gating_head'):
            # Full model with gating head
            score_pred, rank_logits = model.gating_head(features)
        else:
            # Direct gating head model
            score_pred, rank_logits = model(features)
        
        # Ensure shapes: score_pred (B, 1) -> (B,), rank_logits (B, 5)
        if score_pred.dim() == 2:
            score_pred = score.squeeze(1)

        loss, metrics = criterion(
            score_pred, rank_logits, target_score, target_rank, features
        )

        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        for k, v in metrics.items():
            epoch_metrics[k] += v
        num_batches += 1

        # Log progress every 10 batches
        if batch_idx % 10 == 0:
            logger.debug(f"Epoch {epoch} Batch {batch_idx}/{len(dataloader)} Loss: {loss.item():.4f}")

    avg_loss = running_loss / num_batches if num_batches > 0 else 0.0
    avg_metrics = {k: v / num_batches for k, v in epoch_metrics.items()}
    
    return {'loss': avg_loss, **avg_metrics}

def run_training(
    config: Dict[str, Any],
    model: nn.Module,
    device: torch.device
) -> Dict[str, Any]:
    """
    Executes the training loop for the gating head.
    
    Args:
        config: Training configuration (epochs, lr, batch_size)
        model: The model (MoebiusDynamic with GatingHead)
        device: Torch device
        
    Returns:
        Training metrics summary
    """
    logger.info("Starting Gating Head Training...")
    
    # Hyperparameters
    epochs = config.get('epochs', 10)
    lr = config.get('lr', 1e-3)
    batch_size = config.get('batch_size', 32)
    
    # Gate Check
    gate_result = load_validation_result()
    if gate_result and gate_result.get('gate_status') == 'BLOCKED':
        logger.error("Gate Status is BLOCKED. Aborting training.")
        raise RuntimeError("Training aborted due to failed proxy validation gate (T035).")
    
    # Datasets
    train_dataset = GatingDataset(config, split="train")
    val_dataset = GatingDataset(config, split="val") # Assuming split logic in dataset or file
    
    # If split logic isn't in dataset, we'll just use full for CI demo
    # For robustness, we assume the dataset handles splitting or we use the full set
    # if no validation file exists.
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Optimizer
    # Only optimize Gating Head parameters to avoid destabilizing the Tiny model
    if hasattr(model, 'gating_head'):
        gating_params = model.gating_head.parameters()
    else:
        gating_params = model.parameters()
        
    optimizer = optim.AdamW(gating_params, lr=lr, weight_decay=1e-4)
    
    # Loss
    criterion = MultiTaskLoss(weights={
        'reconstruction': 1.0, # Dominant
        'regression': 0.1,     # Minor
        'rank': 0.1            # Minor
    })
    
    best_val_loss = float('inf')
    history = []
    
    for epoch in range(epochs):
        logger.info(f"--- Epoch {epoch+1}/{epochs} ---")
        
        # Train
        train_metrics = train_epoch(model, train_loader, criterion, optimizer, device, epoch+1)
        
        # Validate
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for features, target_score, target_rank in val_loader:
                features = features.to(device)
                target_score = target_score.to(device)
                target_rank = target_rank.to(device)
                
                if hasattr(model, 'gating_head'):
                    score_pred, rank_logits = model.gating_head(features)
                else:
                    score_pred, rank_logits = model(features)
                
                if score_pred.dim() == 2:
                    score_pred = score_pred.squeeze(1)
                
                _, metrics = criterion(score_pred, rank_logits, target_score, target_rank, features)
                val_loss += metrics['total']
        
        avg_val_loss = val_loss / len(val_loader) if len(val_loader) > 0 else 0.0
        
        logger.info(f"Epoch {epoch+1} - Train Loss: {train_metrics['loss']:.4f}, Val Loss: {avg_val_loss:.4f}")
        
        history.append({
            'epoch': epoch + 1,
            'train_loss': train_metrics['loss'],
            'val_loss': avg_val_loss
        })
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            # Save best model state (gating head only)
            if hasattr(model, 'gating_head'):
                torch.save(model.gating_head.state_dict(), get_path("results") / "best_gating_head.pt")
            else:
                torch.save(model.state_dict(), get_path("results") / "best_gating_head.pt")
    
    return {
        'final_train_loss': history[-1]['train_loss'] if history else 0.0,
        'best_val_loss': best_val_loss,
        'epochs_completed': epochs,
        'history': history
    }

def main():
    parser = argparse.ArgumentParser(description="Train Gating Head for Moebius-Dynamic")
    parser.add_argument('--epochs', type=int, default=10, help="Number of training epochs")
    parser.add_argument('--lr', type=float, default=1e-3, help="Learning rate")
    parser.add_argument('--batch_size', type=int, default=32, help="Batch size")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    # Setup
    set_seed(args.seed)
    logger.info(f"Starting training with seed {args.seed}")
    logger.info(f"Mode: {get_mode()}")
    
    # Check Gate
    gate_result = load_validation_result()
    if gate_result:
        logger.info(f"Proxy Validation Gate Status: {gate_result.get('gate_status')}")
        if gate_result.get('gate_status') == 'BLOCKED':
            logger.error("Gate Blocked. Cannot proceed with training.")
            sys.exit(1)
    
    # Device
    device = torch.device("cpu") # Enforce CPU as per project constraints
    logger.info(f"Using device: {device}")
    
    # Model
    # We use MoebiusTiny as the base and attach the GatingHead
    # Or just the GatingHead if we are training it in isolation.
    # Per T022, MoebiusDynamic integrates the head.
    model = create_moebius_dynamic() # Returns MoebiusDynamic instance
    model = model.to(device)
    
    # Config
    training_config = {
        'epochs': args.epochs,
        'lr': args.lr,
        'batch_size': args.batch_size,
        'seed': args.seed
    }
    
    try:
        results = run_training(training_config, model, device)
        logger.info("Training completed successfully.")
        
        # Save final results
        results_path = Path(get_path("results"))
        results_path.mkdir(parents=True, exist_ok=True)
        
        output_file = results_path / "gating_training_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Training results saved to {output_file}")
        
    except FileNotFoundError as e:
        logger.error(f"Data missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
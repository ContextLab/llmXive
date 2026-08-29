"""
End-to-End Fine-tuning Script for Moebius-Dynamic.

This script performs fine-tuning of the Moebius-Dynamic model (MoebiusTiny + GatingHead)
on the prepared dataset. It integrates the dynamic rank modulation logic and
optimizes for both reconstruction quality and gating accuracy.

Workflow:
1. Load configuration and seed environment.
2. Initialize MoebiusDynamic model.
3. Load training data (masked images + complexity scores).
4. Run training loop with multi-task loss (Reconstruction + Gating Regression).
5. Save model weights and training logs.

Dependencies:
- code/config.py, code/utils/seed.py, code/utils/logger.py
- code/models/moebius_dynamic.py
- code/data/loader.py, code/data/mask_generator.py (for metrics loading)
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import time

# Third-party imports
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.functional import mse_loss, smooth_l1_loss

# Project imports
from config import get_mode, is_ci_mode, get_path, ensure_paths_exist
from utils.seed import set_seed
from utils.logger import get_logger, setup_project_logger
from utils.cpu_profiler import profile_function, get_timing_report
from models.moebius_dynamic import create_moebius_dynamic, MoebiusDynamic
from data.loader import get_image_paths
from data.mask_generator import generate_mask_batch
from data.annotator import load_research_annotations, generate_ci_scores
from eval.stats import load_scores_csv, load_mask_metrics_csv

# Configure logging
logger = setup_project_logger("train_end_to_end")


class InpaintingDataset(Dataset):
    """
    PyTorch Dataset for Inpainting Fine-tuning.
    
    Loads images, generates masks (or loads pre-generated), and retrieves
    complexity scores for gating supervision.
    """
    def __init__(
        self, 
        image_paths: List[str], 
        mode: str, 
        score_file: Optional[Path] = None,
        metrics_file: Optional[Path] = None,
        img_size: int = 128,
        transform=None
    ):
        self.image_paths = image_paths
        self.mode = mode
        self.score_file = score_file
        self.metrics_file = metrics_file
        self.img_size = img_size
        self.transform = transform
        
        # Load scores if available
        self.scores = {}
        self.metrics = {}
        
        if score_file and score_file.exists():
            self.scores = load_scores_csv(score_file)
            logger.info(f"Loaded {len(self.scores)} scores from {score_file}")
        else:
            logger.warning(f"Score file not found: {score_file}. Using default score 3.0.")
            self.scores = {i: 3.0 for i in range(len(image_paths))}

        if metrics_file and metrics_file.exists():
            self.metrics = load_mask_metrics_csv(metrics_file)
            logger.info(f"Loaded {len(self.metrics)} metrics from {metrics_file}")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Load image (simplified PIL loading for this pipeline)
        # In a full pipeline, we would use torchvision.transforms
        from PIL import Image
        img_path = self.image_paths[idx]
        
        try:
            image = Image.open(img_path).convert('RGB')
            image = image.resize((self.img_size, self.img_size), Image.Resampling.LANCZOS)
            image_np = np.array(image, dtype=np.float32) / 255.0
        except Exception as e:
            logger.error(f"Failed to load image {img_path}: {e}")
            # Fallback to black image to prevent crash
            image_np = np.zeros((self.img_size, self.img_size, 3), dtype=np.float32)

        # Generate mask on-the-fly for training (or load if pre-computed)
        # For simplicity in this script, we generate a random mask per sample
        # In a robust pipeline, we would load pre-generated masks from data/processed
        mask = generate_mask_batch(1, self.img_size, self.img_size, seed=idx)[0]
        
        # Convert to torch tensors
        image_tensor = torch.from_numpy(image_np).permute(2, 0, 1) # C, H, W
        mask_tensor = torch.from_numpy(mask).unsqueeze(0) # 1, H, W
        
        # Get ground truth complexity score
        # Map image path or index to score. Using index as fallback key.
        score = self.scores.get(idx, 3.0)
        score_tensor = torch.tensor(score, dtype=torch.float32)

        return {
            "image": image_tensor,
            "mask": mask_tensor,
            "gt_score": score_tensor,
            "path": img_path
        }


def compute_reconstruction_loss(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """
    Compute L1 reconstruction loss on the masked region.
    """
    # mask is 0 for hole, 1 for known. We want to reconstruct where mask=0.
    inv_mask = 1.0 - mask
    loss = torch.abs(pred - target)
    loss = (loss * inv_mask).sum() / (inv_mask.sum() + 1e-8)
    return loss


def train_epoch(
    model: MoebiusDynamic,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
    config: Dict[str, Any]
) -> Dict[str, float]:
    """
    Train for one epoch.
    """
    model.train()
    total_loss = 0.0
    total_recon_loss = 0.0
    total_gate_loss = 0.0
    samples = 0

    for batch in dataloader:
        images = batch["image"].to(device)
        masks = batch["mask"].to(device)
        gt_scores = batch["gt_score"].to(device)

        optimizer.zero_grad()

        # Forward pass
        # Model expects: image, mask
        # Returns: output_image, gating_state (complexity score)
        output_image, gating_state = model(images, masks)

        # Loss 1: Reconstruction (L1)
        recon_loss = compute_reconstruction_loss(output_image, images, masks)

        # Loss 2: Gating Regression (L1 or MSE)
        # Gating state output is a scalar complexity score
        gate_loss = smooth_l1_loss(gating_state, gt_scores)

        # Total Loss
        lambda_recon = config.get("lambda_recon", 1.0)
        lambda_gate = config.get("lambda_gate", 0.5)
        
        total_batch_loss = (lambda_recon * recon_loss) + (lambda_gate * gate_loss)

        # Backward
        total_batch_loss.backward()
        
        # Gradient clipping to prevent explosion
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()

        total_loss += total_batch_loss.item()
        total_recon_loss += recon_loss.item()
        total_gate_loss += gate_loss.item()
        samples += 1

    return {
        "loss": total_loss / samples,
        "recon_loss": total_recon_loss / samples,
        "gate_loss": total_gate_loss / samples
    }


@profile_function
def run_training(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main training loop orchestration.
    """
    # Setup
    mode = get_mode()
    seed = config.get("seed", 42)
    set_seed(seed)
    
    device = torch.device("cpu") # CPU-only constraint
    logger.info(f"Running on device: {device}")
    logger.info(f"Mode: {mode}")

    # Paths
    data_dir = get_path("data_processed")
    annotations_dir = get_path("data_annotations")
    results_dir = get_path("data_results")
    models_dir = get_path("data_models")
    
    ensure_paths_exist([results_dir, models_dir])

    # Load Data
    # T012/T017 should have populated data/processed/masked_images and data/annotations
    image_paths = get_image_paths(data_dir, pattern="*.png") # Adjust pattern if needed
    
    if not image_paths:
        logger.warning("No images found in data/processed. Attempting to load from raw.")
        image_paths = get_image_paths(get_path("data_raw"), pattern="*.jpg")
    
    if not image_paths:
        raise FileNotFoundError("No training images found. Ensure data preparation (T017) is complete.")

    logger.info(f"Found {len(image_paths)} images for training.")

    # Determine score file based on mode
    score_file = None
    if mode == "RESEARCH":
        score_file = Path(annotations_dir) / "human_scores.csv"
        if not score_file.exists():
            # T014c requirement: Raise error if missing in Research Mode
            raise FileNotFoundError(f"Research mode active but human scores missing at {score_file}")
    else:
        # CI Mode
        score_file = Path(annotations_dir) / "decoupled_scores.csv"
        if not score_file.exists():
            logger.warning(f"CI Mode score file {score_file} not found. Generating synthetic scores.")
            # Generate on the fly if missing (T014a logic fallback)
            generate_ci_scores(len(image_paths), score_file)
    
    # Metrics file (from mask generation)
    metrics_file = Path(data_dir) / "mask_metrics.csv"
    
    dataset = InpaintingDataset(
        image_paths=image_paths,
        mode=mode,
        score_file=score_file,
        metrics_file=metrics_file,
        img_size=config.get("img_size", 128)
    )

    dataloader = DataLoader(
        dataset, 
        batch_size=config.get("batch_size", 8), 
        shuffle=True,
        num_workers=0 # CPU constraint
    )

    # Model
    model = create_moebius_dynamic(
        in_channels=3,
        hidden_dim=config.get("hidden_dim", 64),
        num_blocks=config.get("num_blocks", 4),
        rank_range=(1, 5)
    )
    model = model.to(device)
    
    param_count = sum(p.numel() for p in model.parameters())
    logger.info(f"Model parameters: {param_count:,}")

    # Optimizer
    optimizer = optim.Adam(model.parameters(), lr=config.get("lr", 1e-4))
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=config.get("lr_decay_step", 5), gamma=0.5)

    # Training Loop
    epochs = config.get("epochs", 10)
    history = []
    best_loss = float('inf')

    logger.info(f"Starting training for {epochs} epochs...")
    start_time = time.time()

    for epoch in range(epochs):
        epoch_start = time.time()
        logs = train_epoch(model, dataloader, optimizer, device, epoch, config)
        scheduler.step()
        
        epoch_time = time.time() - epoch_start
        
        log_entry = {
            "epoch": epoch + 1,
            "loss": logs["loss"],
            "recon_loss": logs["recon_loss"],
            "gate_loss": logs["gate_loss"],
            "lr": optimizer.param_groups[0]['lr'],
            "time_s": round(epoch_time, 2)
        }
        history.append(log_entry)
        
        logger.info(
            f"Epoch {epoch+1}/{epochs} | Loss: {log_entry['loss']:.4f} | "
            f"Recon: {log_entry['recon_loss']:.4f} | Gate: {log_entry['gate_loss']:.4f} | "
            f"LR: {log_entry['lr']:.6f} | Time: {log_entry['time_s']}s"
        )

        if logs["loss"] < best_loss:
            best_loss = logs["loss"]
            # Save best checkpoint
            best_path = Path(models_dir) / "moebius_dynamic_best.pt"
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss": best_loss,
                "config": config
            }, best_path)
            logger.info(f"Saved new best model to {best_path}")

    total_time = time.time() - start_time
    logger.info(f"Training completed in {total_time:.2f} seconds.")

    # Save final model
    final_path = Path(models_dir) / "moebius_dynamic_final.pt"
    torch.save({
        "epoch": epochs,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss": history[-1]["loss"],
        "config": config
    }, final_path)
    logger.info(f"Saved final model to {final_path}")

    # Save history
    history_path = Path(results_dir) / "training_history.json"
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    logger.info(f"Saved training history to {history_path}")

    return {
        "status": "success",
        "final_loss": history[-1]["loss"],
        "best_loss": best_loss,
        "epochs": epochs,
        "model_path": str(final_path),
        "history_path": str(history_path)
    }


def main():
    parser = argparse.ArgumentParser(description="End-to-End Fine-tuning for Moebius-Dynamic")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config module")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Override config with CLI args if provided
    training_config = {
        "epochs": args.epochs,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "seed": args.seed,
        "img_size": 128,
        "hidden_dim": 64,
        "num_blocks": 4,
        "lambda_recon": 1.0,
        "lambda_gate": 0.5
    }

    try:
        result = run_training(training_config)
        logger.info("Training finished successfully.")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
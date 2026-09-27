"""
Task T024: Implement end-to-end fine-tuning for Moebius-Dynamic.

This script fine-tunes the full Moebius-Dynamic model (gating head + backbone)
on the masked image dataset. It respects the CPU-only constraint and memory limits.
It loads the pre-trained weights from T023 (gating) and T020 (backbone) if available,
otherwise initializes from scratch (for CI mode).

It produces:
  - data/results/e2e_training_log.json (training metrics)
  - code/models/moebius_dynamic_finetuned.pt (final weights)
"""
import os
import sys
import json
import argparse
import logging
import time
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Project imports (API surface)
from config import get_mode, is_ci_mode, is_research_mode, get_path, ensure_paths_exist
from utils.logger import get_logger, setup_project_logger
from utils.seed import set_seed
from models.moebius_dynamic import MoebiusDynamic, create_moebius_dynamic
from models.moebius_tiny import MoebiusTiny
from data.loader import fetch_places365_subset, get_image_paths
from data.mask_generator import generate_mask_batch
from utils.cpu_profiler import cpu_timer, get_timing_report, reset_timing_results

# Setup logger
logger = setup_project_logger("train_end_to_end")

# Constants
DEFAULT_EPOCHS = 5
BATCH_SIZE = 4
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-2
DEVICE = "cpu"  # Enforced CPU-only per project constraints

class InpaintingDataset:
    """
    A simple dataset class for the end-to-end training.
    It loads images, applies masks on-the-fly (or loads pre-computed if available),
    and returns (input, target, mask) tuples.
    
    For CI mode with memory constraints, it streams a small subset.
    """
    def __init__(self, data_root: Path, sample_size: int = 50, seed: int = 42):
        self.data_root = data_root
        self.sample_size = sample_size
        self.seed = seed
        self.image_paths = []
        self._load_paths()
    
    def _load_paths(self):
        """Load image paths from the raw dataset directory."""
        raw_dir = self.data_root / "raw"
        if not raw_dir.exists():
            logger.warning(f"Raw data directory not found: {raw_dir}. Creating empty dataset.")
            return
        
        # Simple glob for images
        extensions = {".jpg", ".jpeg", ".png", ".bmp"}
        for ext in extensions:
            self.image_paths.extend(raw_dir.glob(f"*{ext}"))
            self.image_paths.extend(raw_dir.glob(f"*{ext.upper()}") if ext != ext.upper() else [])
        
        # Filter duplicates and sort for determinism
        self.image_paths = sorted(list(set(self.image_paths)))
        
        if len(self.image_paths) == 0:
            logger.warning(f"No images found in {raw_dir}. Dataset will be empty.")
            return

        # Sample if necessary (for CI memory constraints)
        if len(self.image_paths) > self.sample_size:
            # Deterministic sampling based on seed
            import random
            random.seed(self.seed)
            self.image_paths = random.sample(self.image_paths, self.sample_size)
            logger.info(f"Sampled {len(self.image_paths)} images from {len(self.image_paths) + len(self.image_paths) - self.sample_size} total (seed={self.seed}).")
        else:
            logger.info(f"Loaded all {len(self.image_paths)} available images.")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        """
        Load image, apply mask, return tensors.
        Returns: (input_tensor, target_tensor, mask_tensor)
        """
        from PIL import Image
        import torch
        import numpy as np

        path = self.image_paths[idx]
        
        # Load image
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            logger.error(f"Failed to load image {path}: {e}")
            # Return zeros on error to keep pipeline running
            return (torch.zeros(3, 64, 64), torch.zeros(3, 64, 64), torch.zeros(1, 64, 64))

        # Resize to model input size (assume 64x64 for Tiny/CPU)
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        img_np = np.array(img).astype(np.float32) / 255.0
        img_np = np.transpose(img_np, (2, 0, 1)) # C, H, W
        
        target = torch.from_numpy(img_np)
        
        # Generate a random mask (or load pre-computed if available)
        # For simplicity in this script, we generate a random mask on-the-fly
        # to ensure the script runs without external dependencies on pre-generated masks.
        # In a real scenario, this would load from data/processed/masked_images/
        mask = self._generate_random_mask(64, 64)
        mask = torch.from_numpy(mask).float()
        
        # Apply mask
        masked_img = target * (1 - mask)
        
        return masked_img, target, mask

    def _generate_random_mask(self, h, w):
        """Generate a simple random rectangular mask."""
        import numpy as np
        mask = np.zeros((h, w), dtype=np.float32)
        
        # Random center
        cx, cy = np.random.randint(0, w), np.random.randint(0, h)
        # Random size
        rw, rh = np.random.randint(w//4, w//2), np.random.randint(h//4, h//2)
        
        x1, y1 = max(0, cx - rw//2), max(0, cy - rh//2)
        x2, y2 = min(w, x1 + rw), min(h, y1 + rh)
        
        mask[y1:y2, x1:x2] = 1.0
        return mask

def compute_reconstruction_loss(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """
    Compute L1 reconstruction loss on the masked region.
    """
    # Only compute loss where mask is 1 (the missing region)
    # Or sometimes total variation + L1 on whole image.
    # Standard inpainting: L1 on masked region.
    masked_pred = pred * mask
    masked_target = target * mask
    
    loss = torch.mean(torch.abs(masked_pred - masked_target))
    return loss

def train_epoch(
    model: MoebiusDynamic,
    dataloader: Any,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    device: str
) -> Dict[str, float]:
    """
    Train one epoch.
    """
    model.train()
    total_loss = 0.0
    total_samples = 0
    
    for batch_idx, (inputs, targets, masks) in enumerate(dataloader):
        inputs = inputs.to(device)
        targets = targets.to(device)
        masks = masks.to(device)
        
        optimizer.zero_grad()
        
        # Forward pass
        # MoebiusDynamic expects (B, C, H, W) and returns (B, C, H, W)
        outputs = model(inputs, masks)
        
        # Loss
        loss = compute_reconstruction_loss(outputs, targets, masks)
        
        # Backward
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        total_samples += inputs.size(0)
        
        if batch_idx % 10 == 0:
            logger.debug(f"Epoch {epoch} [{batch_idx}/{len(dataloader)}] Loss: {loss.item():.4f}")
    
    avg_loss = total_loss / max(total_samples, 1)
    return {"loss": avg_loss}

def run_training(
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
    data_root: Path,
    output_dir: Path,
    resume_from: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main training loop.
    """
    set_seed(seed)
    
    # Initialize dataset
    dataset = InpaintingDataset(data_root, sample_size=50, seed=seed)
    if len(dataset) == 0:
        logger.error("Dataset is empty. Cannot train.")
        return {"error": "Empty dataset"}
    
    # DataLoader (simple list iteration for CPU demo)
    # In real code, use torch.utils.data.DataLoader with num_workers=0 for CPU safety
    import torch.utils.data as data
    dataloader = data.DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    
    # Initialize Model
    logger.info("Initializing Moebius-Dynamic model...")
    model = create_moebius_dynamic(mode="tiny") # Use tiny for CPU feasibility
    model = model.to(DEVICE)
    
    # Load pretrained weights if available (from T023 gating or T020 backbone)
    if resume_from and resume_from.exists():
        logger.info(f"Resuming from checkpoint: {resume_from}")
        try:
            state = torch.load(resume_from, map_location=DEVICE)
            model.load_state_dict(state, strict=False)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}. Training from scratch.")
    else:
        # Check for standard paths
        default_gating_ckpt = get_path("results") / "gating_checkpoint.pt"
        default_backbone_ckpt = get_path("models") / "moebius_tiny.pt"
        
        if default_gating_ckpt.exists():
            logger.info(f"Loading gating weights from {default_gating_ckpt}")
            try:
                state = torch.load(default_gating_ckpt, map_location=DEVICE)
                model.gating_head.load_state_dict(state, strict=False)
            except Exception as e:
                logger.warning(f"Could not load gating head: {e}")
        
        if default_backbone_ckpt.exists():
            logger.info(f"Loading backbone weights from {default_backbone_ckpt}")
            try:
                state = torch.load(default_backbone_ckpt, map_location=DEVICE)
                # Assuming MoebiusDynamic has a 'backbone' or similar attribute
                if hasattr(model, 'backbone'):
                    model.backbone.load_state_dict(state, strict=False)
                else:
                    # Fallback: try loading into model itself if it's just the tiny model wrapped
                    model.load_state_dict(state, strict=False)
            except Exception as e:
                logger.warning(f"Could not load backbone: {e}")

    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    
    # Training loop
    history = []
    start_time = time.time()
    
    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        metrics = train_epoch(model, dataloader, optimizer, epoch, DEVICE)
        epoch_time = time.time() - epoch_start
        
        metrics["epoch_time"] = epoch_time
        history.append(metrics)
        
        logger.info(f"Epoch {epoch}/{epochs} - Loss: {metrics['loss']:.4f} - Time: {epoch_time:.2f}s")
        
        # Garbage collection
        gc.collect()
    
    total_time = time.time() - start_time
    
    # Save final model
    output_path = output_dir / "moebius_dynamic_finetuned.pt"
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_path)
    logger.info(f"Model saved to {output_path}")
    
    # Save log
    log_path = output_dir / "e2e_training_log.json"
    log_data = {
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "seed": seed,
        "total_time_seconds": total_time,
        "history": history,
        "final_loss": history[-1]["loss"] if history else None,
        "mode": get_mode(),
        "timestamp": datetime.now().isoformat()
    }
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Training log saved to {log_path}")
    
    return log_data

def main():
    parser = argparse.ArgumentParser(description="End-to-End Fine-tuning for Moebius-Dynamic")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE, help="Batch size")
    parser.add_argument("--lr", type=float, default=LEARNING_RATE, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume")
    
    args = parser.parse_args()
    
    # Ensure paths exist
    ensure_paths_exist()
    
    data_root = get_path("raw")
    output_dir = get_path("results")
    
    resume_path = Path(args.resume) if args.resume else None
    
    logger.info(f"Starting End-to-End Training (Mode: {get_mode()})")
    logger.info(f"Data Root: {data_root}, Output Dir: {output_dir}")
    
    try:
        result = run_training(
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            seed=args.seed,
            data_root=data_root,
            output_dir=output_dir,
            resume_from=resume_path
        )
        
        if "error" in result:
            logger.error(f"Training failed: {result['error']}")
            sys.exit(1)
            
        logger.info("Training completed successfully.")
        
    except Exception as e:
        logger.exception(f"Unexpected error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
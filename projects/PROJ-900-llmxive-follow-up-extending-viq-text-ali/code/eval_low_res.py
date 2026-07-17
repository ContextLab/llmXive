"""
Evaluation script for User Story 1: Low-Resolution Reconstruction Verification.

This script loads the trained VQ-VAE codebook (from T014), samples a batch of
64x64 images from the COCO dataset using the streaming loader (T005),
reconstructs them using the model, and calculates the PSNR.

It writes the results to `data/results/reconstruction_metrics.json`.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import torch
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm

# Project imports
from config import get_config
from data_loader import COCOStreamingDataset, get_dataloader
from model import get_model, ResNetVQVAE
from utils import calculate_psnr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_checkpoint(checkpoint_path: str, model: torch.nn.Module) -> torch.nn.Module:
    """Load weights from a checkpoint file into the model."""
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(
            f"Checkpoint not found at {checkpoint_path}. "
            "Please ensure T014 (training) has completed successfully."
        )
    
    logger.info(f"Loading checkpoint from {checkpoint_path}...")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    
    # Handle potential dict vs module state dict structures
    if isinstance(checkpoint, dict) and "model_state" in checkpoint:
        model.load_state_dict(checkpoint["model_state"])
    else:
        model.load_state_dict(checkpoint)
    
    logger.info("Checkpoint loaded successfully.")
    return model

@torch.no_grad()
def evaluate_reconstruction(
    model: ResNetVQVAE,
    dataloader: torch.utils.data.DataLoader,
    num_samples: int = 32,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Run reconstruction on a sample of images and calculate PSNR.
    
    Returns a dictionary with mean PSNR, individual scores, and sample count.
    """
    model.eval()
    psnr_scores: List[float] = []
    
    logger.info(f"Starting evaluation on {num_samples} samples...")
    
    count = 0
    for batch in dataloader:
        if count >= num_samples:
            break
        
        # Batch structure expected from COCOStreamingDataset:
        # Assuming 'image' is the key, shape [B, C, H, W]
        images = batch.get("image")
        if images is None:
            logger.warning("Batch missing 'image' key, skipping.")
            continue
        
        # Ensure tensor on device
        if not isinstance(images, torch.Tensor):
            # Handle case where dataset returns PIL images and collate_fn converts
            images = torch.stack([F.interpolate(img.unsqueeze(0).float(), size=(64, 64), mode='bilinear', align_corners=False) 
                                 if img.shape[-1] != 64 else img 
                                 for img in images])
        
        images = images.to(device)
        
        # Forward pass: Encode -> Quantize -> Decode
        # model.encode returns embeddings, model.quantize handles codebook lookup, model.decode reconstructs
        # Depending on ResNetVQVAE implementation, we might call specific methods or the whole module
        # Assuming standard VQ-VAE interface:
        
        # 1. Encode
        z = model.encode(images)
        
        # 2. Quantize (returns quantized embeddings and loss info)
        z_q, _, _ = model.quantize(z)
        
        # 3. Decode
        recon = model.decode(z_q)
        
        # Ensure reconstruction is clamped to [0, 1] if inputs are
        recon = torch.clamp(recon, 0.0, 1.0)
        images = torch.clamp(images, 0.0, 1.0)
        
        # Calculate PSNR for each item in the batch
        for i in range(images.size(0)):
            if count >= num_samples:
                break
            
            orig = images[i].cpu().numpy()
            rec = recon[i].cpu().numpy()
            
            psnr_val = calculate_psnr(orig, rec)
            psnr_scores.append(psnr_val)
            count += 1
    
    if not psnr_scores:
        raise RuntimeError("No valid PSNR scores calculated. Check dataset and model.")
    
    mean_psnr = float(np.mean(psnr_scores))
    std_psnr = float(np.std(psnr_scores))
    
    logger.info(f"Evaluation complete. Mean PSNR: {mean_psnr:.2f} dB (Std: {std_psnr:.2f})")
    
    return {
        "mean_psnr": mean_psnr,
        "std_psnr": std_psnr,
        "count": count,
        "threshold_target": 15.0,
        "passed": mean_psnr > 15.0
    }

def main():
    config = get_config()
    device = "cpu"  # Enforcing CPU as per US1 constraints
    
    # Paths
    checkpoint_path = str(config.paths.results / "codebook_v0.pth")
    output_path = str(config.paths.results / "reconstruction_metrics.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Initialize Model
    # Using get_model to ensure we get the same architecture definition as training
    model = get_model()
    model = model.to(device)
    
    # Load Checkpoint
    model = load_checkpoint(checkpoint_path, model)
    
    # Initialize Data Loader
    # Re-using the streaming dataset config from T005/T012
    # Note: T013 handles sampling strategy; we assume config.batch_size is set appropriately
    dataset = COCOStreamingDataset(
        split="train",
        resolution=config.dataset_limits.get("resolution", 64),
        max_samples=config.dataset_limits.get("max_eval_samples", 100)
    )
    dataloader = get_dataloader(dataset, batch_size=config.batch_size, shuffle=False)
    
    # Run Evaluation
    try:
        results = evaluate_reconstruction(
            model=model,
            dataloader=dataloader,
            num_samples=config.dataset_limits.get("max_eval_samples", 32),
            device=device
        )
        
        # Save Results
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
        if not results["passed"]:
            logger.warning(f"PSNR threshold ({config.thresholds.semantic_threshold}) not met.")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

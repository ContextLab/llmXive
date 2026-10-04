import os
import math
import random
import logging
import time
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from datasets import load_dataset
from transformers import CLIPTextModel, CLIPTokenizer
import psutil

# Import from project modules
from config import get_config, set_config, Config
from model import Codebook, ProjectionHead, FrozenViQWrapper, FrozenCLIPTextWrapper, ResNetVQVAE, get_model
from utils import calculate_texture_complexity
from data_loader import get_coco_iterator

# Setup logging
def setup_logging(log_file: str = "data/results/train_log.json") -> logging.Logger:
    logger = logging.getLogger("train")
    logger.setLevel(logging.INFO)
    
    # File handler for JSON logs
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def set_seed(seed: int):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_ram_usage_gb() -> float:
    """Get current RAM usage in GB using psutil."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def log_codebook_usage(logger: logging.Logger, codebook: Codebook, step: int):
    """Log codebook usage statistics."""
    if hasattr(codebook, 'embedding') and codebook.embedding is not None:
        # Calculate usage (simplified - in real impl would track indices)
        logger.info(f"Step {step}: Codebook size {codebook.codebook_size}")

def info_nce_loss(visual_features: torch.Tensor, text_features: torch.Tensor, temperature: float = 0.07) -> torch.Tensor:
    """
    Compute InfoNCE contrastive loss.
    Uses in-batch negatives.
    """
    # Normalize features
    visual_features = F.normalize(visual_features, dim=1)
    text_features = F.normalize(text_features, dim=1)
    
    batch_size = visual_features.size(0)
    
    # Compute similarity matrix
    logits = torch.matmul(visual_features, text_features.T) / temperature
    
    # Labels are diagonal (positive pairs)
    labels = torch.arange(batch_size, device=visual_features.device)
    
    # Cross entropy loss with in-batch negatives
    loss = F.cross_entropy(logits, labels)
    return loss

def vq_loss(reconstructions: torch.Tensor, original: torch.Tensor, 
            codebook: Codebook, commitment_weight: float = 0.25) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Compute VQ-VAE loss components.
    Returns: total_loss, vq_loss, commitment_loss
    """
    # Reconstruction loss (MSE)
    recon_loss = F.mse_loss(reconstructions, original)
    
    # VQ loss: commitment loss + codebook loss
    # Commitment loss: encourage encoder to match codebook
    commitment_loss = F.mse_loss(codebook.embeddings, original.detach()) * commitment_weight
    
    # Codebook loss: encourage codebook to match encoder outputs
    codebook_loss = F.mse_loss(codebook.embeddings.detach(), original) * commitment_weight
    
    # Total VQ loss (reconstruction + commitment + codebook)
    total_vq_loss = recon_loss + commitment_loss + codebook_loss
    
    return total_vq_loss, commitment_loss, codebook_loss

def build_models(config: Config) -> Tuple[ResNetVQVAE, FrozenCLIPTextWrapper, torch.optim.Optimizer]:
    """Build and initialize models."""
    device = torch.device("cpu")
    
    # Initialize VQ-VAE model
    model = get_model("vq-vae")
    model = model.to(device)
    
    # Initialize frozen CLIP text wrapper
    text_wrapper = FrozenCLIPTextWrapper()
    text_wrapper = text_wrapper.to(device)
    
    # Optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    
    return model, text_wrapper, optimizer

def tune_batch_size(config: Config, max_ram_gb: float = 6.5) -> int:
    """
    Dynamically tune batch size to fit within RAM constraints.
    Returns the largest batch size that fits.
    """
    logger = logging.getLogger("train")
    batch_size = config.batch_size
    
    logger.info(f"Starting batch size tuning with {batch_size}")
    
    while batch_size >= 1:
        try:
            # Get a sample batch
            coco_iter = get_coco_iterator(split="train", streaming=True)
            sample = next(coco_iter)
            
            # Simulate processing
            images = sample['image']
            if not isinstance(images, list):
                images = [images]
            
            # Resize to 64x64 for low-res training
            processed_images = []
            for img in images[:batch_size]:
                img = img.resize((64, 64))
                processed_images.append(img)
            
            # Convert to tensor
            if processed_images:
                tensor = torch.stack([torch.from_numpy(np.array(img)).float() for img in processed_images])
                _ = tensor * 2.0  # Dummy operation to trigger memory allocation
            
            current_ram = get_ram_usage_gb()
            logger.info(f"Batch size {batch_size}: RAM usage {current_ram:.2f} GB")
            
            if current_ram <= max_ram_gb:
                logger.info(f"Final batch_size: {batch_size}")
                return batch_size
            
            batch_size -= 1
            
        except Exception as e:
            logger.warning(f"Batch size {batch_size} failed: {e}")
            batch_size -= 1
    
    logger.error("Could not find a valid batch size >= 1")
    return 1

def train(config: Config, checkpoint_path: str = "data/results/codebook_v0.pth", 
          max_steps: int = 1000, max_time_hours: float = 5.5):
    """
    Main training loop for VQ-VAE with frozen ViQ encoder.
    """
    logger = setup_logging()
    set_seed(config.seed)
    
    device = torch.device("cpu")
    logger.info(f"Training on device: {device}")
    
    # Tune batch size
    batch_size = tune_batch_size(config)
    config.batch_size = batch_size
    logger.info(f"Using batch size: {batch_size}")
    
    # Build models
    model, text_wrapper, optimizer = build_models(config)
    model.train()
    
    # Training parameters
    temperature = 0.07
    vq_weight = 1.0
    commitment_weight = 0.25
    
    # Training loop
    start_time = time.time()
    initial_loss = None
    final_loss = None
    
    # Data iterator
    coco_iter = get_coco_iterator(split="train", streaming=True)
    
    step = 0
    while step < max_steps:
        elapsed_time = time.time() - start_time
        elapsed_hours = elapsed_time / 3600
        
        # Check time limit
        if elapsed_hours > max_time_hours:
            logger.critical(f"Training time limit exceeded ({elapsed_hours:.2f} > {max_time_hours} hours). Saving checkpoint.")
            break
        
        try:
            # Get batch
            sample = next(coco_iter)
            images = sample['image']
            captions = sample.get('caption', [''] * len(images))
            
            if not isinstance(images, list):
                images = [images]
            if not isinstance(captions, list):
                captions = [captions]
            
            # Process images to 64x64
            processed_images = []
            valid_captions = []
            for img, cap in zip(images[:batch_size], captions[:batch_size]):
                img_resized = img.resize((64, 64))
                processed_images.append(img_resized)
                valid_captions.append(cap)
            
            if not processed_images:
                continue
            
            # Convert to tensor
            image_tensor = torch.stack([
                torch.from_numpy(np.array(img)).float() / 255.0 
                for img in processed_images
            ]).unsqueeze(1)  # Add channel dimension
            
            # Ensure proper shape: [batch, 1, 64, 64]
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(1)
            
            image_tensor = image_tensor.to(device)
            
            # Forward pass through VQ-VAE
            reconstructions, codebook_loss, commitment_loss = model(image_tensor)
            
            # Get text embeddings
            text_features = text_wrapper.encode(valid_captions)
            text_features = text_features.to(device)
            
            # Get visual features from reconstruction (projected)
            visual_features = model.get_visual_features(reconstructions)
            visual_features = visual_features.to(device)
            
            # Compute losses
            recon_loss = F.mse_loss(reconstructions, image_tensor)
            contrastive_loss = info_nce_loss(visual_features, text_features, temperature)
            
            # Total loss
            total_loss = (
                vq_weight * (recon_loss + codebook_loss + commitment_loss) +
                contrastive_loss
            )
            
            # Backward pass
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
            
            # Log metrics
            if initial_loss is None:
                initial_loss = total_loss.item()
            final_loss = total_loss.item()
            
            step += 1
            
            # Log every 10 steps
            if step % 10 == 0:
                logger.info(
                    f"Step {step}: Total Loss={total_loss.item():.4f}, "
                    f"Recon={recon_loss.item():.4f}, VQ={codebook_loss.item():.4f}, "
                    f"Commit={commitment_loss.item():.4f}, Contrastive={contrastive_loss.item():.4f}, "
                    f"Time={elapsed_hours:.2f}h"
                )
                
                # Log to JSON file
                log_entry = {
                    "step": step,
                    "total_loss": total_loss.item(),
                    "vq_loss": (recon_loss.item() + codebook_loss.item() + commitment_loss.item()),
                    "contrastive_loss": contrastive_loss.item(),
                    "elapsed_time": elapsed_hours,
                    "ram_gb": get_ram_usage_gb()
                }
                
                # Append to log file
                log_path = Path("data/results/train_log.json")
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            
        except StopIteration:
            logger.info("Dataset exhausted, restarting iterator")
            coco_iter = get_coco_iterator(split="train", streaming=True)
            continue
        except Exception as e:
            logger.error(f"Error at step {step}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    # Final checks
    if initial_loss is not None and final_loss is not None:
        loss_ratio = final_loss / initial_loss
        logger.info(f"Loss convergence: Initial={initial_loss:.4f}, Final={final_loss:.4f}, Ratio={loss_ratio:.4f}")
        
        if loss_ratio >= 0.5:
            logger.warning("Loss did not decrease sufficiently (final >= 0.5 * initial)")
    
    # Save checkpoint
    checkpoint = {
        'step': step,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'config': {
            'batch_size': config.batch_size,
            'learning_rate': config.learning_rate,
            'seed': config.seed
        }
    }
    
    checkpoint_path = Path(checkpoint_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, checkpoint_path)
    logger.info(f"Checkpoint saved to {checkpoint_path}")
    
    logger.info(f"Training completed. Steps: {step}, Time: {elapsed_hours:.2f}h")
    return step, final_loss

def main():
    parser = argparse.ArgumentParser(description="Train VQ-VAE with frozen ViQ encoder")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config file")
    parser.add_argument("--max_steps", type=int, default=1000, help="Maximum training steps")
    parser.add_argument("--max_time_hours", type=float, default=5.5, help="Maximum training time in hours")
    parser.add_argument("--checkpoint", type=str, default="data/results/codebook_v0.pth", help="Checkpoint path")
    
    args = parser.parse_args()
    
    # Load config
    config = get_config()
    
    # Run training
    train(
        config=config,
        checkpoint_path=args.checkpoint,
        max_steps=args.max_steps,
        max_time_hours=args.max_time_hours
    )

if __name__ == "__main__":
    main()

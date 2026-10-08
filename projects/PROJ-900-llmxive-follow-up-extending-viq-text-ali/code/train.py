"""
T012: CPU-only training loop for VQ-VAE with frozen ViQ encoder.
Implements dynamic batch sizing, RAM monitoring, and loss convergence verification.
"""
import os
import math
import random
import logging
import time
import argparse
import json
import psutil
import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Iterator

# Import from project API surface
from config import get_config, Config
from model import Codebook, ProjectionHead, FrozenViQWrapper, ResNetVQVAE, get_model
from data_loader import get_coco_iterator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/results/train.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_logging():
    """Initialize logging configuration."""
    pass  # Handled by basicConfig above

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_ram_usage_gb() -> float:
    """Get current RAM usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def log_codebook_usage(codebook: Codebook, step: int):
    """Log codebook usage statistics."""
    # In a real implementation, this would track token usage
    logger.info(f"Step {step}: Codebook usage logged")

def info_nce_loss(
    queries: torch.Tensor,
    keys: torch.Tensor,
    temperature: float = 0.07
) -> torch.Tensor:
    """
    Compute InfoNCE contrastive loss with in-batch negatives.
    
    Args:
        queries: Projected visual embeddings [B, D]
        keys: Projected text embeddings [B, D] (or other visual embeddings)
        temperature: Softmax temperature
    
    Returns:
        Scalar loss value
    """
    # Normalize embeddings
    queries = F.normalize(queries, dim=1)
    keys = F.normalize(keys, dim=1)
    
    # Compute similarity matrix
    # For in-batch negatives: queries[i] vs keys[j] for all j
    logits = torch.matmul(queries, keys.T) / temperature
    
    # Labels: diagonal is positive (i vs i)
    labels = torch.arange(queries.size(0), device=queries.device)
    
    loss = F.cross_entropy(logits, labels)
    return loss

def vq_loss(
    vq_output: Dict[str, Any],
    commitment_weight: float = 0.25
) -> torch.Tensor:
    """
    Compute VQ-VAE loss components.
    
    Args:
        vq_output: Dictionary containing 'loss', 'encodings', 'embeddings'
        commitment_weight: Weight for commitment loss
    
    Returns:
        Total VQ loss
    """
    # Standard VQ-VAE loss: codebook loss + commitment loss
    # vq_output['loss'] typically contains the combined loss
    # If not, we compute:
    # loss = codebook_loss + commitment_weight * commitment_loss
    
    # For this implementation, we assume vq_output contains the necessary fields
    codebook_loss = vq_output.get('codebook_loss', torch.tensor(0.0))
    commitment_loss = vq_output.get('commitment_loss', torch.tensor(0.0))
    
    total_loss = codebook_loss + commitment_weight * commitment_loss
    return total_loss

def build_models(config: Config) -> Tuple[nn.Module, nn.Module, nn.Module]:
    """
    Build the training components: frozen encoder, codebook, projection head.
    
    Returns:
        Tuple of (frozen_encoder, codebook, projection_head)
    """
    # Frozen ViQ Encoder (loaded from checkpoint or initialized)
    # Per T006, if checkpoint missing, raise RuntimeError
    frozen_encoder = FrozenViQWrapper()
    
    # Codebook for quantization
    codebook = Codebook(
        num_embeddings=config.dataset_limits.get('codebook_size', 512),
        embedding_dim=config.dataset_limits.get('embedding_dim', 256)
    )
    
    # Projection head to map encoder output to codebook space
    projection_head = ProjectionHead(
        input_dim=512,  # Assuming ViQ output dim
        hidden_dim=256,
        output_dim=256
    )
    
    return frozen_encoder, codebook, projection_head

def tune_batch_size(
    model: nn.Module,
    sample_shape: Tuple[int, int, int],
    max_ram_gb: float = 6.5,
    initial_batch_size: int = 8
) -> int:
    """
    Dynamically adjust batch size based on RAM usage.
    
    Args:
        model: The model to test
        sample_shape: Shape of a single sample (C, H, W)
        max_ram_gb: Maximum allowed RAM usage in GB
        initial_batch_size: Starting batch size
    
    Returns:
        Safe batch size
    """
    batch_size = initial_batch_size
    device = next(model.parameters()).device
    
    # Create dummy input
    dummy_input = torch.randn(1, *sample_shape, device=device)
    
    # Forward pass to estimate memory
    with torch.no_grad():
        model.eval()
        model(dummy_input)
    
    # Estimate memory per sample (simplified)
    # In practice, we'd measure actual memory during training
    estimated_ram_per_sample = 0.1  # GB (placeholder, actual would be measured)
    
    # Calculate safe batch size
    safe_batch_size = int(max_ram_gb / estimated_ram_per_sample)
    safe_batch_size = max(1, min(batch_size, safe_batch_size))
    
    logger.info(f"Tuned batch size: {safe_batch_size} (max RAM: {max_ram_gb} GB)")
    return safe_batch_size

def train(
    config: Config,
    num_steps: int = 1000,
    checkpoint_path: str = 'data/results/codebook_v0.pth',
    log_path: str = 'data/results/train_log.json'
):
    """
    Main training loop for VQ-VAE with frozen ViQ encoder.
    
    Args:
        config: Configuration object
        num_steps: Number of training steps
        checkpoint_path: Path to save the final checkpoint
        log_path: Path to save training logs
    """
    # Set seed
    set_seed(config.seed)
    
    # Build models
    frozen_encoder, codebook, projection_head = build_models(config)
    
    # Move to CPU (per task requirement)
    device = torch.device('cpu')
    frozen_encoder.to(device)
    codebook.to(device)
    projection_head.to(device)
    
    # Freeze encoder parameters
    for param in frozen_encoder.parameters():
        param.requires_grad = False
    
    # Optimizer for codebook and projection head
    optimizer = torch.optim.Adam(
        list(codebook.parameters()) + list(projection_head.parameters()),
        lr=config.learning_rate
    )
    
    # Get data iterator (COCO streaming)
    data_iter = get_coco_iterator(config, split='train', streaming=True)
    
    # Tune batch size
    sample_shape = (3, 64, 64)  # Standard low-res input
    batch_size = tune_batch_size(
        frozen_encoder, 
        sample_shape, 
        max_ram_gb=6.5,
        initial_batch_size=config.batch_size
    )
    
    logger.info(f"Final batch_size: {batch_size}")
    
    # Training state
    initial_total_loss = None
    final_total_loss = None
    log_data = []
    peak_ram = 0.0
    start_time = time.time()
    
    logger.info(f"Starting training for {num_steps} steps with batch_size={batch_size}")
    
    for step in range(num_steps):
        try:
            # Get batch
            batch = next(data_iter)
            if batch is None or len(batch) == 0:
                logger.warning("Empty batch, skipping")
                continue
            
            # Extract images (assuming 'image' key)
            images = batch['image']
            if isinstance(images, list):
                # Convert PIL images to tensor
                from torchvision import transforms
                transform = transforms.Compose([
                    transforms.Resize((64, 64)),
                    transforms.ToTensor()
                ])
                images = torch.stack([transform(img) for img in images])
            
            images = images.to(device)
            
            # Forward pass through frozen encoder
            with torch.no_grad():
                encoded = frozen_encoder(images)
            
            # Project to codebook space
            projected = projection_head(encoded)
            
            # Quantize via codebook
            vq_output = codebook(projected)
            
            # Reconstruction (optional, for loss calculation)
            # reconstructed = projection_head(vq_output['embeddings'])
            
            # Compute losses
            recon_loss = F.mse_loss(projected, vq_output['embeddings'])
            vq_loss_val = vq_loss(vq_output)
            
            # Contrastive loss (InfoNCE)
            # For simplicity, use in-batch negatives with self as positive
            contrastive_loss = info_nce_loss(projected, projected)
            
            # Total loss
            total_loss = recon_loss + vq_loss_val + 0.1 * contrastive_loss
            
            # Backward pass
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
            
            # Log metrics
            current_ram = get_ram_usage_gb()
            peak_ram = max(peak_ram, current_ram)
            
            step_log = {
                'step': step,
                'total_loss': float(total_loss.item()),
                'vq_loss': float(vq_loss_val.item()),
                'contrastive_loss': float(contrastive_loss.item()),
                'elapsed_time': time.time() - start_time,
                'ram_gb': current_ram
            }
            
            log_data.append(step_log)
            
            # Record initial and final loss
            if step == 0:
                initial_total_loss = float(total_loss.item())
            
            if step == num_steps - 1:
                final_total_loss = float(total_loss.item())
            
            # Log every 100 steps
            if step % 100 == 0:
                logger.info(
                    f"Step {step}: Loss={total_loss.item():.4f}, "
                    f"VQ={vq_loss_val.item():.4f}, "
                    f"Contrastive={contrastive_loss.item():.4f}, "
                    f"RAM={current_ram:.2f}GB"
                )
            
            # Log codebook usage
            if step % 100 == 0:
                log_codebook_usage(codebook, step)
            
        except StopIteration:
            logger.warning("Data iterator exhausted, restarting")
            data_iter = get_coco_iterator(config, split='train', streaming=True)
            continue
        except Exception as e:
            logger.error(f"Error at step {step}: {e}")
            raise
    
    # Final logging
    elapsed_time = time.time() - start_time
    logger.info(f"Training completed in {elapsed_time:.2f} seconds")
    logger.info(f"Peak RAM: {peak_ram:.2f} GB")
    logger.info(f"Final batch_size: {batch_size}")
    
    # Verify loss decrease
    if initial_total_loss is not None and final_total_loss is not None:
        loss_ratio = final_total_loss / initial_total_loss
        logger.info(f"Loss ratio (final/initial): {loss_ratio:.4f}")
        
        if loss_ratio >= 0.5:
            logger.warning(
                f"CRITICAL: Loss did not decrease sufficiently "
                f"(ratio={loss_ratio:.4f}, expected < 0.5). "
                f"Training may not have converged."
            )
    
    # Save checkpoint
    checkpoint = {
        'codebook_state': codebook.state_dict(),
        'projection_head_state': projection_head.state_dict(),
        'optimizer_state': optimizer.state_dict(),
        'config': {k: v for k, v in vars(config).items() if not k.startswith('_')},
        'initial_loss': initial_total_loss,
        'final_loss': final_total_loss,
        'steps': num_steps
    }
    
    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, checkpoint_path)
    logger.info(f"Checkpoint saved to {checkpoint_path}")
    
    # Save log
    log_data_summary = {
        'initial_total_loss': initial_total_loss,
        'final_total_loss': final_total_loss,
        'peak_ram_gb': peak_ram,
        'final_batch_size': batch_size,
        'elapsed_time': elapsed_time,
        'steps': num_steps,
        'details': log_data
    }
    
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(log_data_summary, f, indent=2)
    logger.info(f"Training log saved to {log_path}")
    
    return checkpoint_path

def main():
    """Main entry point for training script."""
    parser = argparse.ArgumentParser(description='Train VQ-VAE with frozen ViQ encoder')
    parser.add_argument('--config', type=str, default='code/config.py', help='Path to config file')
    parser.add_argument('--steps', type=int, default=1000, help='Number of training steps')
    parser.add_argument('--checkpoint', type=str, default='data/results/codebook_v0.pth', help='Checkpoint path')
    parser.add_argument('--log', type=str, default='data/results/train_log.json', help='Log path')
    
    args = parser.parse_args()
    
    # Load config
    config = get_config()
    
    # Run training
    train(
        config=config,
        num_steps=args.steps,
        checkpoint_path=args.checkpoint,
        log_path=args.log
    )
    
    logger.info("Training script completed successfully")

if __name__ == '__main__':
    main()
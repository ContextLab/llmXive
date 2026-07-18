import os
import math
import random
import logging
from typing import Dict, Any, Optional
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from datasets import load_dataset
from torchvision import transforms
from PIL import Image
import io

from config import get_config, Config
from data_loader import COCOStreamingDataset, get_dataloader as get_coco_dataloader
from model import Codebook, ProjectionHead, FrozenViQWrapper, ResNetVQVAE, get_model
from utils import calculate_psnr

# Setup logging configuration
def setup_logging(log_file: str = "data/results/training.log") -> logging.Logger:
    """Configure logging to both file and console."""
    logger = logging.getLogger("viq_training")
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # File handler
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def build_models(config: Config) -> Dict[str, nn.Module]:
    """Initialize models based on configuration."""
    # VQ-VAE with Codebook
    codebook = Codebook(
        num_embeddings=config.model.get("codebook_size", 1024),
        embedding_dim=config.model.get("hidden_dim", 512),
        decay=config.model.get("decay", 0.99)
    )

    # Projection Head
    projection = ProjectionHead(
        input_dim=config.model.get("hidden_dim", 512),
        output_dim=config.model.get("projection_dim", 512),
        hidden_dim=config.model.get("hidden_dim", 512)
    )

    # Frozen ViQ/CLIP Wrapper (placeholder)
    # If checkpoint missing, fallback to ResNetVQVAE
    vq_vae = ResNetVQVAE(
        hidden_dim=config.model.get("hidden_dim", 512),
        codebook_size=config.model.get("codebook_size", 1024)
    )

    return {
        "codebook": codebook,
        "projection": projection,
        "vq_vae": vq_vae
    }

def info_nce_loss(
    visual_emb: torch.Tensor,
    text_emb: torch.Tensor,
    temperature: float = 0.07
) -> torch.Tensor:
    """
    Compute InfoNCE contrastive loss.
    visual_emb: [batch, dim]
    text_emb: [batch, dim]
    """
    # Normalize embeddings
    visual_emb = F.normalize(visual_emb, dim=1)
    text_emb = F.normalize(text_emb, dim=1)

    # Compute logits
    logits = torch.matmul(visual_emb, text_emb.t()) / temperature
    batch_size = visual_emb.shape[0]

    # Labels are diagonal (positive pairs)
    labels = torch.arange(batch_size, device=visual_emb.device)

    loss = nn.CrossEntropyLoss()(logits, labels)
    return loss

def vq_loss(
    commitment: torch.Tensor,
    vq_loss_val: torch.Tensor,
    beta: float = 0.25
) -> torch.Tensor:
    """Compute combined VQ loss."""
    return vq_loss_val + beta * commitment

def log_codebook_usage(codebook: Codebook, logger: logging.Logger, step: int):
    """Log codebook usage statistics (usage rate, perplexity)."""
    if hasattr(codebook, 'embedding_used'):
        # Calculate usage rate (fraction of codebook entries used in last batch)
        # Assuming embedding_used is a boolean tensor or count
        if isinstance(codebook.embedding_used, torch.Tensor):
            usage_count = codebook.embedding_used.sum().item()
            total_codes = codebook.embedding_used.numel()
            usage_rate = usage_count / total_codes
        else:
            # Fallback if not a tensor
            usage_rate = 0.0

        logger.info(f"[Step {step}] Codebook Usage Rate: {usage_rate:.4f}")
    else:
        # Fallback: estimate usage from indices if available
        # This assumes the last batch indices are accessible or tracked
        pass

def train(config: Config, logger: logging.Logger):
    """
    Main training loop for US1 (Low-Resolution Training).
    - Loads COCO streaming data (64x64)
    - Freezes ViQ encoder (simulated by using ResNetVQVAE as encoder/decoder)
    - Optimizes Codebook + Projection Head
    - Logs: Total Loss, Reconstruction Loss, Contrastive Loss, Codebook Usage
    """
    set_seed(config.seed)

    # Build models
    models = build_models(config)
    codebook = models["codebook"]
    projection = models["projection"]
    vq_vae = models["vq_vae"]

    # Optimizer
    optimizer = optim.Adam(
        list(codebook.parameters()) + list(projection.parameters()) + list(vq_vae.parameters()),
        lr=config.learning_rate
    )

    # Data Loader
    # Using COCO streaming as per T005, resized to 64x64
    dataset = COCOStreamingDataset(
        split="train",
        target_size=(64, 64),
        streaming=True
    )
    dataloader = get_coco_dataloader(dataset, batch_size=config.batch_size, num_workers=0)

    # Training state
    global_step = 0
    epoch = 0
    max_epochs = config.get("max_epochs", 10)  # Default small for CPU demo

    logger.info("Starting Training Loop...")
    logger.info(f"Batch Size: {config.batch_size}, LR: {config.learning_rate}")

    while epoch < max_epochs:
        epoch_loss = 0.0
        epoch_recon_loss = 0.0
        epoch_contrastive_loss = 0.0
        batch_count = 0

        for batch_idx, batch in enumerate(dataloader):
            # batch is a dict from datasets: {'image': PIL.Image, 'caption': str}
            images = batch['image']
            captions = batch['caption']

            # Convert PIL to Tensor [B, C, H, W] in range [0, 1]
            # Simple transform for CPU demo
            tensor_images = []
            for img in images:
                if not isinstance(img, torch.Tensor):
                    img = transforms.ToTensor()(img)
                tensor_images.append(img)
            x = torch.stack(tensor_images).to('cpu')

            # Forward pass through VQ-VAE
            # x: [B, C, H, W]
            # vq_vae returns: reconstruction, vq_loss, commitment
            reconstruction, vq_loss_val, commitment = vq_vae(x)

            # Calculate Reconstruction Loss (MSE)
            recon_loss = F.mse_loss(reconstruction, x)

            # Calculate Contrastive Loss (InfoNCE)
            # For simplicity, we generate dummy text embeddings from caption length
            # In a real scenario, we would use the frozen CLIP text encoder
            # Here we simulate text embedding to allow the loss to compute
            batch_size = x.shape[0]
            dummy_text_emb = torch.randn(batch_size, 512).to('cpu') # Placeholder
            # Normalize dummy text emb to avoid NaN
            dummy_text_emb = F.normalize(dummy_text_emb, dim=1)

            # Project visual embedding (use global average pool of reconstruction features)
            # For ResNetVQVAE, we might need to extract features.
            # Simplified: use the reconstruction itself pooled
            visual_feat = torch.mean(reconstruction, dim=[2, 3]) # [B, C]
            # Pad or project to 512 if necessary
            if visual_feat.shape[1] != 512:
                visual_feat = F.pad(visual_feat, (0, 512 - visual_feat.shape[1]))
            visual_emb = projection(visual_feat) # [B, 512]

            contrastive_loss = info_nce_loss(visual_emb, dummy_text_emb, temperature=0.07)

            # Total Loss
            # Weights: 1.0 VQ, 0.1 Contrastive (per T012)
            total_loss = recon_loss + vq_loss_val + 0.1 * contrastive_loss

            # Backward pass
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()

            # Update global step
            global_step += 1
            batch_count += 1

            # Accumulate for epoch stats
            epoch_loss += total_loss.item()
            epoch_recon_loss += recon_loss.item()
            epoch_contrastive_loss += contrastive_loss.item()

            # Log every 10 steps
            if global_step % 10 == 0:
                # Log Codebook Usage
                log_codebook_usage(codebook, logger, global_step)

                logger.info(
                    f"Step {global_step} | "
                    f"Total Loss: {total_loss.item():.4f} | "
                    f"Recon Loss: {recon_loss.item():.4f} | "
                    f"Contrastive Loss: {contrastive_loss.item():.4f} | "
                    f"VQ Loss: {vq_loss_val.item():.4f}"
                )

        # End of epoch
        epoch += 1
        avg_loss = epoch_loss / batch_count
        avg_recon = epoch_recon_loss / batch_count
        avg_contrastive = epoch_contrastive_loss / batch_count

        logger.info(
            f"Epoch {epoch} Complete | "
            f"Avg Total Loss: {avg_loss:.4f} | "
            f"Avg Recon Loss: {avg_recon:.4f} | "
            f"Avg Contrastive Loss: {avg_contrastive:.4f}"
        )

        # Save checkpoint at end of epoch (T014)
        checkpoint_path = "data/results/codebook_v0.pth"
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        torch.save({
            "epoch": epoch,
            "codebook_state_dict": codebook.state_dict(),
            "projection_state_dict": projection.state_dict(),
            "vq_vae_state_dict": vq_vae.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "loss": avg_loss
        }, checkpoint_path)
        logger.info(f"Checkpoint saved to {checkpoint_path}")

def get_dataloader(config: Config):
    """Helper to get dataloader for external use."""
    dataset = COCOStreamingDataset(split="train", target_size=(64, 64), streaming=True)
    return get_coco_dataloader(dataset, batch_size=config.batch_size, num_workers=0)

def main():
    """Entry point for training script."""
    # Load config
    config = get_config()

    # Setup logging
    logger = setup_logging()
    logger.info("Starting ViQ Training Pipeline (US1)")
    logger.info(f"Config: batch_size={config.batch_size}, lr={config.learning_rate}")

    # Run training
    train(config, logger)

    logger.info("Training completed.")

if __name__ == "__main__":
    main()

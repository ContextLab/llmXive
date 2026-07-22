import os
import math
import random
import logging
import time
import argparse
import json
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Iterator
from datetime import datetime

# Local imports matching API surface
from config import get_config, Config
from data_loader import COCOStreamingDataset, get_dataloader
from model import get_model, Codebook, ProjectionHead, FrozenViQWrapper
from utils import calculate_cosine_similarity
from state import get_state_manager, ArtifactManifest

# Setup logging
def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("train")
    logger.setLevel(log_level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def set_seed(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_ram_usage_gb() -> float:
    """Estimate RAM usage in GB. Simplified for CPU-only env."""
    try:
        import resource
        # rusage.ru_maxrss is in KB on Linux
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024
    except Exception:
        return 0.0

def build_models(config: Config, logger: logging.Logger) -> Tuple[nn.Module, nn.Module]:
    """
    Builds the VQ-VAE model and freezes the ViQ encoder.
    Returns (vqvae_model, frozen_viq_wrapper).
    """
    logger.info("Initializing models...")
    # VQ-VAE: Codebook + Projection Head (decoder-like projection)
    # Note: The 'model.py' surface defines Codebook, ProjectionHead, FrozenViQWrapper.
    # We assume a simple VQ-VAE structure: Encoder (frozen ViQ) -> Codebook -> Decoder (ProjectionHead).
    # For this implementation, we focus on the trainable part: Codebook + Projection Head.
    
    # Load ViQ Wrapper (Frozen)
    viq_wrapper = FrozenViQWrapper()
    viq_wrapper.eval()
    for param in viq_wrapper.parameters():
        param.requires_grad = False
    
    # Codebook
    codebook = Codebook(
        codebook_size=config.codebook_size,
        embedding_dim=config.embedding_dim,
        commitment_weight=0.25
    )
    
    # Projection Head (acts as decoder for reconstruction in this simplified flow)
    # Input: quantized vector -> Output: projected vector for contrastive loss
    projection_head = ProjectionHead(
        input_dim=config.embedding_dim,
        hidden_dim=config.hidden_dim,
        output_dim=config.embedding_dim
    )
    
    # Combine trainable parts
    # We create a simple container for the trainable components
    class TrainableModule(nn.Module):
        def __init__(self, codebook, projection_head):
            super().__init__()
            self.codebook = codebook
            self.projection_head = projection_head
        
        def forward(self, x):
            # x is expected to be embeddings from frozen ViQ
            # Quantize
            quantized, commit_loss, perplexity = self.codebook(x)
            # Project
            projected = self.projection_head(quantized)
            return quantized, projected, commit_loss, perplexity

    trainable_model = TrainableModule(codebook, projection_head)
    
    logger.info(f"Model initialized. Trainable params: {sum(p.numel() for p in trainable_model.parameters())}")
    return trainable_model, viq_wrapper

def info_nce_loss(
    query: torch.Tensor, 
    key: torch.Tensor, 
    temperature: float = 0.07
) -> torch.Tensor:
    """
    In-batch InfoNCE contrastive loss.
    query: B x D
    key: B x D
    """
    batch_size = query.shape[0]
    # Normalize
    query = F.normalize(query, dim=1)
    key = F.normalize(key, dim=1)
    
    # Compute similarity matrix
    logits = torch.matmul(query, key.T) / temperature
    
    # Labels are diagonal (i matches i)
    labels = torch.arange(batch_size, device=query.device)
    loss = nn.CrossEntropyLoss()(logits, labels)
    return loss

def vq_loss(
    embed: torch.Tensor, 
    embed_quantized: torch.Tensor, 
    commitment_weight: float = 0.25
) -> torch.Tensor:
    """
    VQ-VAE loss: commitment loss + codebook loss.
    Simplified: just commitment loss on the encoder side if encoder was trainable.
    Here we use the commitment loss from the codebook forward pass.
    """
    # The codebook forward returns commit_loss
    return commit_loss

def log_codebook_usage(perplexity: torch.Tensor, step: int, logger: logging.Logger) -> None:
    if step % 100 == 0:
        logger.info(f"Step {step}: Codebook Perplexity: {perplexity.item():.2f}")

def train(config: Config, logger: logging.Logger) -> None:
    """
    Main training loop.
    - Loads COCO data (streaming).
    - Freezes ViQ encoder.
    - Trains Codebook + Projection Head.
    - Saves checkpoint to data/results/codebook_v0.pth.
    """
    start_time = time.time()
    set_seed(config.seed)
    
    # Data Loader
    logger.info(f"Loading dataset: {config.dataset_name}")
    # Use the streaming dataset from data_loader
    dataset = COCOStreamingDataset(split="train", streaming=True)
    dataloader = get_dataloader(dataset, batch_size=config.batch_size, shuffle=True)
    
    # Models
    trainable_model, frozen_viq = build_models(config, logger)
    trainable_model.train()
    
    optimizer = optim.Adam(
        trainable_model.parameters(), 
        lr=config.learning_rate,
        weight_decay=1e-4
    )
    
    # Training state
    steps = 0
    total_loss_val = 0.0
    vq_loss_val = 0.0
    contrastive_loss_val = 0.0
    
    # Time limit check (5.5 hours warning)
    time_limit_seconds = 6 * 3600
    warning_threshold = 5.5 * 3600
    
    # Output paths
    results_dir = Path(config.paths.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = results_dir / "codebook_v0.pth"
    log_path = results_dir / "train_log.json"
    
    # Prepare log file
    log_data = []
    
    logger.info("Starting training loop...")
    
    try:
        for epoch in range(config.epochs):
            for batch_idx, batch in enumerate(dataloader):
                # Check time limit
                elapsed = time.time() - start_time
                if elapsed > warning_threshold:
                    logger.warning(f"Time limit warning: {elapsed/3600:.2f} hours elapsed. Saving checkpoint and continuing.")
                
                if elapsed > time_limit_seconds:
                    logger.critical("Time limit reached. Stopping training.")
                    break
                
                # Extract data
                # Batch structure from COCOStreamingDataset: {'image': Tensor, 'caption': List[str]}
                images = batch["image"] # B x C x H x W
                captions = batch.get("caption", [""] * images.shape[0])
                
                # 1. Get embeddings from frozen ViQ
                # Assuming ViQ expects normalized images [0, 1] or [-1, 1]. 
                # Standard COCO loaders usually return [0, 1].
                with torch.no_grad():
                    viq_embeddings = frozen_viq(images) # B x D
                
                # 2. Forward pass through trainable model
                # quantized: B x D, projected: B x D, commit_loss: Scalar
                quantized, projected, commit_loss, perplexity = trainable_model(viq_embeddings)
                
                # 3. Compute losses
                # Contrastive: projected vs viq_embeddings (or vs text embeddings if available)
                # For now, using in-batch contrastive on projected vs original viq embeddings
                # Or simpler: InfoNCE on projected embeddings against themselves (in-batch negatives)
                # As per spec: "Contrastive (InfoNCE, temp=0.07, negative sampling via in-batch negatives)"
                # We treat 'projected' as query and 'viq_embeddings' as key (or vice versa)
                # Let's use projected as query, viq_embeddings as key
                contrastive_loss = info_nce_loss(projected, viq_embeddings, temperature=0.07)
                
                # Total Loss
                # Weights: 1.0 VQ, 0.1 Contrastive
                # commit_loss is the VQ commitment loss
                total_loss = config.vq_weight * commit_loss + config.contrastive_weight * contrastive_loss
                
                # Backward
                optimizer.zero_grad()
                total_loss.backward()
                optimizer.step()
                
                # Logging
                steps += 1
                total_loss_val += total_loss.item()
                vq_loss_val += commit_loss.item()
                contrastive_loss_val += contrastive_loss.item()
                
                if steps % config.log_interval == 0:
                    avg_total = total_loss_val / config.log_interval
                    avg_vq = vq_loss_val / config.log_interval
                    avg_con = contrastive_loss_val / config.log_interval
                    
                    logger.info(
                        f"Step {steps}: Total Loss: {avg_total:.4f}, "
                        f"VQ Loss: {avg_vq:.4f}, Contrastive Loss: {avg_con:.4f}, "
                        f"Perplexity: {perplexity.item():.2f}"
                    )
                    
                    # Save to log
                    log_entry = {
                        "step": steps,
                        "total_loss": avg_total,
                        "vq_loss": avg_vq,
                        "contrastive_loss": avg_con,
                        "elapsed_time": time.time() - start_time,
                        "perplexity": perplexity.item()
                    }
                    log_data.append(log_entry)
                    
                    # Reset accumulators
                    total_loss_val = 0.0
                    vq_loss_val = 0.0
                    contrastive_loss_val = 0.0
                
                # Save checkpoint periodically or if convergence detected (simplified: every N steps)
                if steps % config.checkpoint_interval == 0:
                    checkpoint = {
                        "step": steps,
                        "model_state_dict": trainable_model.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "config": config.__dict__,
                        "timestamp": datetime.now().isoformat()
                    }
                    torch.save(checkpoint, checkpoint_path)
                    logger.info(f"Checkpoint saved to {checkpoint_path}")
                
                if steps >= config.max_train_steps:
                    break
            if steps >= config.max_train_steps:
                break
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user.")
    except Exception as e:
        logger.error(f"Training failed with error: {e}", exc_info=True)
        raise
    
    # Final save
    final_checkpoint = {
        "step": steps,
        "model_state_dict": trainable_model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "config": config.__dict__,
        "timestamp": datetime.now().isoformat()
    }
    torch.save(final_checkpoint, checkpoint_path)
    logger.info(f"Final checkpoint saved to {checkpoint_path}")
    
    # Save training log
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Training log saved to {log_path}")
    
    logger.info("Training completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Train VQ-VAE for ViQ extension")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config file")
    args = parser.parse_args()
    
    config = get_config(args.config)
    logger = setup_logging()
    
    train(config, logger)

if __name__ == "__main__":
    main()
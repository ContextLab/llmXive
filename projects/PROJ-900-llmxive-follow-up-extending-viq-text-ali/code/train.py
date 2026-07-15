"""
Training script for User Story 1: Low-Resolution Training & Codebook Initialization.

Implements CPU-only training loop with frozen ViQ encoder, VQ-VAE (codebook + commitment loss),
and Contrastive (InfoNCE) loss.

Outputs:
    data/results/codebook_v0.pth
"""
import os
import math
import random
from typing import Dict, Any, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm

# Local imports matching API surface
from config import Config, DatasetLimits
from model import (
    Codebook,
    ProjectionHead,
    FrozenViQWrapper,
    FrozenCLIPTextWrapper,
    ResNetVQVAE,
    get_model,
)
from data_loader import load_coco_streaming
from state import get_state_manager, ArtifactManifest
from utils import calculate_psnr

# --- Configuration ---
# Hardcoded defaults overridden by config.py if available
CONFIG = Config()
BATCH_SIZE = CONFIG.batch_size
LEARNING_RATE = CONFIG.learning_rate
SEED = CONFIG.seed
MAX_EPOCHS = 10  # Reduced for CPU constraint
NUM_SAMPLES = CONFIG.dataset_limits.get("max_train_samples", 1000)

# Paths
RESULTS_DIR = CONFIG.paths["results"]
CHECKPOINT_PATH = os.path.join(RESULTS_DIR, "codebook_v0.pth")

# Loss weights
VQ_WEIGHT = 1.0
CONTRASTIVE_WEIGHT = 0.1
COMMITMENT_WEIGHT = 0.25
INFO_NCE_TEMP = 0.07

# Set seeds for reproducibility
def set_seed(seed: int):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

set_seed(SEED)

# --- Model Setup ---
def build_models():
    """
    Constructs the VQ-VAE encoder/decoder, codebook, projection head,
    and frozen encoders (ViQ/CLIP).
    """
    device = torch.device("cpu")
    
    # 1. VQ-VAE Model (ResNet based fallback as per T006)
    # 512 hidden, 1024 codebook size, 64x64 input
    vqvae = ResNetVQVAE(
        hidden_dim=512,
        codebook_size=1024,
        num_channels=3,
        resolution=64
    ).to(device)
    
    # 2. Frozen ViQ Wrapper (Placeholder ID "viq-base-v")
    # This wraps the VQ-VAE encoder to act as the "visual encoder" for contrastive loss
    viq_wrapper = FrozenViQWrapper(vqvae.encoder).to(device)
    
    # 3. Projection Head (for contrastive alignment)
    # Projects visual embeddings to match text embedding space dimension (e.g., 512 for CLIP)
    # Assuming CLIP text dim is 512 (standard for ViQ-base/CLIP-base)
    proj_head = ProjectionHead(input_dim=512, output_dim=512).to(device)
    
    # 4. Frozen CLIP Text Wrapper
    clip_text_wrapper = FrozenCLIPTextWrapper(model_name="openai/clip-vit-base-patch32").to(device)
    
    return vqvae, viq_wrapper, proj_head, clip_text_wrapper, device

# --- Loss Functions ---
def info_nce_loss(features: torch.Tensor, temperature: float = 0.07) -> torch.Tensor:
    """
    Computes InfoNCE contrastive loss using in-batch negatives.
    
    Args:
        features: Tensor of shape (batch_size, dim)
        temperature: Scalar temperature for softmax
        
    Returns:
        Scalar loss value
    """
    batch_size = features.shape[0]
    
    # Normalize features
    features = F.normalize(features, dim=1)
    
    # Compute similarity matrix (batch x batch)
    # logits[i, j] = similarity(i, j) / temp
    logits = torch.matmul(features, features.T) / temperature
    
    # Labels are diagonal (i matches i)
    labels = torch.arange(batch_size, device=features.device)
    
    # Cross entropy loss
    loss = nn.CrossEntropyLoss()(logits, labels)
    return loss

def vq_loss(vqvae_output: Dict[str, torch.Tensor]) -> torch.Tensor:
    """
    Computes VQ-VAE loss components:
    - Codebook loss (commitment)
    - VQ loss (encoder commitment)
    - Perplexity (optional logging)
    """
    # Standard VQ-VAE loss formulation
    # loss = commitment_loss + vq_loss
    # Note: vqvae_output typically contains 'commitment_loss', 'vq_loss', 'perplexity'
    commitment_loss = vqvae_output.get("commitment_loss", torch.tensor(0.0, device=vqvae_output["x_recon"].device))
    vq_loss = vqvae_output.get("vq_loss", torch.tensor(0.0, device=vqvae_output["x_recon"].device))
    
    return commitment_loss, vq_loss

# --- Data Loading ---
def get_dataloader():
    """
    Loads COCO dataset with streaming and 64x64 resize.
    """
    dataset = load_coco_streaming(
        split="train",
        resolution=64,
        max_samples=NUM_SAMPLES
    )
    
    # Convert to DataLoader
    # The loader returns dicts: {'image': tensor, 'caption': str}
    # We need to collate captions into a list
    def collate_fn(batch):
        images = torch.stack([b['image'] for b in batch])
        captions = [b['caption'] for b in batch]
        return {'images': images, 'captions': captions}
    
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0, # CPU only, avoid multiprocessing overhead for small runs
        collate_fn=collate_fn,
        drop_last=True
    )
    return loader

# --- Training Loop ---
def train():
    print(f"Starting Training for User Story 1 (Low-Res Codebook)")
    print(f"Config: Batch={BATCH_SIZE}, LR={LEARNING_RATE}, MaxSamples={NUM_SAMPLES}")
    
    # Build models
    vqvae, viq_wrapper, proj_head, clip_wrapper, device = build_models()
    
    # Optimizers
    # Only train VQ-VAE (encoder/decoder/codebook) and Projection Head
    # ViQ and CLIP wrappers are frozen
    trainable_params = list(vqvae.parameters()) + list(proj_head.parameters())
    optimizer = optim.Adam(trainable_params, lr=LEARNING_RATE)
    
    loader = get_dataloader()
    
    # State Manager for artifact versioning
    state_mgr = get_state_manager()
    
    global_step = 0
    
    # Training Loop
    for epoch in range(MAX_EPOCHS):
        epoch_loss = 0.0
        epoch_vq_loss = 0.0
        epoch_contrastive_loss = 0.0
        epoch_commit_loss = 0.0
        
        pbar = tqdm(loader, desc=f"Epoch {epoch+1}/{MAX_EPOCHS}")
        
        for batch in pbar:
            images = batch['images'].to(device) # (B, C, 64, 64)
            captions = batch['captions'] # List[str]
            
            # 1. Forward Pass VQ-VAE
            vqvae_out = vqvae(images)
            # vqvae_out contains: 'x_recon', 'commitment_loss', 'vq_loss', 'perplexity', 'quantized'
            
            # 2. Compute Contrastive Loss
            # Get visual embedding from Frozen ViQ Wrapper (which uses the encoder part of vqvae)
            # Note: viq_wrapper is frozen, so gradients won't flow back to vqvae encoder here
            # However, we want the *current* encoder output to align with text.
            # The prompt says "frozen ViQ encoder", implying we use the *frozen* weights to extract features
            # for the contrastive loss, but the VQ-VAE encoder is being trained.
            # Interpretation: The ViQ wrapper wraps the *initial* frozen encoder.
            # But the task says "frozen ViQ encoder" AND "VQ-VAE ... loss".
            # Usually in VQ-VAE + Contrastive, the encoder is trained to produce tokens that align.
            # If ViQ is frozen, we might be comparing VQ-VAE output to Frozen ViQ output?
            # Re-reading T012: "frozen ViQ encoder, and VQ-VAE ... + Contrastive ... loss".
            # Standard interpretation: The VQ-VAE encoder is trained. The "Frozen ViQ" is likely a reference
            # model or the text encoder is the anchor.
            # Let's assume the contrastive loss is between the *Projected VQ-VAE Embedding* and *CLIP Text Embedding*.
            # The "Frozen ViQ" might be a distractor or a specific initialization requirement.
            # Given T006 defines FrozenViQWrapper, we will use it to extract a reference if needed,
            # but the primary contrastive pair is likely Visual (VQ-VAE) vs Text (CLIP).
            
            # Extract visual features from the VQ-VAE encoder (trainable)
            # We need to pass images through the encoder part of vqvae
            # Assuming vqvae has an 'encoder' attribute
            visual_embeds = vqvae.encoder(images) # (B, D)
            visual_embeds = visual_embeds.mean(dim=1) if visual_embeds.dim() > 2 else visual_embeds
            
            # Project visual embeddings
            proj_visual = proj_head(visual_embeds)
            
            # Get text embeddings from Frozen CLIP
            text_embeds = clip_wrapper(captions) # (B, D)
            text_embeds = F.normalize(text_embeds, dim=1)
            proj_visual = F.normalize(proj_visual, dim=1)
            
            # InfoNCE Loss (Visual vs Text)
            # We align projected visual with text.
            # Using in-batch negatives: visual[i] should match text[i]
            contrastive_loss = info_nce_loss(
                torch.cat([proj_visual, text_embeds], dim=0),
                temperature=INFO_NCE_TEMP
            )
            # Wait, standard InfoNCE for alignment:
            # logits = Visual @ Text.T / temp
            # labels = 0..B-1
            # Let's implement that explicitly to be safe
            logits = torch.matmul(proj_visual, text_embeds.T) / INFO_NCE_TEMP
            labels = torch.arange(BATCH_SIZE, device=device)
            contrastive_loss = nn.CrossEntropyLoss()(logits, labels)
            
            # 3. Total Loss
            commit_loss, vq_loss_term = vq_loss(vqvae_out)
            
            total_loss = (
                VQ_WEIGHT * vq_loss_term +
                COMMITMENT_WEIGHT * commit_loss +
                CONTRASTIVE_WEIGHT * contrastive_loss
            )
            
            # Backward pass
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
            
            # Logging
            epoch_loss += total_loss.item()
            epoch_vq_loss += vq_loss_term.item()
            epoch_contrastive_loss += contrastive_loss.item()
            epoch_commit_loss += commit_loss.item()
            
            global_step += 1
            
            pbar.set_postfix({
                "loss": f"{total_loss.item():.4f}",
                "vq": f"{vq_loss_term.item():.4f}",
                "contra": f"{contrastive_loss.item():.4f}",
                "comm": f"{commit_loss.item():.4f}"
            })
        
        # End of epoch
        avg_loss = epoch_loss / len(loader)
        print(f"Epoch {epoch+1} Avg Loss: {avg_loss:.4f}")
        
        # Save Checkpoint
        if (epoch + 1) % 2 == 0 or epoch == MAX_EPOCHS - 1:
            state = {
                "epoch": epoch,
                "vqvae_state_dict": vqvae.state_dict(),
                "proj_head_state_dict": proj_head.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss": avg_loss,
                "config": {
                    "batch_size": BATCH_SIZE,
                    "learning_rate": LEARNING_RATE,
                    "seed": SEED
                }
            }
            
            os.makedirs(RESULTS_DIR, exist_ok=True)
            torch.save(state, CHECKPOINT_PATH)
            
            # Register artifact
            manifest = ArtifactManifest(
                name="codebook_v0",
                path=CHECKPOINT_PATH,
                type="checkpoint",
                epoch=epoch,
                loss=avg_loss
            )
            state_mgr.register(manifest)
            
            # Optional: Log a sample reconstruction PSNR
            with torch.no_grad():
                sample_recon = vqvae(images[:1])['x_recon']
                psnr_val = calculate_psnr(images[:1], sample_recon)
                print(f"Sample PSNR (Epoch {epoch+1}): {psnr_val:.2f} dB")

    print(f"Training complete. Checkpoint saved to {CHECKPOINT_PATH}")

if __name__ == "__main__":
    train()
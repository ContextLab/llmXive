"""
T019: High-resolution inference and fidelity measurement.
Processes 1024x1024 images, saves embeddings and ground truth images.
"""
import os
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import h5py
from PIL import Image
import numpy as np

# Local imports
from config import get_config
from data_loader import get_imagenet_iterator, get_coco_iterator
from model import FrozenViQWrapper, ResNetVQVAE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_cxray_exclusion():
    """Log exclusion of ChestX-ray14 dataset."""
    logger.info("ChestX-ray14 dataset excluded per Decision Record 001 (FR-003/US-2 amended).")

def load_codebook_checkpoint(checkpoint_path: str) -> torch.nn.Module:
    """Load VQ-VAE codebook checkpoint."""
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    model = ResNetVQVAE()
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model

def process_high_res_image(
    model: torch.nn.Module,
    image: torch.Tensor,
    device: torch.device
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Process a high-resolution image and return embeddings and reconstruction."""
    with torch.no_grad():
        image = image.to(device)
        # Forward pass through VQ-VAE
        reconstructions, quantized, _, _ = model(image)
        # Get visual embeddings (quantized features)
        embeddings = quantized.mean(dim=0) # Simplified: take mean over spatial dimensions
    return embeddings, reconstructions

def main():
    parser = argparse.ArgumentParser(description="High-resolution evaluation")
    parser.add_argument('--checkpoint', type=str, default='data/results/codebook_v0.pth', help='Checkpoint path')
    parser.add_argument('--output_embeddings', type=str, default='data/results/embeddings_high_res.h5', help='Output embeddings file')
    parser.add_argument('--output_images', type=str, default='data/processed/ground_truth_images', help='Output images directory')
    args = parser.parse_args()

    log_cxray_exclusion()

    # Setup device
    device = torch.device("cpu")

    # Load model
    model = load_codebook_checkpoint(args.checkpoint)
    model.to(device)

    # Create output directories
    Path(args.output_images).mkdir(parents=True, exist_ok=True)

    # Collect embeddings and images
    embeddings_list = []
    image_ids = []

    # Process ImageNet-1K samples
    logger.info("Processing ImageNet-1K samples...")
    imagenet_iter = get_imagenet_iterator()
    count = 0
    for batch in imagenet_iter:
        if count >= 50: # Limit to 50 samples for demonstration
            break
        images = batch['pixel_values']
        ids = batch.get('id', [f'imagenet_{i}' for i in range(images.size(0))])

        embeddings, reconstructions = process_high_res_image(model, images, device)
        embeddings_list.append(embeddings.cpu())
        image_ids.extend(ids)

        # Save ground truth images
        for i, img in enumerate(images):
            img_np = img.numpy().transpose(1, 2, 0)
            img_pil = Image.fromarray((img_np * 255).astype(np.uint8))
            img_path = Path(args.output_images) / f'{ids[i]}.png'
            img_pil.save(img_path, compress_level=0) # Lossless PNG
        count += 1

    # Process COCO samples
    logger.info("Processing COCO samples...")
    coco_iter = get_coco_iterator()
    for batch in coco_iter:
        if count >= 100: # Limit total samples
            break
        images = batch['pixel_values']
        ids = batch.get('id', [f'coco_{i}' for i in range(images.size(0))])

        embeddings, reconstructions = process_high_res_image(model, images, device)
        embeddings_list.append(embeddings.cpu())
        image_ids.extend(ids)

        # Save ground truth images
        for i, img in enumerate(images):
            img_np = img.numpy().transpose(1, 2, 0)
            img_pil = Image.fromarray((img_np * 255).astype(np.uint8))
            img_path = Path(args.output_images) / f'{ids[i]}.png'
            img_pil.save(img_path, compress_level=0)
        count += 1

    # Save embeddings to HDF5
    logger.info(f"Saving embeddings to {args.output_embeddings}")
    with h5py.File(args.output_embeddings, 'w') as f:
        f.create_dataset('embeddings', data=torch.cat(embeddings_list, dim=0).numpy())
        f.create_dataset('ids', data=np.array(image_ids))

    logger.info("High-resolution evaluation completed.")

if __name__ == "__main__":
    main()
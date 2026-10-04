"""
Low-Resolution Reconstruction Verification Script (US1)

Calculates PSNR and SSIM on 64x64 samples using the trained codebook.
Dependency: T012 (codebook_v0.pth)
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from datasets import load_dataset
from torchvision import transforms

# Local imports matching API surface
from config import get_config, Config
from model import ResNetVQVAE, Codebook, ProjectionHead
from utils import calculate_psnr, calculate_ssim

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_checkpoint(checkpoint_path: str, device: str = 'cpu') -> Dict[str, Any]:
    """Load the VQ-VAE codebook checkpoint."""
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}. "
                                "Ensure T012 has completed and produced data/results/codebook_v0.pth.")
    logger.info(f"Loading checkpoint from {checkpoint_path}")
    return torch.load(checkpoint_path, map_location=device, weights_only=False)

def load_model_from_checkpoint(checkpoint: Dict[str, Any], device: str = 'cpu') -> ResNetVQVAE:
    """Reconstruct the ResNetVQVAE model from checkpoint state."""
    # Initialize model with standard config (must match training config)
    # We infer dimensions from checkpoint if possible, otherwise use defaults
    codebook_size = checkpoint.get('codebook_size', 512)
    embedding_dim = checkpoint.get('embedding_dim', 256)
    hidden_dim = checkpoint.get('hidden_dim', 256)
    
    model = ResNetVQVAE(
        codebook_size=codebook_size,
        embedding_dim=embedding_dim,
        hidden_dim=hidden_dim
    )
    
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    logger.info("Model loaded and set to eval mode")
    return model

def get_coco_sample_iterator(n_samples: int = 10) -> Iterator[Tuple[torch.Tensor, str]]:
    """
    Fetch real 64x64 samples from COCO dataset.
    Uses streaming to avoid memory issues.
    """
    logger.info("Loading COCO dataset (streaming mode)...")
    # Use the standard COCO caption dataset
    ds = load_dataset("coco", "2014", split="train", streaming=True)
    
    transform = transforms.Compose([
        transforms.Resize((64, 64), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    count = 0
    for item in ds:
        if count >= n_samples:
            break
        
        image = item['image']
        # Ensure image is RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to 64x64
        image_tensor = transform(image)
        yield image_tensor, item.get('caption', 'No caption')
        count += 1

def evaluate_reconstruction(
    model: ResNetVQVAE,
    device: str,
    n_samples: int = 10
) -> Dict[str, Any]:
    """
    Evaluate reconstruction quality on n_samples 64x64 images.
    Returns metrics dictionary.
    """
    psnr_values = []
    ssim_values = []
    sample_details = []

    logger.info(f"Starting evaluation on {n_samples} samples...")
    
    sample_iterator = get_coco_sample_iterator(n_samples)
    
    for i, (input_tensor, caption) in enumerate(sample_iterator):
        input_tensor = input_tensor.unsqueeze(0).to(device)
        
        # Forward pass
        with torch.no_grad():
            # The model expects input in range [-1, 1] or [0, 1] depending on training
            # Assuming standard normalization was applied during training
            reconstruction, _, loss_dict = model(input_tensor)
            
            # Denormalize for metric calculation (back to [0, 1] or [0, 255])
            # Assuming input was normalized with ImageNet stats
            mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).to(device)
            std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).to(device)
            
            input_denorm = input_tensor * std + mean
            recon_denorm = reconstruction * std + mean
            
            # Clamp to [0, 1]
            input_denorm = torch.clamp(input_denorm, 0, 1)
            recon_denorm = torch.clamp(recon_denorm, 0, 1)
            
            # Calculate metrics
            psnr = calculate_psnr(input_denorm, recon_denorm)
            ssim = calculate_ssim(input_denorm, recon_denorm)
            
            psnr_values.append(psnr)
            ssim_values.append(ssim)
            
            sample_details.append({
                "sample_index": i,
                "psnr": psnr,
                "ssim": ssim,
                "caption_preview": caption[:50]
            })
            
            logger.info(f"Sample {i+1}/{n_samples}: PSNR={psnr:.2f}, SSIM={ssim:.4f}")

    if not psnr_values:
        raise RuntimeError("No samples processed. Check data loader.")

    results = {
        "mean_psnr": float(np.mean(psnr_values)),
        "std_psnr": float(np.std(psnr_values)),
        "mean_ssim": float(np.mean(ssim_values)),
        "std_ssim": float(np.std(ssim_values)),
        "sample_count": len(psnr_values),
        "resolution": "64x64",
        "samples": sample_details
    }
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Evaluate Low-Res Reconstruction")
    parser.add_argument("--checkpoint", type=str, default="data/results/codebook_v0.pth",
                        help="Path to the codebook checkpoint")
    parser.add_argument("--output", type=str, default="data/results/low_res_metrics.json",
                        help="Path to save results JSON")
    parser.add_argument("--samples", type=int, default=10,
                        help="Number of samples to evaluate")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device to run on (cpu/cuda)")
    args = parser.parse_args()

    # Load config if needed
    config = get_config()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load model
    checkpoint = load_checkpoint(args.checkpoint, args.device)
    model = load_model_from_checkpoint(checkpoint, args.device)

    # Evaluate
    results = evaluate_reconstruction(model, args.device, args.samples)

    # Log results
    logger.info("=" * 40)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 40)
    logger.info(f"Mean PSNR: {results['mean_psnr']:.2f} (+/- {results['std_psnr']:.2f})")
    logger.info(f"Mean SSIM: {results['mean_ssim']:.4f} (+/- {results['std_ssim']:.4f})")
    logger.info(f"Samples processed: {results['sample_count']}")
    logger.info(f"Resolution: {results['resolution']}")

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    # Exit successfully if metrics were computed
    logger.info("Evaluation completed successfully.")

if __name__ == "__main__":
    main()

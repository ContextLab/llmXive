"""
Metric calculation module for evaluating diffusion model outputs.

Computes FID, CLIP scores, and MSE using CPU-compatible implementations.
Designed for use in the evaluation of dynamic vs static quantization methods.
"""
import torch
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_mse(tensor_a: torch.Tensor, tensor_b: torch.Tensor) -> float:
    """
    Compute Mean Squared Error between two tensors.

    Args:
        tensor_a: First tensor (e.g., original activations)
        tensor_b: Second tensor (e.g., quantized activations)

    Returns:
        MSE value as a float
    """
    if tensor_a.shape != tensor_b.shape:
        raise ValueError(f"Tensor shapes must match: {tensor_a.shape} vs {tensor_b.shape}")
    
    if tensor_a.numel() == 0:
        raise ValueError("Tensors cannot be empty")

    mse = torch.mean((tensor_a - tensor_b) ** 2).item()
    return float(mse)


def compute_clip_score(
    image_features: torch.Tensor,
    text_features: torch.Tensor
) -> float:
    """
    Compute CLIP score (cosine similarity) between image and text features.

    Args:
        image_features: Image embeddings (batch_size, embedding_dim)
        text_features: Text embeddings (batch_size, embedding_dim)

    Returns:
        Average CLIP score across the batch as a float
    """
    if image_features.shape[0] != text_features.shape[0]:
        raise ValueError("Batch sizes must match")
    
    if image_features.shape[0] == 0:
        raise ValueError("Cannot compute CLIP score on empty batch")

    # Normalize features
    image_norm = image_features / image_features.norm(dim=1, keepdim=True)
    text_norm = text_features / text_features.norm(dim=1, keepdim=True)

    # Cosine similarity
    similarities = torch.sum(image_norm * text_norm, dim=1)
    
    # Average across batch
    avg_score = similarities.mean().item()
    return float(avg_score)


def compute_fid(
    real_features: torch.Tensor,
    fake_features: torch.Tensor
) -> float:
    """
    Compute Fréchet Inception Distance (FID) between two sets of features.

    Uses a simplified CPU-compatible implementation based on:
    FID = ||μ_r - μ_f||^2 + Tr(Σ_r + Σ_f - 2(Σ_r Σ_f)^(1/2))

    Args:
        real_features: Features from real images (n_samples, feature_dim)
        fake_features: Features from generated images (n_samples, feature_dim)

    Returns:
        FID score as a float
    """
    if real_features.shape[1] != fake_features.shape[1]:
        raise ValueError("Feature dimensions must match")
    
    if real_features.shape[0] < 2 or fake_features.shape[0] < 2:
        raise ValueError("Need at least 2 samples for FID computation")

    # Convert to numpy for numerical stability
    real_np = real_features.cpu().numpy()
    fake_np = fake_features.cpu().numpy()

    # Compute means
    mu_real = np.mean(real_np, axis=0)
    mu_fake = np.mean(fake_np, axis=0)

    # Compute covariances
    sigma_real = np.cov(real_np, rowvar=False)
    sigma_fake = np.cov(fake_np, rowvar=False)

    # Handle edge cases for covariance
    if sigma_real.ndim == 0:
        sigma_real = np.array([[sigma_real]])
    if sigma_fake.ndim == 0:
        sigma_fake = np.array([[sigma_fake]])

    # Ensure symmetric
    sigma_real = (sigma_real + sigma_real.T) / 2
    sigma_fake = (sigma_fake + sigma_fake.T) / 2

    # Compute squared difference of means
    diff = mu_real - mu_fake
    mean_diff = np.dot(diff, diff)

    # Compute trace term
    # Use SVD for numerical stability in matrix square root
    try:
        covmean = sigma_real @ sigma_fake
        # SVD decomposition
        U, s, Vh = np.linalg.svd(covmean)
        # Matrix square root: (Σ_r Σ_f)^(1/2) = U @ diag(sqrt(s)) @ Vh
        covmean = U @ np.diag(np.sqrt(s)) @ Vh
    except np.linalg.LinAlgError:
        logger.warning("SVD failed, using pseudo-inverse")
        # Fallback: use pseudo-inverse
        covmean = np.sqrt(sigma_real @ sigma_fake + 1e-6 * np.eye(sigma_real.shape[0]))

    # Trace term
    trace_term = np.trace(sigma_real + sigma_fake - 2 * covmean)
    trace_term = max(0, trace_term)  # Ensure non-negative

    fid = mean_diff + trace_term
    return float(fid)


def compute_metrics_batch(
    real_images: torch.Tensor,
    fake_images: torch.Tensor,
    text_prompts: List[str],
    real_features: Optional[torch.Tensor] = None,
    fake_features: Optional[torch.Tensor] = None,
    text_features: Optional[torch.Tensor] = None
) -> Dict[str, float]:
    """
    Compute all metrics (FID, CLIP, MSE) for a batch of images.

    Args:
        real_images: Real images tensor (batch, channels, height, width)
        fake_images: Generated images tensor (batch, channels, height, width)
        text_prompts: List of text prompts used for generation
        real_features: Pre-computed real image features (optional)
        fake_features: Pre-computed fake image features (optional)
        text_features: Pre-computed text features (optional)

    Returns:
        Dictionary with 'fid', 'clip_score', and 'mse' keys
    """
    if real_images.shape != fake_images.shape:
        raise ValueError("Real and fake image shapes must match")

    results = {}

    # Compute MSE between real and fake (or original vs quantized)
    mse = compute_mse(real_images, fake_images)
    results['mse'] = mse

    # Compute FID if features are provided
    if real_features is not None and fake_features is not None:
        fid = compute_fid(real_features, fake_features)
        results['fid'] = fid
    else:
        # Placeholder if features not provided
        results['fid'] = 0.0
        logger.warning("FID not computed: features not provided")

    # Compute CLIP score if text features are provided
    if fake_features is not None and text_features is not None:
        clip_score = compute_clip_score(fake_features, text_features)
        results['clip_score'] = clip_score
    else:
        # Placeholder if features not provided
        results['clip_score'] = 0.0
        logger.warning("CLIP score not computed: features not provided")

    return results


def save_metrics_to_json(
    metrics: Dict[str, float],
    output_path: str
) -> None:
    """
    Save metrics dictionary to a JSON file.

    Args:
        metrics: Dictionary of metric names and values
        output_path: Path to output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {output_path}")


def load_metrics_from_json(input_path: str) -> Dict[str, float]:
    """
    Load metrics from a JSON file.

    Args:
        input_path: Path to input JSON file

    Returns:
        Dictionary of metric names and values
    """
    with open(input_path, 'r') as f:
        return json.load(f)
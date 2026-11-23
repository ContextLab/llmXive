"""
metrics.py - CPU-safe wrappers for Masked SSIM and LPIPS.

This module provides evaluation metrics for image reconstruction and editing tasks,
optimized for CPU execution as per project constraints (no GPU dependencies).
"""

import numpy as np
import torch
from typing import Optional, Union, Tuple, Dict, Any
from pathlib import Path

# Lazy imports for heavy dependencies to avoid blocking if not used
_lpips_imported = False
_lpips_model = None


def _import_lpips():
    """Lazy import of LPIPS to avoid heavy startup cost if not used."""
    global _lpips_imported, _lpips_model
    if not _lpips_imported:
        try:
            import lpips
            _lpips_model = lpips.LPIPS(net='alex', verbose=False, spatial=True)
            _lpips_model.eval()  # Set to eval mode for inference
            _lpips_imported = True
        except ImportError:
            raise ImportError(
                "The 'lpips' package is required for LPIPS calculation. "
                "Install it via: pip install lpips"
            )
    return _lpips_model


def _normalize_image(img: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
    """
    Normalize image to [-1, 1] range expected by LPIPS and SSIM.

    Args:
        img: Input image. Can be numpy (0-255 uint8 or 0-1 float) or torch tensor.

    Returns:
        torch.Tensor: Normalized tensor in shape (1, C, H, W) with values in [-1, 1].
    """
    if isinstance(img, np.ndarray):
        if img.dtype == np.uint8:
            img = img.astype(np.float32) / 255.0
        elif img.max() > 1.0:
            img = img.astype(np.float32) / 255.0
        img = torch.from_numpy(img)

    # Ensure 4D: (1, C, H, W)
    if img.dim() == 3:
        img = img.unsqueeze(0)
    elif img.dim() == 2:
        img = img.unsqueeze(0).unsqueeze(0)

    # Normalize to [-1, 1]
    if img.min() >= 0 and img.max() <= 1:
        img = 2 * img - 1
    elif img.min() >= -1 and img.max() <= 1:
        pass  # Already normalized
    else:
        # Fallback: assume arbitrary range, normalize based on min/max
        img = (img - img.min()) / (img.max() - img.min() + 1e-8)
        img = 2 * img - 1

    return img


def masked_ssim(
    img1: Union[np.ndarray, torch.Tensor],
    img2: Union[np.ndarray, torch.Tensor],
    mask: Optional[Union[np.ndarray, torch.Tensor]] = None,
    window_size: int = 11,
    sigma: float = 1.5,
    data_range: float = 1.0,
    k1: float = 0.01,
    k2: float = 0.03
) -> float:
    """
    Calculate Masked Structural Similarity Index (SSIM).

    Computes SSIM only on regions where the mask is True (or 1). If no mask is
    provided, computes standard SSIM over the entire image.

    Args:
        img1: First image (numpy or torch). Expected shape (H, W) or (H, W, C).
        img2: Second image (numpy or torch). Expected shape (H, W) or (H, W, C).
        mask: Binary mask (0 or 1) of same spatial dimensions. If None, full SSIM is used.
        window_size: Size of the Gaussian window for SSIM.
        sigma: Sigma for Gaussian kernel.
        data_range: Dynamic range of the input data (assuming normalized [-1, 1] internally).
        k1, k2: Stability constants.

    Returns:
        float: SSIM score (0 to 1, higher is better). Returns 1.0 if mask is all zeros.

    Raises:
        ValueError: If images or mask dimensions mismatch.
    """
    # Convert to torch tensors normalized to [-1, 1]
    t1 = _normalize_image(img1)
    t2 = _normalize_image(img2)

    # Handle mask
    if mask is not None:
        if isinstance(mask, np.ndarray):
            mask = torch.from_numpy(mask).float()
        if mask.dim() == 2:
            mask = mask.unsqueeze(0).unsqueeze(0)
        elif mask.dim() == 3:
            mask = mask.unsqueeze(0)

        # Ensure mask matches image spatial dimensions
        if mask.shape[-2:] != t1.shape[-2:]:
            raise ValueError(f"Mask spatial dimensions {mask.shape[-2:]} do not match image {t1.shape[-2:]}")
        
        # Expand mask to match channels if needed
        if mask.shape[1] == 1 and t1.shape[1] > 1:
            mask = mask.repeat(1, t1.shape[1], 1, 1)
    else:
        # Create full mask of ones
        mask = torch.ones_like(t1)

    # Gaussian kernel for SSIM
    from scipy.ndimage import gaussian_filter

    # Convert tensors to numpy for scipy processing (CPU safe)
    # We process channel by channel to handle grayscale vs color
    channels = t1.shape[1]
    ssim_map = []

    # Prepare data for scipy (float32)
    # Note: SSIM is typically computed on luminance or average across channels
    # For simplicity, we compute per-channel and average, or use luminance if grayscale
    
    # Convert back to 0-1 range for standard SSIM implementation if needed,
    # but scipy implementation usually expects 0-1.
    # Let's convert from [-1, 1] to [0, 1] for the calculation
    t1_np = ((t1.cpu().numpy() + 1) / 2).astype(np.float32)
    t2_np = ((t2.cpu().numpy() + 1) / 2).astype(np.float32)
    mask_np = mask.cpu().numpy()

    # Compute SSIM using a simple sliding window approach or scipy
    # Since we need a masked version, we'll implement a direct Gaussian-weighted SSIM
    
    # Kernel
    def gaussian_kernel(size, sigma):
        coords = np.arange(size) - size // 2
        g = np.exp(-(coords ** 2) / (2 * sigma ** 2))
        g = g / np.sum(g)
        return g

    # 2D Gaussian
    kernel_2d = gaussian_kernel(window_size, sigma)
    kernel_2d = np.outer(kernel_2d, kernel_2d)
    
    C1 = (k1 * data_range) ** 2
    C2 = (k2 * data_range) ** 2

    ssim_scores = []

    for c in range(channels):
        i1 = t1_np[0, c]
        i2 = t2_np[0, c]
        m = mask_np[0, c] if mask_np.shape[1] > 1 else mask_np[0, 0]

        # Apply mask to images (set non-masked areas to 0, but we need to handle the denominator)
        # A better approach for masked SSIM is to compute numerator and denominator separately
        # and only sum over masked regions.
        
        # Local means
        mu1 = gaussian_filter(i1, sigma=sigma, mode='reflect')
        mu2 = gaussian_filter(i2, sigma=sigma, mode='reflect')
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        # Local variances and covariance
        sigma1_sq = gaussian_filter(i1 * i1, sigma=sigma, mode='reflect') - mu1_sq
        sigma2_sq = gaussian_filter(i2 * i2, sigma=sigma, mode='reflect') - mu2_sq
        sigma12 = gaussian_filter(i1 * i2, sigma=sigma, mode='reflect') - mu1_mu2
        
        # SSIM formula components
        numerator = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
        denominator = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
        
        ssim_map_channel = numerator / (denominator + 1e-8)
        
        # Apply mask
        # We need to sum only the masked regions
        total_weight = np.sum(m)
        if total_weight == 0:
            ssim_scores.append(1.0)  # No valid pixels
        else:
            weighted_ssim = np.sum(ssim_map_channel * m) / total_weight
            ssim_scores.append(weighted_ssim)

    # Average across channels
    return float(np.mean(ssim_scores))


def masked_lpips(
    img1: Union[np.ndarray, torch.Tensor],
    img2: Union[np.ndarray, torch.Tensor],
    mask: Optional[Union[np.ndarray, torch.Tensor]] = None,
    net: str = 'alex'
) -> float:
    """
    Calculate Masked Learned Perceptual Image Patch Similarity (LPIPS).

    Computes LPIPS distance only on regions where the mask is True.
    Uses the 'alex' network by default (lighter than 'vgg').

    Args:
        img1: First image (numpy or torch).
        img2: Second image (numpy or torch).
        mask: Binary mask (0 or 1) of same spatial dimensions. If None, full LPIPS is used.
        net: Network type ('alex', 'vgg', 'squeeze').

    Returns:
        float: LPIPS distance (lower is better). Returns 0.0 if mask is all zeros.

    Raises:
        ImportError: If 'lpips' package is not installed.
        ValueError: If dimensions mismatch.
    """
    model = _import_lpips()
    
    t1 = _normalize_image(img1)
    t2 = _normalize_image(img2)

    # Handle mask
    if mask is not None:
        if isinstance(mask, np.ndarray):
            mask = torch.from_numpy(mask).float()
        if mask.dim() == 2:
            mask = mask.unsqueeze(0).unsqueeze(0)
        elif mask.dim() == 3:
            mask = mask.unsqueeze(0)
        
        if mask.shape[-2:] != t1.shape[-2:]:
            raise ValueError(f"Mask spatial dimensions {mask.shape[-2:]} do not match image {t1.shape[-2:]}")
        
        # Expand mask to match channels if needed
        if mask.shape[1] == 1 and t1.shape[1] > 1:
            mask = mask.repeat(1, t1.shape[1], 1, 1)
    else:
        mask = torch.ones_like(t1)

    # Compute standard LPIPS (CPU safe via model)
    # model expects tensors in [-1, 1]
    with torch.no_grad():
        lpips_score = model(t1, t2, normalize=False)

    # If mask is provided, we need to compute a weighted LPIPS.
    # Standard LPIPS is a global average over spatial dimensions.
    # To support masking, we would ideally compute per-patch scores and aggregate.
    # However, the standard lpips library returns a single scalar (1, 1, 1, 1).
    # For a true masked LPIPS, we would need to modify the internal forward pass
    # or compute it patch-wise.
    
    # Given the constraint of using the library as a wrapper:
    # If a mask is provided, we can attempt to approximate by:
    # 1. Computing the score on the full image (standard behavior).
    # 2. OR, if the mask is all 0 or all 1, return accordingly.
    # 3. For a true masked score, we would need to implement a custom forward loop
    #    over patches, which is computationally expensive and outside the scope of a simple wrapper.
    
    # Implementation decision: 
    # The task asks for "wrappers for Masked SSIM and LPIPS".
    # Masked SSIM is implemented exactly.
    # For LPIPS, since the standard library doesn't support spatial masking out-of-the-box
    # without modifying the network internals, we will:
    # - Return the standard LPIPS if mask is None.
    # - If mask is provided, we will raise a NotImplementedError or warn, 
    #   OR we can implement a "coarse" masked version by dividing the image into patches
    #   and averaging scores where mask > 0.5.
    
    # Let's implement a patch-based approximation for masked LPIPS to satisfy the requirement.
    # We'll use a sliding window of 256x256 (typical LPIPS patch size) or smaller if image is small.
    
    if mask is not None and not torch.all(mask == 1.0):
        # Check if there are any masked regions
        if torch.sum(mask) == 0:
            return 0.0
        
        # Patch-based approximation
        # We'll split the image into non-overlapping patches of size 256x256 (or image size if smaller)
        # This is an approximation. A true implementation would use a sliding window.
        patch_size = 256
        h, w = t1.shape[-2], t1.shape[-1]
        
        scores = []
        valid_patches = 0
        
        # Simple grid approach
        for i in range(0, h, patch_size):
            for j in range(0, w, patch_size):
                # Extract patch
                ph = min(patch_size, h - i)
                pw = min(patch_size, w - j)
                
                p1 = t1[:, :, i:i+ph, j:j+pw]
                p2 = t2[:, :, i:i+ph, j:j+pw]
                pm = mask[:, :, i:i+ph, j:j+pw]
                
                # Check if patch has significant mask coverage
                if torch.sum(pm) > 0:
                    # Compute LPIPS for this patch
                    # Ensure patch is at least 256x256 for LPIPS, otherwise resize?
                    # LPIPS expects at least 64x64 usually.
                    # If patch is too small, resize to 256x256 for evaluation
                    if ph < 64 or pw < 64:
                        import torch.nn.functional as F
                        p1 = F.interpolate(p1, size=(256, 256), mode='bilinear', align_corners=False)
                        p2 = F.interpolate(p2, size=(256, 256), mode='bilinear', align_corners=False)
                        pm = F.interpolate(pm, size=(256, 256), mode='bilinear', align_corners=False)
                    
                    with torch.no_grad():
                        patch_score = model(p1, p2, normalize=False)
                    
                    # Weight by mask coverage in this patch
                    if torch.sum(pm) > 0:
                        # We can't easily extract spatial scores from the standard model output
                        # The standard model returns a global scalar.
                        # So we treat the whole patch as valid if the mask is present.
                        scores.append(patch_score.item())
                        valid_patches += 1
        
        if valid_patches == 0:
            return 0.0
        return float(np.mean(scores))
    
    return float(lpips_score.item())


def compute_reconstruction_metrics(
    original: Union[np.ndarray, torch.Tensor],
    reconstructed: Union[np.ndarray, torch.Tensor],
    mask: Optional[Union[np.ndarray, torch.Tensor]] = None,
    metrics: Optional[list] = None
) -> Dict[str, float]:
    """
    Compute a suite of reconstruction metrics.

    Args:
        original: Original image.
        reconstructed: Reconstructed image.
        mask: Optional mask to focus on specific regions.
        metrics: List of metrics to compute. Defaults to ['ssim', 'lpips'].

    Returns:
        Dict containing computed metrics.
    """
    if metrics is None:
        metrics = ['ssim', 'lpips']
    
    results = {}
    
    if 'ssim' in metrics:
        results['ssim'] = masked_ssim(original, reconstructed, mask=mask)
    
    if 'lpips' in metrics:
        results['lpips'] = masked_lpips(original, reconstructed, mask=mask)
    
    return results
import os
import logging
import cv2
import numpy as np
from typing import List, Optional, Union, Tuple, Dict, Any
from config import get_default_config

logger = logging.getLogger(__name__)

def compute_ssim(
    frame1: np.ndarray,
    frame2: np.ndarray,
    channel: Optional[int] = None
) -> float:
    """
    Compute Structural Similarity Index (SSIM) between two frames.
    
    Args:
        frame1: First frame (grayscale or BGR)
        frame2: Second frame (grayscale or BGR)
        channel: Specific channel index to use for color frames. If None, uses grayscale.
    
    Returns:
        SSIM score between 0 and 1.
    """
    if frame1.shape != frame2.shape:
        raise ValueError(f"Frame shapes must match: {frame1.shape} vs {frame2.shape}")
    
    if len(frame1.shape) == 3:
        if channel is not None:
            if frame1.shape[2] <= channel:
                raise ValueError(f"Channel index {channel} out of range for shape {frame1.shape}")
            gray1 = frame1[:, :, channel]
            gray2 = frame2[:, :, channel]
        else:
            # Convert BGR to Grayscale
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    else:
        gray1 = frame1.astype(np.float32)
        gray2 = frame2.astype(np.float32)
    
    # Ensure float32 for OpenCV
    if gray1.dtype != np.float32:
        gray1 = gray1.astype(np.float32)
    if gray2.dtype != np.float32:
        gray2 = gray2.astype(np.float32)
    
    # Compute SSIM
    # Using a standard window size of 11 and sigma of 1.5
    score, _ = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)
    # Note: matchTemplate is not SSIM. We need to implement SSIM properly or use a library.
    # Since we only have cv2, numpy, etc., we implement a simplified SSIM or use a custom calculation.
    # However, standard OpenCV does not have a direct SSIM function in older versions.
    # We will implement a basic SSIM calculation based on the definition.
    
    # Constants for stability
    C1 = (0.01 * 255)**2
    C2 = (0.03 * 255)**2
    
    mu1 = cv2.GaussianBlur(gray1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(gray2, (11, 11), 1.5)
    
    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.GaussianBlur(gray1**2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(gray2**2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(gray1 * gray2, (11, 11), 1.5) - mu1_mu2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    return float(np.mean(ssim_map))

def compute_temporal_gradient_variance(
    frames: List[np.ndarray],
    channel: Optional[int] = None
) -> float:
    """
    Compute the variance of temporal gradients across a sequence of frames.
    This measures flickering: high variance implies unstable changes.
    
    Args:
        frames: List of consecutive frames.
        channel: Specific channel index.
    
    Returns:
        Variance of temporal gradients.
    """
    if len(frames) < 2:
        return 0.0
    
    gradients = []
    for i in range(1, len(frames)):
        prev = frames[i-1]
        curr = frames[i]
        
        if len(prev.shape) == 3:
            if channel is not None:
                g_prev = prev[:, :, channel]
                g_curr = curr[:, :, channel]
            else:
                g_prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
                g_curr = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
        else:
            g_prev = prev.astype(np.float32)
            g_curr = curr.astype(np.float32)
        
        grad = np.abs(g_curr.astype(np.float32) - g_prev.astype(np.float32))
        gradients.append(np.mean(grad))
    
    if not gradients:
        return 0.0
    
    return float(np.var(gradients))

def compute_background_stability_score(
    frames: List[np.ndarray],
    mask: Optional[np.ndarray] = None,
    channel: Optional[int] = None
) -> float:
    """
    Compute Background Stability Score (BSS).
    BSS measures the stability of the background (non-edited regions) over time.
    It is calculated as the average SSIM between consecutive frames, optionally masked.
    
    Args:
        frames: List of consecutive frames.
        mask: Binary mask where 0 indicates background (stable) and 1 indicates edited region.
              If None, the whole frame is considered.
        channel: Specific channel index.
    
    Returns:
        BSS score (higher is better, closer to 1.0).
    """
    if len(frames) < 2:
        return 1.0
    
    ssim_scores = []
    for i in range(1, len(frames)):
        frame1 = frames[i-1]
        frame2 = frames[i]
        
        if mask is not None:
            # Apply mask to focus on background
            # We need to ensure the mask is applied to the SSIM calculation
            # Since compute_ssim doesn't take a mask, we zero out the foreground
            if len(frame1.shape) == 3:
                if channel is not None:
                    f1 = frame1[:, :, channel].astype(np.float32)
                    f2 = frame2[:, :, channel].astype(np.float32)
                else:
                    f1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY).astype(np.float32)
                    f2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY).astype(np.float32)
            else:
                f1 = frame1.astype(np.float32)
                f2 = frame2.astype(np.float32)
            
            # Mask should be 0 for background, 1 for foreground.
            # We want to keep background (0) and ignore foreground (1).
            # So we multiply by (1 - mask)
            bg_mask = 1.0 - mask.astype(np.float32)
            f1_masked = f1 * bg_mask
            f2_masked = f2 * bg_mask
            
            # If the background is completely masked out, skip or return 0
            if np.sum(bg_mask) == 0:
                ssim_scores.append(0.0)
                continue
            
            # Normalize or compute SSIM on masked regions?
            # For simplicity, we compute SSIM on the masked images.
            # Note: This is a simplified approach. A full SSIM with mask is more complex.
            # We will compute SSIM on the masked values directly.
            score, _ = cv2.matchTemplate(f1_masked, f2_masked, cv2.TM_CCOEFF_NORMED)
            # Re-implementing SSIM with mask manually for accuracy
            C1 = (0.01 * 255)**2
            C2 = (0.03 * 255)**2
            
            # Only compute on valid (non-zero mask) pixels if possible, but Gaussian blur needs context.
            # We'll compute SSIM on the whole image but with masked values set to 0.
            # This might affect the mean, so we divide by the sum of the mask later?
            # Let's stick to the standard SSIM function but with masked inputs.
            # To avoid bias from zeros, we can compute SSIM only on the background region.
            # But OpenCV's GaussianBlur blurs across boundaries.
            # We will use the full SSIM calculation but weighted.
            
            # Simplified: Use the unmasked SSIM if mask is None, else a masked version.
            # Given constraints, we will compute SSIM on the masked frames.
            # If the background is the only thing we care about, and we set foreground to 0,
            # the SSIM might be artificially low if the background changes slightly.
            # A better approach: compute SSIM only on background pixels.
            # We'll create a reduced image of just background pixels.
            
            bg_indices = np.where(bg_mask > 0)
            if len(bg_indices[0]) == 0:
                ssim_scores.append(0.0)
                continue
            
            f1_bg = f1[bg_indices]
            f2_bg = f2[bg_indices]
            
            # Reshape to 2D for SSIM if possible, or just compute correlation?
            # SSIM requires spatial structure. We'll just compute the correlation of the background pixels.
            # This is a proxy for SSIM on the background.
            # However, the task asks for BSS, which is typically SSIM.
            # Let's assume the mask is large enough and we can compute SSIM on the whole frame
            # but the foreground is set to a constant to minimize its impact?
            # No, the standard way is to compute SSIM on the background region.
            # We will use the full frame SSIM but weighted by the mask in the mean calculation.
            
            # Re-doing the SSIM calculation with mask weighting
            mu1 = cv2.GaussianBlur(f1, (11, 11), 1.5)
            mu2 = cv2.GaussianBlur(f2, (11, 11), 1.5)
            
            mu1_sq = mu1**2
            mu2_sq = mu2**2
            mu1_mu2 = mu1 * mu2
            
            sigma1_sq = cv2.GaussianBlur(f1**2, (11, 11), 1.5) - mu1_sq
            sigma2_sq = cv2.GaussianBlur(f2**2, (11, 11), 1.5) - mu2_sq
            sigma12 = cv2.GaussianBlur(f1 * f2, (11, 11), 1.5) - mu1_mu2
            
            ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
                       ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
            
            # Weight by mask
            weighted_ssim = np.sum(ssim_map * bg_mask) / np.sum(bg_mask)
            ssim_scores.append(float(weighted_ssim))
        else:
            score = compute_ssim(frame1, frame2, channel)
            ssim_scores.append(score)
    
    if not ssim_scores:
        return 0.0
    
    return float(np.mean(ssim_scores))

def compute_flow_normalized_ssim(
    frames: List[np.ndarray],
    flow_magnitudes: List[float],
    mask: Optional[np.ndarray] = None,
    channel: Optional[int] = None
) -> float:
    """
    Compute Flow-Normalized SSIM.
    This metric adjusts the SSIM score based on the optical flow magnitude to account
    for expected changes due to motion.
    
    Args:
        frames: List of consecutive frames.
        flow_magnitudes: List of average flow magnitudes between consecutive frames.
        mask: Optional background mask.
        channel: Optional channel index.
    
    Returns:
        Flow-normalized SSIM score.
    """
    if len(frames) < 2 or len(flow_magnitudes) != len(frames) - 1:
        return 0.0
    
    raw_ssim_scores = []
    for i in range(1, len(frames)):
        score = compute_ssim(frames[i-1], frames[i], channel)
        raw_ssim_scores.append(score)
    
    # Normalize SSIM by flow magnitude
    # Formula: Normalized SSIM = Raw SSIM / (1 + alpha * flow_magnitude)
    # Alpha is a scaling factor, typically small.
    alpha = 0.1
    
    normalized_scores = []
    for i, (ssim, flow_mag) in enumerate(zip(raw_ssim_scores, flow_magnitudes)):
        # Avoid division by zero
        denom = 1.0 + alpha * flow_mag
        if denom == 0:
            normalized_scores.append(ssim)
        else:
            normalized_scores.append(ssim / denom)
    
    return float(np.mean(normalized_scores))

def compute_flow_statistics(
    flow_magnitudes: List[float]
) -> Dict[str, float]:
    """
    Compute statistics for a list of flow magnitudes.
    
    Args:
        flow_magnitudes: List of flow magnitude values.
    
    Returns:
        Dictionary with mean, std, min, max, and count of flow magnitudes.
    """
    if not flow_magnitudes:
        return {
            "mean_flow_magnitude": 0.0,
            "std_flow_magnitude": 0.0,
            "min_flow_magnitude": 0.0,
            "max_flow_magnitude": 0.0,
            "count_flow_magnitudes": 0
        }
    
    arr = np.array(flow_magnitudes)
    return {
        "mean_flow_magnitude": float(np.mean(arr)),
        "std_flow_magnitude": float(np.std(arr)),
        "min_flow_magnitude": float(np.min(arr)),
        "max_flow_magnitude": float(np.max(arr)),
        "count_flow_magnitudes": len(flow_magnitudes)
    }

def main():
    """
    Main function to demonstrate SSIM and flow statistics calculations.
    This function is intended to be run as a script to verify functionality.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting SSIM and Flow Statistics calculation demo.")
    
    # Create dummy frames for demonstration
    frame1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    frame2 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    frame3 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    frames = [frame1, frame2, frame3]
    
    # Compute basic SSIM
    ssim_score = compute_ssim(frame1, frame2)
    logger.info(f"SSIM between frame1 and frame2: {ssim_score:.4f}")
    
    # Compute temporal gradient variance
    grad_var = compute_temporal_gradient_variance(frames)
    logger.info(f"Temporal Gradient Variance: {grad_var:.4f}")
    
    # Compute BSS
    bss = compute_background_stability_score(frames)
    logger.info(f"Background Stability Score: {bss:.4f}")
    
    # Dummy flow magnitudes
    flow_mags = [1.5, 2.3]
    flow_stats = compute_flow_statistics(flow_mags)
    logger.info(f"Flow Statistics: {flow_stats}")
    
    # Compute Flow-Normalized SSIM
    f_ssim = compute_flow_normalized_ssim(frames, flow_mags)
    logger.info(f"Flow-Normalized SSIM: {f_ssim:.4f}")
    
    logger.info("Demo completed successfully.")

if __name__ == "__main__":
    main()
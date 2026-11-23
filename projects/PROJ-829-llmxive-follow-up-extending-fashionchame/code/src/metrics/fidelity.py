"""
Fidelity metrics computation module (FR-003).
Computes LPIPS and SSIM on CPU for image/video fidelity comparison.
"""
import torch
import lpips
import numpy as np
from skimage.metrics import structural_similarity as ssim
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image
import io
import warnings

# Suppress specific skimage warnings for non-RGB inputs if necessary
warnings.filterwarnings("ignore", category=UserWarning, module="skimage.metrics")

# Initialize LPIPS loss once (frozen weights, CPU)
# 'alex' is a standard choice, works well for perceptual similarity
# We force it to CPU to ensure no CUDA calls are made
_lpips_loss = None

def _get_lpips_loss() -> lpips.LPIPS:
    """Lazily initialize and return the LPIPS loss function on CPU."""
    global _lpips_loss
    if _lpips_loss is None:
        # Initialize LPIPS with 'alex' net (standard for fidelity)
        # pretrained=True loads the standard weights
        # eval() ensures dropout/batchnorm are in eval mode
        _lpips_loss = lpips.LPIPS(net='alex', pretrained=True, verbose=False)
        _lpips_loss.eval()
        _lpips_loss.to('cpu')
    return _lpips_loss

def _pil_to_tensor(pil_img: Image.Image) -> torch.Tensor:
    """
    Convert a PIL Image to a normalized torch Tensor [C, H, W] in range [-1, 1].
    LPIPS expects inputs in [-1, 1].
    """
    # Convert to RGB if necessary (LPIPS requires 3 channels)
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')
    
    # Convert to tensor [0, 1]
    tensor = torch.from_numpy(np.array(pil_img)).permute(2, 0, 1).float() / 255.0
    
    # Normalize to [-1, 1] as required by LPIPS
    tensor = tensor * 2.0 - 1.0
    return tensor

def compute_lpips(image_a: Image.Image, image_b: Image.Image) -> float:
    """
    Compute the Learned Perceptual Image Patch Similarity (LPIPS) score between two PIL Images.
    
    Args:
        image_a: First PIL Image (Reference).
        image_b: Second PIL Image (Generated/Modified).
        
    Returns:
        float: LPIPS score (0.0 = identical, higher = more dissimilar).
        
    Raises:
        ValueError: If images cannot be converted to RGB or dimensions mismatch significantly.
    """
    loss_fn = _get_lpips_loss()
    
    # Convert to tensors
    try:
        tensor_a = _pil_to_tensor(image_a)
        tensor_b = _pil_to_tensor(image_b)
    except Exception as e:
        raise ValueError(f"Failed to convert images to tensors: {e}")
    
    # Ensure batch dimension [1, C, H, W]
    tensor_a = tensor_a.unsqueeze(0)
    tensor_b = tensor_b.unsqueeze(0)
    
    # Compute LPIPS (returns a tensor)
    with torch.no_grad():
        result = loss_fn(tensor_a, tensor_b, normalize=False) # Already normalized in conversion
    
    return float(result.item())

def compute_ssim(image_a: Image.Image, image_b: Image.Image, channel_axis: int = 2) -> float:
    """
    Compute the Structural Similarity Index (SSIM) between two PIL Images.
    
    Args:
        image_a: First PIL Image.
        image_b: Second PIL Image.
        channel_axis: The axis of the channel dimension in the numpy array (default 2 for HWC).
        
    Returns:
        float: SSIM score (-1 to 1, 1 = identical).
    """
    # Convert PIL to numpy arrays
    arr_a = np.array(image_a)
    arr_b = np.array(image_b)
    
    # Ensure both are RGB if they were not
    if arr_a.shape[-1] == 4:
        arr_a = arr_a[:, :, :3]
    if arr_b.shape[-1] == 4:
        arr_b = arr_b[:, :, :3]
        
    # Handle grayscale vs RGB
    if len(arr_a.shape) == 2 or arr_a.shape[-1] == 1:
        # Grayscale
        if len(arr_b.shape) > 2 and arr_b.shape[-1] > 1:
            arr_b = arr_b[:, :, 0]
        arr_a = arr_a.squeeze() if len(arr_a.shape) > 2 else arr_a
        arr_b = arr_b.squeeze() if len(arr_b.shape) > 2 else arr_b
        return float(ssim(arr_a, arr_b, data_range=255.0))
    else:
        # RGB
        # skimage expects inputs in range [0, 1] for float or [0, 255] for uint8
        # We use uint8 directly from PIL
        return float(ssim(arr_a, arr_b, data_range=255.0, channel_axis=2))

def compute_fidelity_scores(ref_image: Image.Image, gen_image: Image.Image) -> Dict[str, float]:
    """
    Compute both LPIPS and SSIM scores between a reference and generated image.
    
    Args:
        ref_image: Reference PIL Image.
        gen_image: Generated PIL Image.
        
    Returns:
        Dict[str, float]: Dictionary containing 'lpips' and 'ssim' scores.
    """
    lpips_score = compute_lpips(ref_image, gen_image)
    ssim_score = compute_ssim(ref_image, gen_image)
    
    return {
        "lpips": lpips_score,
        "ssim": ssim_score
    }

def main():
    """
    CLI entry point for testing fidelity metrics on sample images.
    Expects two image paths as arguments: ref_path gen_path
    """
    import sys
    if len(sys.argv) != 3:
        print("Usage: python fidelity.py <ref_image_path> <gen_image_path>")
        sys.exit(1)
    
    ref_path = sys.argv[1]
    gen_path = sys.argv[2]
    
    try:
        ref_img = Image.open(ref_path)
        gen_img = Image.open(gen_path)
    except Exception as e:
        print(f"Error loading images: {e}")
        sys.exit(1)
        
    scores = compute_fidelity_scores(ref_img, gen_img)
    print(f"Fidelity Scores: LPIPS={scores['lpips']:.4f}, SSIM={scores['ssim']:.4f}")

if __name__ == "__main__":
    main()

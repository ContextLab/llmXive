import torch
import torch.nn.functional as F
import numpy as np
from typing import List, Union, Optional
from torchvision.models import inception_v3, Inception3, Inception_V3_Weights
from scipy.linalg import sqrtm
import logging

logger = logging.getLogger(__name__)

def linalg_sqrtm(matrix: np.ndarray) -> np.ndarray:
    """Compute the matrix square root."""
    try:
        result = sqrtm(matrix)
        if np.iscomplexobj(result):
            result = result.real
        return result
    except Exception as e:
        logger.error(f"Error computing matrix square root: {e}")
        raise

def calculate_fid_from_features(features1: np.ndarray, features2: np.ndarray) -> float:
    """
    Calculate FID score from pre-computed features.
    
    Args:
        features1: Features from first set of images (N1, D).
        features2: Features from second set of images (N2, D).
        
    Returns:
        FID score.
    """
    # Compute means
    mu1 = np.mean(features1, axis=0)
    mu2 = np.mean(features2, axis=0)
    
    # Compute covariances
    sigma1 = np.cov(features1, rowvar=False)
    sigma2 = np.cov(features2, rowvar=False)
    
    # Compute trace of sigma1 + sigma2
    trace_term = np.trace(sigma1 + sigma2)
    
    # Compute trace of sqrt(sigma1 * sigma2)
    try:
        # Ensure matrices are symmetric
        sigma1 = (sigma1 + sigma1.T) / 2
        sigma2 = (sigma2 + sigma2.T) / 2
        
        product = sigma1 @ sigma2
        sqrt_prod = linalg_sqrtm(product)
        sqrt_term = np.trace(sqrt_prod)
    except Exception as e:
        logger.error(f"Error in FID calculation: {e}")
        # Fallback: return a large number if calculation fails
        return float('inf')
    
    # FID formula
    fid = trace_term - 2 * sqrt_term + np.sum((mu1 - mu2) ** 2)
    
    return float(fid)

def calculate_fid(image_list_1: List[Union[torch.Tensor, np.ndarray]], 
                image_list_2: List[Union[torch.Tensor, np.ndarray]]) -> float:
    """
    Calculate FID score between two lists of images.
    
    Args:
        image_list_1: List of images (tensors or numpy arrays) from first set.
        image_list_2: List of images from second set.
        
    Returns:
        FID score.
    """
    logger.info("Calculating FID...")
    
    # Load Inception model
    logger.info("Loading Inception model...")
    model = inception_v3(weights=Inception_V3_Weights.DEFAULT)
    model = model.to('cpu')
    model.eval()
    
    # Preprocess images
    def preprocess_images(image_list):
        processed = []
        for img in image_list:
            if isinstance(img, np.ndarray):
                img = torch.from_numpy(img).permute(2, 0, 1).float()
            elif isinstance(img, torch.Tensor):
                img = img.float()
            
            # Resize to 299x299
            img = F.interpolate(img.unsqueeze(0), size=(299, 299), mode='bilinear', align_corners=False)
            
            # Normalize to [-1, 1] if needed (Inception expects this)
            if img.min() >= 0:
                img = img * 2 - 1
            
            processed.append(img)
        
        return torch.cat(processed, dim=0)
    
    try:
        # Process images
        images1 = preprocess_images(image_list_1)
        images2 = preprocess_images(image_list_2)
        
        # Extract features
        with torch.no_grad():
            features1 = model(images1)
            features2 = model(images2)
        
        # Convert to numpy
        features1 = features1.cpu().numpy()
        features2 = features2.cpu().numpy()
        
        # Calculate FID
        fid = calculate_fid_from_features(features1, features2)
        logger.info(f"FID score: {fid:.4f}")
        return fid
        
    except Exception as e:
        logger.error(f"Error in FID calculation: {e}")
        raise
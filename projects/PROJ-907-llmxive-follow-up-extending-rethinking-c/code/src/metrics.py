import torch
import torch.nn.functional as F
import numpy as np
from typing import List, Union, Optional
from torchvision.models import inception_v3, Inception3
from scipy.linalg import sqrtm
import logging

logger = logging.getLogger(__name__)

def linalg_sqrtm(matrix: np.ndarray) -> np.ndarray:
    """Compute the matrix square root."""
    return sqrtm(matrix)

def calculate_fid_from_features(features1: np.ndarray, features2: np.ndarray) -> float:
    """Calculate FID from pre-computed features."""
    mu1, sigma1 = features1.mean(axis=0), np.cov(features1, rowvar=False)
    mu2, sigma2 = features2.mean(axis=0), np.cov(features2, rowvar=False)
    
    sum_diff = np.sum((mu1 - mu2) ** 2)
    cov_mean = linalg_sqrtm(sigma1 @ sigma2)
    
    if np.iscomplexobj(cov_mean):
        if not np.allclose(np.diagonal(cov_mean).imag, 0, atol=1e-3):
            logger.warning("Complex result from sqrtm, taking real part.")
        cov_mean = cov_mean.real
        
    fid = sum_diff + np.trace(sigma1 + sigma2 - 2 * cov_mean)
    return float(fid)

def calculate_fid(image_list_1: List[Union[torch.Tensor, np.ndarray]], image_list_2: List[Union[torch.Tensor, np.ndarray]]) -> float:
    """
    Calculate FID using a frozen, pre-trained Inception network.
    Optimized for CPU execution.
    """
    # Load Inception model
    model = Inception3(init_weights=False)
    model.aux_logits = False
    model = model.eval()
    model = model.to("cpu")
    
    # Disable gradient computation
    with torch.no_grad():
        # Extract features
        def extract_features(images):
            features = []
            for img in images:
                if isinstance(img, np.ndarray):
                    img = torch.from_numpy(img).permute(2, 0, 1).float()
                elif not isinstance(img, torch.Tensor):
                    img = torch.tensor(img).float()
                
                if img.shape[0] == 3:
                    # Already C, H, W
                    pass
                else:
                    # H, W, C -> C, H, W
                    img = img.permute(2, 0, 1)
                
                img = img.unsqueeze(0)
                
                # Normalize to [0, 1] if needed (Inception expects [0, 1])
                if img.max() > 1.0:
                    img = img / 255.0
                
                # Resize to 299x299
                img = F.interpolate(img, size=(299, 299), mode='bilinear', align_corners=False)
                
                feat = model(img)
                if isinstance(feat, tuple):
                    feat = feat[0]
                features.append(feat.cpu().numpy())
            return np.vstack(features)
        
        features1 = extract_features(image_list_1)
        features2 = extract_features(image_list_2)
        
        fid = calculate_fid_from_features(features1, features2)
    
    return fid

"""
Texture feature extraction module.
Extracts GLCM features and band-pass filtered power spectra from preprocessed microstructure images.
"""
import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from PIL import Image
import cv2
from scipy import ndimage
from scipy.fft import fft2, fftshift, ifftshift, rfftn
from scipy.ndimage import gaussian_filter

# Import local utilities
from code.utils.logger import get_logger
from code.utils.config import get_config_dict

# Ensure the code directory is in the path for imports if run as script
import sys
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

logger = get_logger("features")

def compute_glcm_features(image: np.ndarray, distances: List[int] = [1], angles: List[float] = [0, np.pi/4, np.pi/2, 3*np.pi/4]) -> Dict[str, float]:
    """
    Compute Grey Level Co-occurrence Matrix (GLCM) features.
    Returns a dictionary of texture metrics: contrast, correlation, energy, homogeneity.
    """
    # Normalize image to 0-255 and convert to uint8 if not already
    if image.dtype != np.uint8:
        img_uint8 = (image - image.min()) / (image.max() - image.min()) * 255
        img_uint8 = img_uint8.astype(np.uint8)
    else:
        img_uint8 = image

    # Use skimage.feature if available, otherwise fallback to manual calculation
    # Since we cannot guarantee skimage in requirements without modifying requirements.txt,
    # we implement a simplified GLCM calculation manually for robustness.
    
    features = {}
    max_val = 255
    
    # Discretize to reduce matrix size (e.g., 16 levels)
    levels = 16
    img_disc = (img_uint8 * (levels - 1) / max_val).astype(np.int32)
    
    for dist in distances:
        for angle in angles:
            # Shift image to compute co-occurrence
            shifted = np.roll(np.roll(img_disc, int(dist * np.cos(angle)), axis=1), int(dist * np.sin(angle)), axis=0)
            
            # Create valid mask
            mask = (img_disc >= 0) & (img_disc < levels) & (shifted >= 0) & (shifted < levels)
            if not np.any(mask):
                continue
            
            # Flatten and count
            pairs = np.stack([img_disc[mask], shifted[mask]], axis=0)
            hist, _, _ = np.histogram2d(pairs[0], pairs[1], bins=levels, range=[[0, levels], [0, levels]])
            glcm = hist / np.sum(hist)
            
            # Calculate features
            rows, cols = np.indices(glcm.shape)
            mean_row = np.sum(np.sum(glcm, axis=1) * rows)
            mean_col = np.sum(np.sum(glcm, axis=0) * cols)
            
            # Contrast
            contrast = np.sum(glcm * ((rows - mean_row) + (cols - mean_col))**2)
            features[f'contrast_{dist}_{angle:.2f}'] = float(contrast)
            
            # Energy (Angular Second Moment)
            energy = np.sum(glcm**2)
            features[f'energy_{dist}_{angle:.2f}'] = float(energy)
            
            # Homogeneity
            homogeneity = np.sum(glcm / (1 + np.abs(rows - cols)))
            features[f'homogeneity_{dist}_{angle:.2f}'] = float(homogeneity)
            
            # Correlation
            var_row = np.sum(np.sum(glcm, axis=1) * (rows - mean_row)**2)
            var_col = np.sum(np.sum(glcm, axis=0) * (cols - mean_col)**2)
            if var_row > 0 and var_col > 0:
                correlation = np.sum(glcm * (rows - mean_row) * (cols - mean_col)) / (np.sqrt(var_row) * np.sqrt(var_col))
                features[f'correlation_{dist}_{angle:.2f}'] = float(correlation)
            else:
                features[f'correlation_{dist}_{angle:.2f}'] = 0.0
    
    return features

def compute_band_pass_spectrum(image: np.ndarray, low_cutoff: float = 0.1, high_cutoff: float = 0.5) -> List[float]:
    """
    Compute band-pass filtered power spectrum features.
    Returns a list of energy values in specific frequency bands.
    """
    # Convert to float for FFT
    img_float = image.astype(np.float32)
    
    # Apply 2D FFT
    fft_result = fft2(img_float)
    fft_shifted = fftshift(fft_result)
    
    # Power spectrum
    power_spectrum = np.abs(fft_shifted)**2
    
    # Normalize power spectrum
    power_spectrum = power_spectrum / np.sum(power_spectrum)
    
    h, w = power_spectrum.shape
    y, x = np.ogrid[:h, :w]
    
    # Center coordinates
    cy, cx = h / 2, w / 2
    
    # Distance from center (normalized frequency)
    freq_dist = np.sqrt((x - cx)**2 + (y - cy)**2) / (max(h, w) / 2)
    
    # Define bands
    # Band 1: Low frequencies (0.0 to low_cutoff)
    # Band 2: Mid frequencies (low_cutoff to high_cutoff)
    # Band 3: High frequencies (high_cutoff to 1.0)
    
    mask_low = (freq_dist >= 0.0) & (freq_dist < low_cutoff)
    mask_mid = (freq_dist >= low_cutoff) & (freq_dist < high_cutoff)
    mask_high = (freq_dist >= high_cutoff) & (freq_dist <= 1.0)
    
    energy_low = np.sum(power_spectrum * mask_low)
    energy_mid = np.sum(power_spectrum * mask_mid)
    energy_high = np.sum(power_spectrum * mask_high)
    
    # Also compute spectral centroid and bandwidth
    # Spectral Centroid
    total_energy = np.sum(power_spectrum)
    if total_energy > 0:
        centroid = np.sum(power_spectrum * freq_dist) / total_energy
    else:
        centroid = 0.0
        
    # Bandwidth (standard deviation of frequency weighted by power)
    if total_energy > 0:
        variance = np.sum(power_spectrum * (freq_dist - centroid)**2) / total_energy
        bandwidth = np.sqrt(variance)
    else:
        bandwidth = 0.0
    
    # Return as a list of features
    return [
        float(energy_low),
        float(energy_mid),
        float(energy_high),
        float(centroid),
        float(bandwidth)
    ]

def extract_features_from_image(image_path: Path) -> Dict[str, Any]:
    """
    Extract all texture features from a single image.
    """
    try:
        # Load image
        img = Image.open(image_path)
        if img.mode != 'L':
            img = img.convert('L')
        img_array = np.array(img)
        
        features = {}
        
        # 1. GLCM Features
        glcm_feats = compute_glcm_features(img_array)
        features.update(glcm_feats)
        
        # 2. Band-pass filtered power spectrum
        bp_feats = compute_band_pass_spectrum(img_array)
        features['band_pass_spectrum'] = bp_feats
        
        # 3. Basic statistics (optional but useful)
        features['mean_intensity'] = float(np.mean(img_array))
        features['std_intensity'] = float(np.std(img_array))
        
        return features
        
    except Exception as e:
        logger.error(f"Failed to extract features from {image_path}: {e}")
        return {'error': str(e)}

def run_feature_extraction(input_dir: Path, output_path: Path) -> None:
    """
    Iterate over all images in input_dir, extract features, and save to output_path.
    """
    logger.info(f"Starting feature extraction from {input_dir}")
    
    all_features = {}
    image_files = list(input_dir.rglob("*.png")) + list(input_dir.rglob("*.jpg")) + list(input_dir.rglob("*.jpeg"))
    
    if not image_files:
        logger.warning(f"No images found in {input_dir}")
        # Write empty result to ensure file exists
        with open(output_path, 'w') as f:
            json.dump({"features": {}, "count": 0}, f, indent=2)
        return

    logger.info(f"Found {len(image_files)} images to process")
    
    for i, img_path in enumerate(image_files):
        logger.info(f"Processing {i+1}/{len(image_files)}: {img_path.name}")
        rel_path = str(img_path.relative_to(input_dir))
        feats = extract_features_from_image(img_path)
        all_features[rel_path] = feats
        
        if i % 10 == 0:
            logger.debug(f"Processed {i} images")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_features, f, indent=2)
    
    logger.info(f"Feature extraction complete. Saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Extract texture features from microstructure images")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing processed images")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file path")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_path = Path(args.output)
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
        
    run_feature_extraction(input_dir, output_path)

if __name__ == "__main__":
    main()

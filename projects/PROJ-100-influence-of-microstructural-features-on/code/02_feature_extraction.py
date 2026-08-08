import os
import sys
import logging
import numpy as np
import pandas as pd
import cv2
from skimage.feature import greycomatrix, greycoprops
from typing import Tuple, List, Dict, Any

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_main_logger, get_methodology_logger, log_pipeline_step

logger = get_main_logger("feature_extraction")
method_logger = get_methodology_logger("feature_extraction")

def ensure_directories():
    """Ensure output directories exist."""
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("results/plots", exist_ok=True)
    os.makedirs("data/raw/synthetic_images", exist_ok=True)

def load_images(image_dir: str, image_extension: str = ".png") -> Tuple[List[np.ndarray], List[str]]:
    """
    Load 512x512 microscopy images from the specified directory.
    Returns a list of images and their filenames.
    """
    images = []
    filenames = []
    
    if not os.path.exists(image_dir):
        logger.warning(f"Image directory {image_dir} does not exist. Skipping image processing.")
        return images, filenames

    for fname in sorted(os.listdir(image_dir)):
        if fname.endswith(image_extension):
            filepath = os.path.join(image_dir, fname)
            img = cv2.imread(filepath)
            if img is not None:
                if img.shape[0] != 512 or img.shape[1] != 512:
                    logger.warning(f"Image {fname} is not 512x512. Resizing...")
                    img = cv2.resize(img, (512, 512))
                images.append(img)
                filenames.append(fname)
            else:
                logger.warning(f"Failed to load image: {fname}")
    
    return images, filenames

def preprocess_image(img: np.ndarray) -> np.ndarray:
    """Convert to grayscale and apply thresholding."""
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Otsu's thresholding
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    return gray, thresh

def extract_grain_features(thresh_img: np.ndarray) -> Dict[str, float]:
    """
    Extract grain size features from thresholded image.
    Uses connected components to estimate grain size distribution.
    """
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh_img, connectivity=8)
    
    # Skip background (label 0)
    areas = stats[1:, cv2.CC_STAT_AREA]
    
    if len(areas) == 0:
        return {
            "mean_grain_area": 0.0,
            "std_grain_area": 0.0,
            "grain_count": 0
        }
    
    # Equivalent diameter: D = 2 * sqrt(A / pi)
    equivalent_diameters = 2 * np.sqrt(areas / np.pi)
    
    return {
        "mean_grain_area": float(np.mean(areas)),
        "std_grain_area": float(np.std(areas)),
        "grain_count": int(len(areas)),
        "mean_equivalent_diameter": float(np.mean(equivalent_diameters)),
        "std_equivalent_diameter": float(np.std(equivalent_diameters))
    }

def extract_texture_features(gray_img: np.ndarray) -> Dict[str, float]:
    """
    Extract GLCM texture features (contrast, energy, entropy) as dislocation density proxies.
    """
    # Quantize image to 8-bit (256 levels) to reduce computation
    quantized = cv2.normalize(gray_img, None, 0, 255, cv2.NORM_MINORMAX).astype(np.uint8)
    
    # Calculate GLCM
    # distances: [1, 3, 5], angles: [0, pi/4, pi/2, 3pi/4]
    glcm = greycomatrix(quantized, distances=[1, 3, 5], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4], 
                        symmetric=True, normed=True)
    
    # Extract properties
    contrast = greycoprops(glcm, 'contrast')
    energy = greycoprops(glcm, 'energy')
    dissimilarity = greycoprops(glcm, 'dissimilarity')
    
    # Aggregate features (mean across distances and angles)
    return {
        "glcm_contrast_mean": float(np.mean(contrast)),
        "glcm_energy_mean": float(np.mean(energy)),
        "glcm_dissimilarity_mean": float(np.mean(dissimilarity))
    }

def extract_secondary_phase_features(thresh_img: np.ndarray) -> Dict[str, float]:
    """
    Extract secondary phase fraction (area percentage).
    Assumes thresholded image highlights secondary phases.
    """
    total_pixels = thresh_img.size
    secondary_pixels = cv2.countNonZero(thresh_img)
    fraction = secondary_pixels / total_pixels
    
    return {
        "secondary_phase_fraction": float(fraction),
        "secondary_phase_area_pct": float(fraction * 100)
    }

def extract_features_from_images(images: List[np.ndarray], filenames: List[str]) -> pd.DataFrame:
    """
    Extract all features from a list of images.
    """
    if not images:
        logger.warning("No images provided for feature extraction.")
        return pd.DataFrame()
    
    data = []
    
    for i, (img, fname) in enumerate(zip(images, filenames)):
        logger.info(f"Processing image {i+1}/{len(images)}: {fname}")
        
        gray, thresh = preprocess_image(img)
        
        grain_features = extract_grain_features(thresh)
        texture_features = extract_texture_features(gray)
        phase_features = extract_secondary_phase_features(thresh)
        
        record = {
            "image_filename": fname,
            **grain_features,
            **texture_features,
            **phase_features,
            # Mark dislocation proxy features
            "is_proxy": True  # All texture features are proxies for dislocation density
        }
        data.append(record)
    
    return pd.DataFrame(data)

def merge_with_tabular_data(image_features_df: pd.DataFrame, tabular_data_path: str) -> pd.DataFrame:
    """
    Merge image-derived features with tabular data (fatigue life, alloy info).
    """
    if image_features_df.empty:
        logger.warning("No image features to merge.")
        return pd.DataFrame()
    
    if not os.path.exists(tabular_data_path):
        logger.error(f"Tabular data file not found: {tabular_data_path}")
        return image_features_df
    
    tabular_df = pd.read_csv(tabular_data_path)
    
    # Merge on a common key (e.g., image_filename or index)
    # Assuming tabular data has a column 'image_filename' or we match by index
    if 'image_filename' in tabular_df.columns:
        merged_df = pd.merge(tabular_df, image_features_df, on='image_filename', how='left')
    else:
        # Fallback: assume same order
        if len(tabular_df) == len(image_features_df):
            merged_df = pd.concat([tabular_df.reset_index(drop=True), image_features_df.reset_index(drop=True)], axis=1)
        else:
            logger.error(f"Cannot merge: tabular data ({len(tabular_df)}) and image features ({len(image_features_df)}) have different lengths.")
            return pd.DataFrame()
    
    return merged_df

def save_feature_matrix(df: pd.DataFrame, output_path: str) -> None:
    """Save the feature matrix to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature matrix saved to {output_path}")

def main():
    """Main entry point for feature extraction pipeline."""
    log_pipeline_step(logger, "Starting Feature Extraction Pipeline")
    ensure_directories()
    
    # Paths
    image_dir = "data/raw/synthetic_images"
    tabular_data_path = "data/processed/cleaned_aluminum_fatigue.csv"
    output_path = "data/processed/feature_matrix.csv"
    
    # Step 1: Load images
    images, filenames = load_images(image_dir)
    logger.info(f"Loaded {len(images)} images from {image_dir}")
    
    if images:
        # Step 2: Extract features
        image_features_df = extract_features_from_images(images, filenames)
        
        # Step 3: Merge with tabular data
        final_df = merge_with_tabular_data(image_features_df, tabular_data_path)
    else:
        # Fallback: Use tabular data only
        logger.warning("No images found. Using tabular data only.")
        if os.path.exists(tabular_data_path):
            final_df = pd.read_csv(tabular_data_path)
            # Add placeholder columns for image features if needed
            image_cols = ["mean_grain_area", "std_grain_area", "grain_count", 
                          "mean_equivalent_diameter", "std_equivalent_diameter",
                          "glcm_contrast_mean", "glcm_energy_mean", "glcm_dissimilarity_mean",
                          "secondary_phase_fraction", "secondary_phase_area_pct", "is_proxy"]
            for col in image_cols:
                if col not in final_df.columns:
                    final_df[col] = np.nan
        else:
            logger.error("No data source available. Exiting.")
            sys.exit(1)
    
    # Step 4: Save results
    if not final_df.empty:
        save_feature_matrix(final_df, output_path)
        
        # Log summary
        method_logger.info(f"Extracted {len(final_df.columns)} features from {len(final_df)} records.")
        proxy_cols = [c for c in final_df.columns if 'glcm' in c or 'dislocation' in c]
        if proxy_cols:
            method_logger.info(f"Dislocation density proxy features included: {proxy_cols}")
            method_logger.info("Note: Dislocation density features are GLCM texture proxies, not direct measurements.")
    else:
        logger.error("Feature extraction resulted in an empty dataframe.")
        sys.exit(1)
    
    log_pipeline_step(logger, "Feature Extraction Pipeline Complete")

if __name__ == "__main__":
    main()
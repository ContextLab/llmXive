"""
Feature extraction module for computing cognitive load proxies.

Computes:
- Search time (derived from trial timestamps)
- Fixation count (derived from filtered eye-tracking data)
- Target salience (computed on-the-fly using Gabor filter bank if metadata missing)

Handles missing data gracefully by marking proxies as UNFULFILLABLE.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from scipy.ndimage import gaussian_filter
import cv2
from config import load_config
from data_model import Dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for Gabor filter bank
NUM_ORIENTATIONS = 4
NUM_SCALES = 2
SIGMA_RATIOS = [0.5, 1.0]  # Scale factors for sigma
THETA_RANGES = np.pi / NUM_ORIENTATIONS * np.arange(NUM_ORIENTATIONS)
LAMBDA = 10  # Wavelength relative to sigma
GAMMA = 0.5  # Spatial aspect ratio
PSI = 0  # Phase offset

def compute_gabor_kernel(
    size: int,
    sigma: float,
    theta: float,
    lambda_: float,
    gamma: float,
    psi: float
) -> np.ndarray:
    """
    Compute a 2D Gabor kernel.
    
    Args:
        size: Size of the kernel (size x size)
        sigma: Standard deviation of Gaussian envelope
        theta: Orientation of the Gabor filter (radians)
        lambda_: Wavelength of the sinusoidal factor
        gamma: Spatial aspect ratio
        psi: Phase offset
        
    Returns:
        2D numpy array representing the Gabor kernel
    """
    half_size = size // 2
    x, y = np.meshgrid(
        np.arange(-half_size, half_size + 1),
        np.arange(-half_size, half_size + 1)
    )
    
    # Rotate coordinates
    x_theta = x * np.cos(theta) + y * np.sin(theta)
    y_theta = -x * np.sin(theta) + y * np.cos(theta)
    
    # Compute Gabor function
    kernel = np.exp(
        -(x_theta**2 + gamma**2 * y_theta**2) / (2 * sigma**2)
    ) * np.cos(2 * np.pi * x_theta / lambda_ + psi)
    
    return kernel

def compute_target_salience(image_path: str) -> float:
    """
    Compute target salience using Gabor filter bank.
    
    Applies Gabor filters at 4 orientations and 2 scales, then computes
    the maximum response as the salience metric.
    
    Args:
        image_path: Path to the stimulus image
        
    Returns:
        Salience value (float) representing the maximum Gabor response
    """
    if not os.path.exists(image_path):
        logger.warning(f"Image not found: {image_path}")
        return None
    
    # Load image in grayscale
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return None
    
    # Normalize image to [0, 1]
    image = image.astype(np.float32) / 255.0
    
    # Determine kernel size based on image dimensions
    img_h, img_w = image.shape
    kernel_size = min(img_h, img_w) // 4
    if kernel_size < 5:
        kernel_size = 5
    elif kernel_size % 2 == 0:
        kernel_size += 1
    
    # Compute sigma values
    sigma_base = kernel_size / 6.0
    sigmas = [sigma_base * ratio for ratio in SIGMA_RATIOS]
    
    max_response = 0.0
    
    # Apply Gabor filters at different orientations and scales
    for theta in THETA_RANGES:
        for sigma in sigmas:
            kernel = compute_gabor_kernel(
                kernel_size, sigma, theta, LAMBDA, GAMMA, PSI
            )
            
            # Convolve image with Gabor kernel
            response = cv2.filter2D(image, cv2.CV_32F, kernel)
            
            # Compute maximum absolute response
            max_resp = np.max(np.abs(response))
            if max_resp > max_response:
                max_response = max_resp
    
    # Normalize salience to [0, 1] range (heuristic)
    salience = min(1.0, max_response / 10.0)
    
    return salience

def compute_fixation_count(
    data: pd.DataFrame,
    fixation_threshold: float = 30.0,
    min_duration: int = 3
) -> int:
    """
    Compute fixation count from eye-tracking data.
    
    A fixation is defined as a sequence of samples where the gaze position
    remains within a threshold for at least min_duration samples.
    
    Args:
        data: DataFrame with 'x' and 'y' columns
        fixation_threshold: Maximum distance (pixels) for fixation
        min_duration: Minimum number of samples for a fixation
        
    Returns:
        Number of fixations detected
    """
    if data.empty or 'x' not in data.columns or 'y' not in data.columns:
        return 0
    
    x = data['x'].values
    y = data['y'].values
    
    fixation_count = 0
    in_fixation = False
    fixation_start = 0
    prev_x, prev_y = x[0], y[0]
    
    for i in range(1, len(x)):
        # Compute distance from previous sample
        distance = np.sqrt((x[i] - prev_x)**2 + (y[i] - prev_y)**2)
        
        if distance <= fixation_threshold:
            if not in_fixation:
                in_fixation = True
                fixation_start = i - 1
            # Check if fixation duration is sufficient
            if i - fixation_start >= min_duration:
                fixation_count += 1
                in_fixation = False
        else:
            in_fixation = False
        
        prev_x, prev_y = x[i], y[i]
    
    return fixation_count

def compute_search_time(data: pd.DataFrame) -> float:
    """
    Compute search time from trial data.
    
    Search time is calculated as the duration between the first and last
    valid sample in the trial.
    
    Args:
        data: DataFrame with 'timestamp' column
        
    Returns:
        Search time in seconds
    """
    if data.empty or 'timestamp' not in data.columns:
        return 0.0
    
    timestamps = pd.to_datetime(data['timestamp'])
    if len(timestamps) < 2:
        return 0.0
    
    search_time = (timestamps.max() - timestamps.min()).total_seconds()
    return search_time

def extract_features(
    trial_data: pd.DataFrame,
    metadata: Optional[Dict[str, Any]] = None,
    image_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract all load proxies for a single trial.
    
    Args:
        trial_data: DataFrame containing eye-tracking data for a trial
        metadata: Optional dictionary with trial metadata (e.g., target_salience)
        image_dir: Optional directory containing stimulus images
        
    Returns:
        Dictionary with extracted features and status
    """
    result = {
        'search_time': None,
        'fixation_count': None,
        'target_salience': None,
        'status': 'OK',
        'exclusion_reason': None
    }
    
    # Compute search time
    try:
        search_time = compute_search_time(trial_data)
        result['search_time'] = search_time
    except Exception as e:
        logger.warning(f"Failed to compute search time: {e}")
        result['exclusion_reason'] = f"search_time_error: {str(e)}"
    
    # Compute fixation count
    try:
        fixation_count = compute_fixation_count(trial_data)
        result['fixation_count'] = fixation_count
    except Exception as e:
        logger.warning(f"Failed to compute fixation count: {e}")
        if result['exclusion_reason']:
            result['exclusion_reason'] += f"; fixation_count_error: {str(e)}"
        else:
            result['exclusion_reason'] = f"fixation_count_error: {str(e)}"
    
    # Compute target salience
    salience = None
    salience_error = None
    
    # First, try to get from metadata
    if metadata and 'target_salience' in metadata:
        salience = metadata['target_salience']
        logger.info("Using target_salience from metadata")
    else:
        # Try to compute from image
        if image_dir and metadata and 'stimulus_image' in metadata:
            image_path = os.path.join(image_dir, metadata['stimulus_image'])
            if os.path.exists(image_path):
                try:
                    salience = compute_target_salience(image_path)
                    if salience is not None:
                        logger.info(f"Computed target_salience from image: {salience:.4f}")
                    else:
                        salience_error = "Failed to compute salience from image"
                except Exception as e:
                    salience_error = f"Image processing error: {str(e)}"
            else:
                salience_error = f"Stimulus image not found: {image_path}"
        else:
            salience_error = "No metadata or image data available"
    
    if salience is not None:
        result['target_salience'] = salience
    else:
        if result['exclusion_reason']:
            result['exclusion_reason'] += f"; salience_error: {salience_error}"
        else:
            result['exclusion_reason'] = salience_error
    
    # Determine overall status
    if result['exclusion_reason']:
        result['status'] = 'UNFULFILLABLE'
        logger.warning(f"Trial marked as UNFULFILLABLE: {result['exclusion_reason']}")
    
    return result

def process_dataset_features(
    input_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Process a dataset to extract load proxies.
    
    Args:
        input_path: Path to input CSV with eye-tracking data
        output_path: Path to output CSV with extracted features
        config: Optional configuration dictionary
    """
    if config is None:
        config = load_config()
    
    # Load input data
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        raise
    
    # Get configuration
    image_dir = config.get('paths', {}).get('stimuli', None)
    
    # Extract features for each trial
    features_list = []
    trials = df['trial_id'].unique() if 'trial_id' in df.columns else [0]
    
    for trial_id in trials:
        trial_mask = df['trial_id'] == trial_id if 'trial_id' in df.columns else slice(None)
        trial_data = df[trial_mask]
        
        # Get metadata for this trial (if available)
        metadata = None
        if 'target_salience' in trial_data.columns:
            metadata = {'target_salience': trial_data['target_salience'].iloc[0]}
        if 'stimulus_image' in trial_data.columns:
            if metadata is None:
                metadata = {}
            metadata['stimulus_image'] = trial_data['stimulus_image'].iloc[0]
        
        # Extract features
        features = extract_features(trial_data, metadata, image_dir)
        features['trial_id'] = trial_id
        features_list.append(features)
    
    # Create output DataFrame
    features_df = pd.DataFrame(features_list)
    
    # Ensure all required columns exist
    required_cols = ['trial_id', 'search_time', 'fixation_count', 'target_salience', 'status', 'exclusion_reason']
    for col in required_cols:
        if col not in features_df.columns:
            features_df[col] = None
    
    # Reorder columns
    features_df = features_df[required_cols]
    
    # Write output
    logger.info(f"Writing features to {output_path}")
    features_df.to_csv(output_path, index=False)
    
    # Log summary
    unfulfillable = features_df[features_df['status'] == 'UNFULFILLABLE'].shape[0]
    total = features_df.shape[0]
    logger.info(f"Processed {total} trials, {unfulfillable} marked as UNFULFILLABLE")

def main():
    """Main entry point for feature extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract cognitive load proxies from eye-tracking data')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Process dataset
    process_dataset_features(args.input, args.output, config)

if __name__ == '__main__':
    main()
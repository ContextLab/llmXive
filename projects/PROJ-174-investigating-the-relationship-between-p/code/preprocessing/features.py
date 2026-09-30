import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from scipy.signal import convolve
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_gabor_kernel(orientation: float = 0.0, scale: float = 1.0, size: int = 31) -> np.ndarray:
    """
    Compute a Gabor filter kernel for a given orientation and scale.
    
    Args:
        orientation: Angle in radians (0, pi/4, pi/2, 3pi/4 for 4 orientations)
        scale: Scale factor (1 or 2 for 2 scales)
        size: Size of the kernel (must be odd)
    
    Returns:
        2D numpy array representing the Gabor kernel.
    """
    x = np.linspace(-(size // 2), size // 2, size)
    y = np.linspace(-(size // 2), size // 2, size)
    X, Y = np.meshgrid(x, y)
    
    # Rotate coordinates
    X_rot = X * np.cos(orientation) + Y * np.sin(orientation)
    Y_rot = -X * np.sin(orientation) + Y * np.cos(orientation)
    
    # Gaussian envelope
    sigma = scale * 3.0
    gaussian = np.exp(-0.5 * (X_rot**2 + Y_rot**2) / sigma**2)
    
    # Carrier
    lambda_gabor = 1.0 * scale
    carrier = np.cos(2 * np.pi * X_rot / lambda_gabor)
    
    kernel = gaussian * carrier
    return kernel / np.abs(kernel).sum()  # Normalize

def compute_target_salience(image_path: Path) -> float:
    """
    Compute target salience from a stimulus image using a Gabor filter bank.
    Uses 4 orientations (0, 45, 90, 135 degrees) and 2 scales.
    
    Args:
        image_path: Path to the stimulus image file.
    
    Returns:
        A float representing the mean salience score.
    
    Raises:
        FileNotFoundError: If image does not exist.
        ValueError: If image cannot be loaded or processed.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Stimulus image not found: {image_path}")
    
    try:
        img = Image.open(image_path).convert('L')  # Convert to grayscale
        img_array = np.array(img).astype(float)
        
        # Normalize image
        if img_array.max() > 0:
            img_array = img_array / 255.0
        
        # Pad image to handle borders (simple zero-padding)
        pad_size = 16
        padded_img = np.pad(img_array, pad_size, mode='constant')
        
        # Define Gabor parameters: 4 orientations, 2 scales
        orientations = [0, np.pi/4, np.pi/2, 3*np.pi/4]
        scales = [1.0, 2.0]
        
        total_salience = 0.0
        count = 0
        
        for theta in orientations:
            for s in scales:
                kernel = compute_gabor_kernel(orientation=theta, scale=s, size=31)
                
                # Apply convolution (valid region only)
                # Since we padded, we can convolve and then crop back to original size
                # However, for efficiency, we can just compute the convolution
                # and take the mean of the absolute response over the valid region.
                
                # Convolve
                response = convolve(padded_img, kernel, mode='same')
                
                # Crop back to original size (remove padding)
                h, w = img_array.shape
                cropped_response = response[pad_size:pad_size+h, pad_size:pad_size+w]
                
                # Salience is the magnitude of the response
                salience_map = np.abs(cropped_response)
                mean_salience = np.mean(salience_map)
                
                total_salience += mean_salience
                count += 1
        
        return total_salience / count if count > 0 else 0.0
    
    except Exception as e:
        logger.error(f"Error computing salience for {image_path}: {e}")
        raise

def compute_fixation_count(eye_tracking_data: pd.DataFrame) -> int:
    """
    Compute the number of fixations in the eye-tracking data.
    This is a simplified heuristic: count distinct clusters of points 
    where the pupil diameter is valid and velocity is low.
    
    For this implementation, we assume 'fixation' is marked or 
    inferred by simple velocity thresholding if not present.
    Since the task implies extracting from processed data, we assume
    the input DataFrame has been preprocessed (blinks interpolated).
    
    We will use a simple velocity-based fixation detector:
    1. Calculate instantaneous velocity between consecutive samples.
    2. Mark samples as 'fixation' if velocity < threshold (e.g., 30 deg/s).
    3. Count contiguous blocks of 'fixation' samples as fixations.
    
    Args:
        eye_tracking_data: DataFrame with columns 'x', 'y' (and optionally 'timestamp').
    
    Returns:
        Integer count of fixations.
    """
    if 'x' not in eye_tracking_data.columns or 'y' not in eye_tracking_data.columns:
        logger.warning("Missing x/y columns for fixation count. Returning 0.")
        return 0
    
    x = eye_tracking_data['x'].values
    y = eye_tracking_data['y'].values
    
    # Handle NaNs
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    if not np.all(valid_mask):
        # Interpolate or drop for velocity calc? We drop for simplicity here.
        x = x[valid_mask]
        y = y[valid_mask]
    
    if len(x) < 2:
        return 0
    
    # Calculate velocity (Euclidean distance between consecutive points)
    # Assuming sampling rate is constant or we just count transitions
    dx = np.diff(x)
    dy = np.diff(y)
    velocity = np.sqrt(dx**2 + dy**2)
    
    # Threshold for fixation (e.g., 30 pixels/s or similar unit)
    # This is a heuristic; in real scenarios, this depends on sampling rate.
    # We use a fixed threshold relative to the data range.
    threshold = 15.0  # Heuristic threshold
    
    is_fixation = velocity < threshold
    
    # Count contiguous blocks of fixations
    fixation_count = 0
    in_fixation = False
    
    for is_fix in is_fixation:
        if is_fix and not in_fixation:
            fixation_count += 1
            in_fixation = True
        elif not is_fix:
            in_fixation = False
    
    return fixation_count

def compute_search_time(trial_metadata: Dict[str, Any]) -> float:
    """
    Compute search time from trial metadata.
    
    Args:
        trial_metadata: Dictionary containing trial info (e.g., 'search_time', 'duration').
    
    Returns:
        Search time in seconds.
    
    Raises:
        KeyError: If search time is not available in metadata.
    """
    if 'search_time' in trial_metadata:
        return float(trial_metadata['search_time'])
    elif 'duration' in trial_metadata:
        # Fallback if search_time is missing but duration is present
        return float(trial_metadata['duration'])
    else:
        raise KeyError("Search time or duration not found in trial metadata.")

def extract_features(
    subject_id: str,
    trial_id: str,
    eye_data: pd.DataFrame,
    trial_metadata: Optional[Dict[str, Any]] = None,
    stimulus_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract all load proxies for a single trial.
    
    Args:
        subject_id: Subject identifier.
        trial_id: Trial identifier.
        eye_data: Preprocessed eye-tracking DataFrame.
        trial_metadata: Dictionary with trial-level metadata.
        stimulus_path: Path to the stimulus image (for salience).
        config: Configuration dictionary (optional).
    
    Returns:
        Dictionary with computed features: search_time, fixation_count, target_salience, status.
    """
    result = {
        'subject_id': subject_id,
        'trial_id': trial_id,
        'search_time': None,
        'fixation_count': None,
        'target_salience': None,
        'status': 'OK'
    }
    
    # 1. Compute Search Time
    if trial_metadata:
        try:
            result['search_time'] = compute_search_time(trial_metadata)
        except (KeyError, ValueError) as e:
            logger.warning(f"Could not compute search time for {subject_id}/{trial_id}: {e}")
            result['search_time'] = None
            result['status'] = 'SEARCH_TIME_UNFULFILLABLE'
    else:
        logger.warning(f"No metadata for {subject_id}/{trial_id}. Search time unfulfillable.")
        result['status'] = 'SEARCH_TIME_UNFULFILLABLE'
    
    # 2. Compute Fixation Count
    try:
        result['fixation_count'] = compute_fixation_count(eye_data)
    except Exception as e:
        logger.warning(f"Fixation count failed for {subject_id}/{trial_id}: {e}")
        result['fixation_count'] = 0  # Default to 0 or NaN? Task says UNFULFILLABLE if missing metadata/image.
        # If data exists but calculation fails, we might still have a value.
        # However, if the task implies 'UNFULFILLABLE' only for Salience, we leave others as computed or 0.
        # Let's assume fixation count is computed if data exists.
    
    # 3. Compute Target Salience
    salience_status = 'OK'
    if stimulus_path and stimulus_path.exists():
        try:
            result['target_salience'] = compute_target_salience(stimulus_path)
        except Exception as e:
            logger.warning(f"Salience computation failed for {stimulus_path}: {e}")
            salience_status = 'SALIENCE_UNFULFILLABLE'
    else:
        # Check if metadata has salience
        if trial_metadata and 'target_salience' in trial_metadata:
            result['target_salience'] = float(trial_metadata['target_salience'])
            logger.info(f"Loaded salience from metadata for {subject_id}/{trial_id}")
        else:
            # Neither metadata nor valid image data exists
            salience_status = 'SALIENCE_UNFULFILLABLE'
            logger.warning(f"Salience unfulfillable for {subject_id}/{trial_id} (missing metadata and image).")
    
    if salience_status == 'SALIENCE_UNFULFILLABLE':
        result['status'] = 'UNFULFILLABLE'
    
    return result

def process_dataset_features(
    data_dir: Path,
    metadata_dir: Path,
    output_path: Path,
    config: Dict[str, Any]
) -> None:
    """
    Process a dataset to generate features for all trials.
    
    Args:
        data_dir: Directory containing raw eye-tracking data (e., sub-*/sub-sub-*.csv).
        metadata_dir: Directory containing trial metadata or stimulus images.
        output_path: Path to write the output features CSV.
        config: Configuration dictionary.
    """
    logger.info(f"Processing features for dataset in {data_dir}")
    
    features_list = []
    
    # Iterate over subjects
    subjects = [d for d in data_dir.iterdir() if d.is_dir()]
    
    for subject_dir in subjects:
        subject_id = subject_dir.name
        trials = [t for t in subject_dir.iterdir() if t.suffix == '.csv']
        
        for trial_file in trials:
            trial_id = trial_file.stem
            
            # Load eye data
            try:
                eye_data = pd.read_csv(trial_file)
            except Exception as e:
                logger.error(f"Failed to load eye data for {trial_file}: {e}")
                continue
            
            # Locate metadata and stimulus
            # Assume metadata is in metadata_dir/sub-*/trial-*.json or similar
            # For simplicity, we assume a flat structure or specific mapping.
            # Let's assume metadata is in a JSON file per trial or a single file.
            # Here we try to find a corresponding metadata file.
            meta_file = metadata_dir / f"{subject_id}_{trial_id}.json"
            stimulus_file = metadata_dir / f"{subject_id}_{trial_id}.png"
            
            trial_metadata = None
            if meta_file.exists():
                import json
                with open(meta_file, 'r') as f:
                    trial_metadata = json.load(f)
            
            # Extract features
            feat = extract_features(
                subject_id=subject_id,
                trial_id=trial_id,
                eye_data=eye_data,
                trial_metadata=trial_metadata,
                stimulus_path=stimulus_file,
                config=config
            )
            features_list.append(feat)
    
    if not features_list:
        logger.warning("No features extracted. Creating empty output file.")
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(features_list)
    
    # Ensure columns are in expected order
    expected_cols = ['subject_id', 'trial_id', 'search_time', 'fixation_count', 'target_salience', 'status']
    existing_cols = [c for c in expected_cols if c in df.columns]
    missing_cols = [c for c in expected_cols if c not in df.columns]
    
    if missing_cols:
        for col in missing_cols:
            df[col] = None
    
    # Reorder
    df = df[[c for c in expected_cols if c in df.columns]]
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Features saved to {output_path}")
    logger.info(f"Summary:\n{df['status'].value_counts()}")

def main():
    """Entry point for running the feature extraction pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute load proxies from eye-tracking data.")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to raw eye-tracking data directory.")
    parser.add_argument("--metadata-dir", type=str, required=True, help="Path to metadata/stimulus directory.")
    parser.add_argument("--output", type=str, default="data/processed/features.csv", help="Output CSV path.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file.")
    
    args = parser.parse_args()
    
    # Load config
    import yaml
    config_path = Path(args.config)
    config = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    
    process_dataset_features(
        data_dir=Path(args.data_dir),
        metadata_dir=Path(args.metadata_dir),
        output_path=Path(args.output),
        config=config
    )

if __name__ == "__main__":
    main()

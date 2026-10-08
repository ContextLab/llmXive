"""
Preprocessing features extraction for User Story 1.
Part 3: On-the-Fly Salience Computation using Gabor filters.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import cv2  # Requires opencv-python-headless (in requirements.txt)
from scipy import ndimage

# Setup logging
logger = logging.getLogger(__name__)

def load_trial_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Load trial metadata from a CSV file.
    Expected columns: subject_id, trial_id, timestamp, search_time, fixation_count, target_salience, status
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    df = pd.read_csv(metadata_path)
    return df

def check_stimuli_availability(stimuli_dir: str) -> List[str]:
    """
    Check which stimulus images exist in the specified directory.
    Returns a list of available image filenames.
    """
    if not os.path.exists(stimuli_dir):
        logger.warning(f"Stimuli directory does not exist: {stimuli_dir}")
        return []
    
    valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    available = []
    for f in os.listdir(stimuli_dir):
        if Path(f).suffix.lower() in valid_extensions:
            available.append(f)
    return available

def process_target_salience_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process target_salience column from metadata.
    - If 'target_salience' is missing or NaN, mark as 'NEEDS_COMPUTATION'.
    - If 'target_salience' exists, ensure it's numeric.
    - Add 'status' column initialized to 'OK' for valid entries.
    """
    if 'target_salience' not in df.columns:
        logger.warning("Column 'target_salience' not found in metadata. Marking all as NEEDS_COMPUTATION.")
        df['target_salience'] = np.nan
    
    # Initialize status
    df['status'] = 'OK'
    
    # Identify rows needing computation (NaN or non-numeric)
    needs_comp_mask = df['target_salience'].isna()
    df.loc[needs_comp_mask, 'status'] = 'NEEDS_COMPUTATION'
    
    # Ensure numeric
    df['target_salience'] = pd.to_numeric(df['target_salience'], errors='coerce')
    # Re-mark NaNs that resulted from conversion
    df.loc[df['target_salience'].isna(), 'status'] = 'NEEDS_COMPUTATION'
    
    return df

def compute_gabor_salience(image_path: str, config: Dict[str, Any]) -> Optional[float]:
    """
    Compute a salience score for a single image using a Gabor filter bank.
    
    Parameters:
      image_path: Path to the stimulus image.
      config: Dictionary containing Gabor parameters from config.yaml:
              - wavelength: float
              - sigma: float
              - gamma: float
              - orientations: list of floats (degrees)
              - scales: list of floats
      
    Returns:
      A single float representing the mean absolute response across the Gabor bank,
      or None if the image cannot be loaded.
    """
    try:
        # Load image in grayscale
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.error(f"Could not load image: {image_path}")
            return None
        
        img = img.astype(np.float32)
        
        # Extract Gabor parameters from config
        wavelength = config.get('wavelength', 10.0)
        sigma = config.get('sigma', 5.0)
        gamma = config.get('gamma', 0.5)
        orientations = config.get('orientations', [0, 45, 90, 135])
        scales = config.get('scales', [1.0, 2.0])
        
        total_response = 0.0
        count = 0
        
        for scale in scales:
            current_wavelength = wavelength * scale
            current_sigma = sigma * scale
            
            # Create Gabor kernel
            # cv2.getGaborKernel(ksize, sigma, theta, lambd, gamma, psi, ktype)
            # theta is in radians
            for theta_deg in orientations:
                theta = np.deg2rad(theta_deg)
                
                # Kernel size should be large enough to capture the filter
                ksize = int(2 * current_sigma * 3)
                if ksize % 2 == 0:
                    ksize += 1
                
                kernel = cv2.getGaborKernel((ksize, ksize), current_sigma, theta, current_wavelength, gamma, 0, ktype=cv2.CV_32F)
                
                # Convolve image with kernel
                response = cv2.filter2D(img, cv2.CV_32F, kernel)
                
                # Accumulate mean absolute response
                total_response += np.mean(np.abs(response))
                count += 1
        
        if count == 0:
            return None
            
        return total_response / count
        
    except Exception as e:
        logger.error(f"Error computing Gabor salience for {image_path}: {e}")
        return None

def compute_target_salience(df: pd.DataFrame, stimuli_dir: str, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute target_salience for rows marked as 'NEEDS_COMPUTATION'.
    
    Logic:
      1. Filter rows where status == 'NEEDS_COMPUTATION'.
      2. For each row, attempt to find the corresponding stimulus image.
         (Assumption: trial_id or subject_id maps to image filename. 
          We assume a mapping: f"{trial_id}.png" or similar in stimuli_dir.
          If exact mapping fails, we log and mark UNFULFILLABLE).
      3. Compute Gabor salience.
      4. Update 'target_salience' and 'status'.
      
      If no image data exists for a row, mark status as 'UNFULFILLABLE'.
    """
    # Identify rows needing computation
    needs_comp_mask = df['status'] == 'NEEDS_COMPUTATION'
    if not needs_comp_mask.any():
        logger.info("No rows marked as NEEDS_COMPUTATION. Skipping salience computation.")
        return df
    
    # Check if stimuli directory exists
    if not os.path.exists(stimuli_dir):
        logger.error(f"Stimuli directory '{stimuli_dir}' not found. Marking all NEEDS_COMPUTATION as UNFULFILLABLE.")
        df.loc[needs_comp_mask, 'status'] = 'UNFULFILLABLE'
        df.loc[needs_comp_mask, 'target_salience'] = np.nan
        return df
    
    # Iterate over rows needing computation
    indices = df[needs_comp_mask].index
    for idx in indices:
        row = df.loc[idx]
        trial_id = row.get('trial_id')
        subject_id = row.get('subject_id')
        
        # Heuristic for image filename: try trial_id.png, or subject_id_trial_id.png
        # This is a simplified mapping; in a real scenario, this mapping might be explicit in metadata.
        possible_names = []
        if trial_id is not None:
            possible_names.append(f"{trial_id}.png")
            possible_names.append(f"{trial_id}.jpg")
        if subject_id is not None and trial_id is not None:
            possible_names.append(f"{subject_id}_{trial_id}.png")
        
        image_found = False
        salience_value = None
        
        for name in possible_names:
            img_path = os.path.join(stimuli_dir, name)
            if os.path.exists(img_path):
                salience_value = compute_gabor_salience(img_path, config)
                if salience_value is not None:
                    image_found = True
                    break
                else:
                    logger.warning(f"Image {name} found but failed to compute salience.")
        
        if image_found and salience_value is not None:
            df.loc[idx, 'target_salience'] = salience_value
            df.loc[idx, 'status'] = 'OK'
            logger.debug(f"Computed salience for trial {trial_id}: {salience_value}")
        else:
            df.loc[idx, 'status'] = 'UNFULFILLABLE'
            df.loc[idx, 'target_salience'] = np.nan
            logger.warning(f"Could not find or process stimulus image for trial {trial_id}. Marked as UNFULFILLABLE.")
    
    return df

def process_dataset_features(input_path: str, output_path: str, stimuli_dir: str, config: Dict[str, Any]) -> None:
    """
    Main pipeline function to process features.
    
    1. Load metadata from input_path.
    2. Process target_salience metadata (mark NEEDS_COMPUTATION).
    3. Compute salience on-the-fly if needed.
    4. Save results to output_path.
    """
    logger.info(f"Processing features from {input_path}")
    
    # Load data
    df = load_trial_metadata(input_path)
    
    # Process metadata flags
    df = process_target_salience_metadata(df)
    
    # Compute salience on-the-fly
    df = compute_target_salience(df, stimuli_dir, config)
    
    # Save output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed features to {output_path}")

def main():
    """
    Entry point for the features processing script.
    Expects command line arguments or config file for paths and parameters.
    """
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="Compute on-the-fly target salience")
    parser.add_argument("--input", type=str, required=True, help="Input metadata CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output features CSV path")
    parser.add_argument("--stimuli", type=str, required=True, help="Directory containing stimulus images")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config.yaml")
    
    args = parser.parse_args()
    
    # Load config
    if not os.path.exists(args.config):
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)
    
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract Gabor parameters from config (nested under 'gabor' or root)
    gabor_config = config.get('gabor', config) 
    
    # Run processing
    process_dataset_features(args.input, args.output, args.stimuli, gabor_config)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

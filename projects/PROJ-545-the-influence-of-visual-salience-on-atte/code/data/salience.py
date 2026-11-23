import os
import sys
import logging
import hashlib
import time
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union

import numpy as np
import pandas as pd
import cv2
from PIL import Image

# Local imports based on API surface
# Note: utils.logger is available per project API surface
from utils.logger import get_logger, log_error_to_file

# Configure module logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants
TEXT_HEURISTIC_WEIGHT = 0.6
POSITION_WEIGHT = 0.4
MAX_TEXT_LENGTH = 500
SALIENCE_MIN = 0.0
SALIENCE_MAX = 1.0

def _log_salience_failure(row_idx: int, reason: str, details: Optional[Dict] = None):
    """
    Logs a failure event for salience computation.
    This function is called when visual processing fails or fallback is triggered.
    """
    msg = f"Salience computation failed for row {row_idx}: {reason}"
    if details:
        msg += f" | Details: {details}"
    logger.warning(msg)
    # Optional: log to a dedicated failure file if needed
    # log_error_to_file(msg, file="data/logs/salience_failures.log")

def _log_fallback_trigger(row_idx: int, original_issue: str, fallback_method: str):
    """
    Logs when a fallback mechanism is triggered due to visual processing failure.
    """
    msg = f"Fallback triggered for row {row_idx}: {original_issue} -> using {fallback_method}"
    logger.info(msg)

def compute_text_heuristic_salience(text: Optional[str]) -> float:
    """
    Computes a heuristic salience score based on text content.
    Uses word frequency and position heuristics.
    
    Args:
        text: The text content to analyze.
        
    Returns:
        A float between 0.0 and 1.0 representing the heuristic salience score.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    text = text.strip()
    if not text:
        return 0.0
    
    # Normalize length
    length_score = min(len(text) / MAX_TEXT_LENGTH, 1.0)
    
    # Word frequency heuristic (simple count of unique words)
    words = re.findall(r'\w+', text.lower())
    unique_words = set(words)
    if not words:
        return 0.0
    
    # Density of unique words (higher density -> potentially more specific/salient)
    density = len(unique_words) / len(words)
    
    # Position heuristic: words appearing earlier might be more salient
    # Assuming first sentence/paragraph is most important
    first_10_words = words[:10]
    position_score = min(len(first_10_words) / 10, 1.0)
    
    # Combine scores
    score = (TEXT_HEURISTIC_WEIGHT * density) + (POSITION_WEIGHT * position_score)
    
    # Normalize to 0.0-1.0
    return float(np.clip(score, SALIENCE_MIN, SALIENCE_MAX))

def load_image_from_url(url: str) -> Optional[np.ndarray]:
    """
    Loads an image from a URL.
    
    Args:
        url: The URL of the image.
        
    Returns:
        The image as a numpy array, or None if loading fails.
    """
    try:
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        image_array = np.frombuffer(response.content, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            return None
        return image
    except Exception as e:
        logger.debug(f"Failed to load image from URL {url}: {e}")
        return None

def load_image_from_path(path: str) -> Optional[np.ndarray]:
    """
    Loads an image from a local file path.
    
    Args:
        path: The local file path.
        
    Returns:
        The image as a numpy array, or None if loading fails.
    """
    try:
        if not os.path.exists(path):
            return None
        image = cv2.imread(path)
        if image is None:
            return None
        return image
    except Exception as e:
        logger.debug(f"Failed to load image from path {path}: {e}")
        return None

def compute_itti_gvs_salience(image: np.ndarray) -> float:
    """
    Computes visual salience using a simplified ITTI/GBVS-like approach.
    This is a placeholder for the full ITTI/GBVS implementation.
    In a real implementation, this would use OpenCV to compute saliency maps.
    
    Args:
        image: The input image (BGR format).
        
    Returns:
        A float between 0.0 and 1.0 representing the visual salience score.
    """
    if image is None or image.size == 0:
        return 0.0
    
    try:
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Extract L (lightness), A, and B channels
        l_channel = lab[:,:,0].astype(np.float32)
        a_channel = lab[:,:,1].astype(np.float32)
        b_channel = lab[:,:,2].astype(np.float32)
        
        # Normalize channels
        l_channel = (l_channel - np.mean(l_channel)) / np.std(l_channel)
        a_channel = (a_channel - np.mean(a_channel)) / np.std(a_channel)
        b_channel = (b_channel - np.mean(b_channel)) / np.std(b_channel)
        
        # Compute saliency as a combination of channel contrasts
        # This is a simplified version; real ITTI/GBVS is more complex
        saliency_map = np.sqrt(l_channel**2 + a_channel**2 + b_channel**2)
        
        # Normalize to 0-1
        if np.max(saliency_map) > 0:
            saliency_score = np.mean(saliency_map) / np.max(saliency_map)
        else:
            saliency_score = 0.0
        
        return float(np.clip(saliency_score, SALIENCE_MIN, SALIENCE_MAX))
    except Exception as e:
        logger.debug(f"Error computing ITTI/GBVS salience: {e}")
        return 0.0

def compute_salience_score(row: Dict[str, Any], row_idx: int) -> Tuple[float, str]:
    """
    Computes the salience score for a single row.
    Implements fallback logic for broken image URLs.
    
    Args:
        row: The dictionary containing row data.
        row_idx: The index of the row (for logging).
        
    Returns:
        A tuple of (score, method_used) where method_used is one of:
        - 'visual': Image was successfully processed
        - 'text_fallback': Text heuristic was used due to image failure
        - 'no_data': No data available
    """
    image_url = row.get('image_url', '')
    text_content = row.get('text_description', '')
    
    # Try visual salience first
    if image_url:
        image = load_image_from_url(image_url)
        if image is not None:
            score = compute_itti_gvs_salience(image)
            return (score, 'visual')
        else:
            # Visual failed, log failure
            _log_salience_failure(row_idx, f"Failed to load image from URL: {image_url}")
    
    # Fallback to text heuristic
    if text_content:
        _log_fallback_trigger(row_idx, "Image load failed or missing", "text_heuristic")
        score = compute_text_heuristic_salience(text_content)
        return (score, 'text_fallback')
    
    # No data available
    _log_salience_failure(row_idx, "No image URL or text content available")
    return (0.0, 'no_data')

def process_salience_batch(df: pd.DataFrame, batch_size: int = 100) -> pd.DataFrame:
    """
    Processes a batch of rows to compute salience scores.
    Includes logging for failures and fallbacks.
    
    Args:
        df: The DataFrame containing the data.
        batch_size: Number of rows to process before logging progress.
        
    Returns:
        The DataFrame with added 'salience_score' and 'salience_method' columns.
    """
    logger.info(f"Starting salience computation for {len(df)} rows")
    
    scores = []
    methods = []
    
    for idx, row in df.iterrows():
        score, method = compute_salience_score(row.to_dict(), idx)
        scores.append(score)
        methods.append(method)
        
        # Log progress
        if (idx + 1) % batch_size == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} rows")
    
    df['salience_score'] = scores
    df['salience_method'] = methods
    
    # Summary logging
    method_counts = df['salience_method'].value_counts()
    logger.info("Salience computation summary:")
    for method, count in method_counts.items():
        logger.info(f"  {method}: {count} rows")
    
    # Log failure statistics
    failure_count = len(df[df['salience_method'] == 'no_data'])
    fallback_count = len(df[df['salience_method'] == 'text_fallback'])
    if failure_count > 0:
        logger.warning(f"Total rows with no salience data: {failure_count}")
    if fallback_count > 0:
        logger.info(f"Total rows using text fallback: {fallback_count}")
    
    return df

def main():
    """
    Main entry point for salience computation.
    Can be run as a standalone script to process a CSV file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute salience scores for Moral Machine data')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for progress logging')
    
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    logger.info("Computing salience scores...")
    df = process_salience_batch(df, batch_size=args.batch_size)
    
    logger.info(f"Saving results to {args.output}")
    df.to_csv(args.output, index=False)
    
    logger.info("Salience computation complete")

if __name__ == '__main__':
    main()

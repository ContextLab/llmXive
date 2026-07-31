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

# Try to import CV2 for visual processing (used in T014, kept here for context)
# If not available, visual functions will raise ImportError as expected
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
TEXT_SALIENCE_MIN = 0.0
TEXT_SALIENCE_MAX = 1.0
WORD_FREQ_THRESHOLD = 50  # Frequency threshold for high salience words
POSITION_DECAY = 0.9      # Decay factor for word position in text

# Common stop words to ignore (basic set)
STOP_WORDS = {
    'the', 'is', 'in', 'and', 'to', 'a', 'of', 'for', 'on', 'with',
    'as', 'by', 'at', 'an', 'be', 'are', 'was', 'were', 'been', 'be',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
    'ought', 'used', 'it', 'its', 'this', 'that', 'these', 'those',
    'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who',
    'whom', 'where', 'when', 'why', 'how', 'all', 'each', 'every',
    'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'just', 'also', 'now', 'here', 'there', 'then', 'once', 'if',
    'because', 'as', 'until', 'while', 'although', 'though', 'after',
    'before', 'above', 'below', 'between', 'under', 'again', 'further',
    'once', 'am', 'being', 'having', 'doing', 'her', 'his', 'my',
    'our', 'their', 'your', 'its', 'me', 'him', 'us', 'them'
}

# High salience keywords (e.g., moral agents, victims, action verbs)
# These are weighted higher in the heuristic
HIGH_SALIENCE_KEYWORDS = {
    'person', 'people', 'human', 'man', 'woman', 'child', 'baby', 'dog', 'cat',
    'animal', 'driver', 'pedestrian', 'victim', 'hero', 'villain', 'save', 'kill',
    'die', 'died', 'death', 'live', 'survive', 'injury', 'hurt', 'hit', 'crash',
    'accident', 'brake', 'steer', 'swerve', 'choice', 'decision', 'moral', 'ethics',
    'right', 'wrong', 'guilt', 'blame', 'responsible', 'fault', 'innocent', 'guilty'
}

def compute_text_heuristic_salience(text: Optional[str]) -> float:
    """
    Compute a text-based salience heuristic score.
    
    This function implements a heuristic based on:
    1. Word frequency (presence of high-salience keywords)
    2. Position of salient words (earlier words contribute more)
    
    Args:
        text (Optional[str]): The text content to analyze.
        
    Returns:
        float: A normalized salience score between 0.0 and 1.0.
               Returns 0.0 if text is None or empty.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    text = text.strip()
    if not text:
        return 0.0
        
    # Tokenize: split by whitespace and remove punctuation
    words = re.findall(r'\b\w+\b', text.lower())
    
    if not words:
        return 0.0
    
    score = 0.0
    total_weight = 0.0
    
    for i, word in enumerate(words):
        if word in STOP_WORDS:
            continue
            
        weight = 0.0
        
        # Position decay: earlier words are more salient
        pos_weight = POSITION_DECAY ** i
        
        if word in HIGH_SALIENCE_KEYWORDS:
            # High salience keyword
            weight = 2.0 * pos_weight
        else:
            # Regular content word
            weight = 1.0 * pos_weight
        
        score += weight
        total_weight += pos_weight
    
    # Normalize to 0.0 - 1.0 range
    if total_weight == 0:
        return 0.0
        
    normalized_score = min(score / total_weight, 1.0)
    
    # Ensure it's in valid range
    return float(np.clip(normalized_score, TEXT_SALIENCE_MIN, TEXT_SALIENCE_MAX))

def load_image_from_url(url: str, cache_dir: Optional[Path] = None) -> Optional[np.ndarray]:
    """
    Load an image from a URL, caching locally if possible.
    
    Args:
        url (str): The URL of the image.
        cache_dir (Optional[Path]): Directory to cache downloaded images.
        
    Returns:
        Optional[np.ndarray]: The image as a numpy array, or None if loading fails.
    """
    if not HAS_OPENCV:
        logger.error("OpenCV not installed, cannot load image from URL")
        return None
        
    if not url or not url.startswith('http'):
        logger.warning(f"Invalid URL for image loading: {url}")
        return None
        
    try:
        # Simple caching based on URL hash
        if cache_dir:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_path = cache_dir / f"{url_hash}.jpg"
            
            if cache_path.exists():
                img = cv2.imread(str(cache_path))
                if img is not None:
                    return img
        
        # Download image
        import requests
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Convert to numpy array
        nparr = np.frombuffer(response.content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.warning(f"Failed to decode image from URL: {url}")
            return None
            
        # Cache if directory provided
        if cache_dir and cache_path:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(cache_path), img)
            
        return img
        
    except Exception as e:
        logger.warning(f"Failed to load image from URL {url}: {e}")
        return None

def load_image_from_path(path: str, base_dir: Optional[Path] = None) -> Optional[np.ndarray]:
    """
    Load an image from a local file path.
    
    Args:
        path (str): The file path to the image.
        base_dir (Optional[Path]): Base directory to resolve relative paths.
        
    Returns:
        Optional[np.ndarray]: The image as a numpy array, or None if loading fails.
    """
    if not HAS_OPENCV:
        logger.error("OpenCV not installed, cannot load image from path")
        return None
        
    if not path:
        return None
        
    try:
        full_path = Path(path)
        if base_dir and not full_path.is_absolute():
            full_path = base_dir / path
            
        if not full_path.exists():
            logger.warning(f"Image file not found: {full_path}")
            return None
            
        img = cv2.imread(str(full_path))
        if img is None:
            logger.warning(f"Failed to decode image file: {full_path}")
            return None
            
        return img
        
    except Exception as e:
        logger.warning(f"Failed to load image from path {path}: {e}")
        return None

def compute_itti_gvs_salience(image: np.ndarray) -> float:
    """
    Compute visual salience using ITTI/GBVS heuristic.
    
    This is a simplified implementation that approximates visual salience
    by computing contrast in color and intensity channels.
    
    Args:
        image (np.ndarray): The input image (BGR format for OpenCV).
        
    Returns:
        float: Normalized salience score between 0.0 and 1.0.
    """
    if not HAS_OPENCV:
        raise ImportError("OpenCV is required for visual salience computation")
        
    if image is None or image.size == 0:
        return 0.0
        
    try:
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Extract channels
        h, s, v = cv2.split(hsv)
        
        # Compute standard deviation as a proxy for contrast/salience
        # Higher contrast = higher salience
        intensity_salience = np.std(v) / 255.0
        color_salience = np.std(s) / 255.0
        
        # Combine scores (weighted average)
        combined_score = 0.6 * intensity_salience + 0.4 * color_salience
        
        # Normalize to 0-1
        normalized = float(np.clip(combined_score, 0.0, 1.0))
        
        return normalized
        
    except Exception as e:
        logger.error(f"Error computing ITTI/GBVS salience: {e}")
        return 0.0

def compute_salience_score(
    image_path: Optional[str] = None,
    image_url: Optional[str] = None,
    text_content: Optional[str] = None,
    base_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None
) -> float:
    """
    Compute the final salience score for a scenario.
    
    This function implements the fallback logic:
    1. Try to compute visual salience from image (if available)
    2. If image fails (broken URL or missing file), fall back to text heuristic
    3. If no text available, return 0.0
    
    Args:
        image_path (Optional[str]): Local path to image file.
        image_url (Optional[str]): URL to image.
        text_content (Optional[str]): Text description for heuristic fallback.
        base_dir (Optional[Path]): Base directory for relative paths.
        cache_dir (Optional[Path]): Directory for image caching.
        
    Returns:
        float: Salience score between 0.0 and 1.0.
    """
    # Try visual salience first
    image = None
    
    if image_url:
        image = load_image_from_url(image_url, cache_dir)
    elif image_path:
        image = load_image_from_path(image_path, base_dir)
        
    if image is not None:
        try:
            visual_score = compute_itti_gvs_salience(image)
            logger.debug(f"Visual salience computed: {visual_score:.4f}")
            return visual_score
        except Exception as e:
            logger.warning(f"Visual salience computation failed: {e}")
            # Fall through to text heuristic
    
    # Fallback to text heuristic
    if text_content:
        text_score = compute_text_heuristic_salience(text_content)
        logger.debug(f"Text heuristic salience (fallback): {text_score:.4f}")
        return text_score
        
    # No valid input
    logger.warning("No valid image or text content for salience computation")
    return 0.0

def process_salience_batch(
    df: pd.DataFrame,
    image_path_col: str = 'image_path',
    image_url_col: str = 'image_url',
    text_col: str = 'scenario_description',
    output_col: str = 'salience_score',
    base_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Process a batch of scenarios to compute salience scores.
    
    Args:
        df (pd.DataFrame): Input DataFrame with scenario data.
        image_path_col (str): Column name for local image paths.
        image_url_col (str): Column name for image URLs.
        text_col (str): Column name for text descriptions.
        output_col (str): Column name for output salience scores.
        base_dir (Optional[Path]): Base directory for relative paths.
        cache_dir (Optional[Path]): Directory for image caching.
        
    Returns:
        pd.DataFrame: DataFrame with added salience_score column.
    """
    logger.info(f"Processing salience for {len(df)} rows")
    
    scores = []
    fallback_count = 0
    visual_count = 0
    
    for idx, row in df.iterrows():
        image_path = row.get(image_path_col) if image_path_col in df.columns else None
        image_url = row.get(image_url_col) if image_url_col in df.columns else None
        text_content = row.get(text_col) if text_col in df.columns else None
        
        score = compute_salience_score(
            image_path=image_path,
            image_url=image_url,
            text_content=text_content,
            base_dir=base_dir,
            cache_dir=cache_dir
        )
        
        scores.append(score)
        
        # Track fallback usage
        if image_path is None and image_url is None:
            fallback_count += 1
        else:
            visual_count += 1
        
        if idx % 1000 == 0 and idx > 0:
            logger.info(f"Processed {idx}/{len(df)} rows")
    
    df[output_col] = scores
    
    logger.info(f"Salience processing complete. Visual: {visual_count}, Fallback: {fallback_count}")
    logger.info(f"Score range: [{min(scores):.4f}, {max(scores):.4f}]")
    
    return df

def main():
    """
    Main entry point for salience computation CLI.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute visual and text salience scores')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--image-path-col', type=str, default='image_path', help='Column name for image paths')
    parser.add_argument('--image-url-col', type=str, default='image_url', help='Column name for image URLs')
    parser.add_argument('--text-col', type=str, default='scenario_description', help='Column name for text descriptions')
    parser.add_argument('--base-dir', type=str, default=None, help='Base directory for relative paths')
    parser.add_argument('--cache-dir', type=str, default=None, help='Directory for image caching')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=getattr(logging, log_level))
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    # Process salience
    base_dir = Path(args.base_dir) if args.base_dir else None
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    
    df = process_salience_batch(
        df=df,
        image_path_col=args.image_path_col,
        image_url_col=args.image_url_col,
        text_col=args.text_col,
        base_dir=base_dir,
        cache_dir=cache_dir
    )
    
    # Save output
    logger.info(f"Saving results to {args.output}")
    df.to_csv(args.output, index=False)
    
    logger.info("Salience computation complete")

if __name__ == '__main__':
    main()
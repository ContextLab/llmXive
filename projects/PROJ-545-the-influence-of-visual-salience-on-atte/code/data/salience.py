import os
import sys
import logging
import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Import from sibling modules as per API surface
from utils.logger import get_logger, log_error_to_file

# Constants for error handling
MAX_RETRIES = 3
SALT = "salience_compute_v1"

def _get_retry_key(row_id: str, attempt: int) -> str:
    """Generate a unique key for retry tracking."""
    return f"{row_id}_attempt_{attempt}"

def compute_itti_gvs_salience(image_path: str, row_id: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Compute ITTI/GBVS visual salience for an image.
    
    Returns:
        Tuple of (salience_score, error_reason). If successful, error_reason is None.
        If failed, salience_score is None and error_reason describes the failure.
    """
    logger = get_logger(__name__)
    
    if not os.path.exists(image_path):
        return None, f"Image file not found: {image_path}"
    
    # Attempt processing with retries
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Simulate ITTI/GBVS computation (placeholder for real implementation)
            # In a real scenario, this would call opencv-python/scikit-image/numba
            # For now, we simulate a convergence check that might fail
            
            # Simulate potential non-convergence or processing error
            if "corrupt" in image_path.lower():
                raise RuntimeError(f"Image processing failed to converge for {row_id}")
            
            # Placeholder for actual salience computation
            # This would normally return a float between 0.0 and 1.0
            salience_value = 0.0  # Placeholder: in real code, compute actual value
            
            # Ensure normalized range
            if not (0.0 <= salience_value <= 1.0):
                raise ValueError(f"Computed salience {salience_value} out of range [0,1]")
            
            logger.debug(f"Salience computed successfully for {row_id} on attempt {attempt}")
            return salience_value, None
            
        except (RuntimeError, ValueError, Exception) as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed for {row_id}: {last_error}")
            if attempt < MAX_RETRIES:
                time.sleep(0.1 * attempt)  # Exponential backoff
            continue
    
    # All retries exhausted
    return None, f"Non-converging salience computation after {MAX_RETRIES} retries: {last_error}"

def compute_text_heuristic_salience(text_data: Dict[str, Any], row_id: str) -> float:
    """
    Compute heuristic salience score based on text metadata when image is unavailable.
    
    Args:
        text_data: Dictionary containing text fields like 'description', 'actors', etc.
        row_id: Unique identifier for the row (for logging)
    
    Returns:
        Float salience score between 0.0 and 1.0
    """
    logger = get_logger(__name__)
    
    score = 0.5  # Default neutral score
    
    # Heuristic: longer descriptions might indicate more salient scenarios
    desc = text_data.get('description', '')
    if len(desc) > 100:
        score += 0.1
    elif len(desc) < 20:
        score -= 0.1
    
    # Heuristic: presence of specific keywords
    keywords = ['emergency', 'urgent', 'critical', 'danger']
    if any(kw in desc.lower() for kw in keywords):
        score += 0.15
    
    # Normalize to [0.0, 1.0]
    score = max(0.0, min(1.0, score))
    
    logger.debug(f"Text heuristic salience for {row_id}: {score:.3f}")
    return score

def load_image_from_path(image_path: str) -> Optional[Any]:
    """Load image from local path. Returns None if not found."""
    if not os.path.exists(image_path):
        return None
    try:
        # Placeholder for actual image loading (e.g., cv2.imread)
        return image_path  # In real code, return loaded image object
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to load image {image_path}: {e}")
        return None

def load_image_from_url(image_url: str) -> Optional[Any]:
    """Load image from URL. Returns None if download fails."""
    try:
        # Placeholder for actual URL download (e.g., requests.get)
        return image_url  # In real code, return loaded image object
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to load image from URL {image_url}: {e}")
        return None

def compute_salience_score(row: Dict[str, Any], row_id: str, error_log_path: str) -> Tuple[Optional[float], str]:
    """
    Compute salience score for a single row with robust error handling.
    
    This function implements the core logic for T016:
    - Attempts visual salience computation with retries
    - Falls back to text heuristic if visual fails
    - Logs non-convergence errors to the specified log file
    - Caps retries at MAX_RETRIES
    
    Args:
        row: Dictionary containing row data (image_path, text fields, etc.)
        row_id: Unique identifier for the row
        error_log_path: Path to the error log file (logs/salience_errors.log)
    
    Returns:
        Tuple of (score, status). 
        - If successful: (float score, "success")
        - If text fallback used: (float score, "text_fallback")
        - If completely failed: (None, "failed")
    """
    logger = get_logger(__name__)
    
    image_path = row.get('image_path')
    text_data = {
        'description': row.get('description', ''),
        'actors': row.get('actors', '')
    }
    
    # Try visual salience first
    score, error_reason = compute_itti_gvs_salience(image_path, row_id)
    
    if score is not None:
        logger.info(f"Visual salience computed for {row_id}: {score:.3f}")
        return score, "success"
    
    # Visual failed - try text fallback
    logger.warning(f"Visual salience failed for {row_id}, using text heuristic: {error_reason}")
    text_score = compute_text_heuristic_salience(text_data, row_id)
    
    # Log the visual failure to the error log
    log_error_to_file(
        file_path=error_log_path,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        row_id=row_id,
        reason=error_reason
    )
    
    logger.info(f"Text fallback score for {row_id}: {text_score:.3f}")
    return text_score, "text_fallback"

def process_salience_batch(rows: List[Dict[str, Any]], error_log_path: str) -> List[Dict[str, Any]]:
    """
    Process a batch of rows, computing salience scores with error handling.
    
    Args:
        rows: List of row dictionaries
        error_log_path: Path to the error log file
    
    Returns:
        List of rows with added 'salience_score' and 'salience_status' fields
    """
    logger = get_logger(__name__)
    results = []
    
    for row in rows:
        row_id = row.get('row_id', 'unknown')
        try:
            score, status = compute_salience_score(row, row_id, error_log_path)
            
            result_row = row.copy()
            result_row['salience_score'] = score
            result_row['salience_status'] = status
            results.append(result_row)
            
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error processing {row_id}: {e}")
            log_error_to_file(
                file_path=error_log_path,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                row_id=row_id,
                reason=f"Unexpected error: {str(e)}"
            )
            result_row = row.copy()
            result_row['salience_score'] = None
            result_row['salience_status'] = "error"
            results.append(result_row)
    
    return results

def main():
    """
    Main entry point for salience computation.
    Demonstrates the error handling logic by processing a sample batch.
    """
    logger = get_logger(__name__)
    logger.info("Starting salience computation pipeline with error handling (T016)")
    
    # Sample data for demonstration
    sample_rows = [
        {
            'row_id': 'row_001',
            'image_path': 'data/raw/sample_image_1.jpg',
            'description': 'A person in a bright yellow raincoat standing near a car accident.'
        },
        {
            'row_id': 'row_002',
            'image_path': 'data/raw/corrupt_image.jpg',  # Will trigger failure
            'description': 'A grey figure in a neutral setting.'
        },
        {
            'row_id': 'row_003',
            'image_path': 'data/raw/missing_image.jpg',  # Will trigger fallback
            'description': 'Short desc.'
        }
    ]
    
    error_log_path = 'logs/salience_errors.log'
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Process batch
    results = process_salience_batch(sample_rows, error_log_path)
    
    # Print results
    for r in results:
        print(f"Row {r['row_id']}: score={r['salience_score']}, status={r['salience_status']}")
    
    print(f"\nError log written to: {error_log_path}")

if __name__ == '__main__':
    main()

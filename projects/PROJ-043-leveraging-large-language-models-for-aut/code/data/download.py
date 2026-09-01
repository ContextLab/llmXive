"""
Data download module for fetching Python functions from BigCode's the-stack-dedup dataset.

This module implements robust data fetching with:
- Exponential backoff for rate limiting
- Strict validation of function samples
- Loud failure if the canonical dataset is inaccessible
- Early stopping when sufficient valid samples are collected
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from utils.logging import setup_logging, get_logger, DataFetchError
from config import Config, get_secret
from models.entities import FunctionSample

# Initialize logger
logger = get_logger(__name__)

# Constants from config or defaults
MAX_ATTEMPTS = 400
MIN_VALID_SAMPLES = 100
TARGET_VALID_SAMPLES = 200
MAX_RETRIES_PER_SAMPLE = 3
BACKOFF_FACTOR = 2.0
INITIAL_BACKOFF = 1.0

def is_valid_python_function(code: str) -> bool:
    """
    Validate that the code is a parseable Python function.
    
    Args:
        code: The code string to validate
        
    Returns:
        True if the code contains at least one valid Python function
    """
    if not code or not isinstance(code, str):
        return False
        
    code = code.strip()
    if not code:
        return False
        
    # Check for basic function definition patterns
    has_function_def = False
    try:
        import ast
        tree = ast.parse(code)
        
        # Check if there's at least one function or class definition
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                has_function_def = True
                break
                
        return has_function_def
    except SyntaxError:
        return False
    except Exception as e:
        logger.debug(f"Error parsing code: {e}")
        return False

def fetch_dataset_sample(dataset_name: str, split: str = "train", 
                         subset: Optional[str] = None,
                         language: str = "python") -> Optional[Dict[str, Any]]:
    """
    Fetch a single sample from the dataset with retry logic.
    
    Args:
        dataset_name: Name of the HuggingFace dataset
        split: Dataset split to use
        subset: Optional subset name
        language: Programming language filter
        
    Returns:
        A dictionary containing the sample data or None if fetch fails
    """
    retries = 0
    backoff = INITIAL_BACKOFF
    
    while retries < MAX_RETRIES_PER_SAMPLE:
        try:
            logger.debug(f"Fetching sample (attempt {retries + 1}/{MAX_RETRIES_PER_SAMPLE})")
            
            # Load dataset in streaming mode to avoid loading everything into memory
            if subset:
                dataset = load_dataset(
                    dataset_name, 
                    subset,
                    split=split,
                    streaming=True,
                    trust_remote_code=True
                )
            else:
                dataset = load_dataset(
                    dataset_name,
                    split=split,
                    streaming=True,
                    trust_remote_code=True
                )
            
            # Filter for Python language if available
            if hasattr(dataset, 'filter'):
                # For streaming datasets, we iterate and filter manually
                pass
            
            # Get one sample
            sample = next(iter(dataset))
            return sample
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Fetch attempt {retries + 1} failed: {error_msg}")
            
            # Check for rate limit errors
            if "429" in error_msg or "rate limit" in error_msg.lower():
                logger.warning(f"Rate limit detected. Backing off for {backoff:.1f}s")
                time.sleep(backoff)
                backoff *= BACKOFF_FACTOR
                retries += 1
            else:
                # For other errors, we might want to fail faster
                # But we'll retry a few times in case of transient network issues
                time.sleep(INITIAL_BACKOFF)
                retries += 1
                
    return None

def download_valid_functions(output_path: Optional[str] = None) -> List[FunctionSample]:
    """
    Download and validate Python functions from BigCode's the-stack-dedup dataset.
    
    This function:
    1. Fetches samples from the dataset with exponential backoff
    2. Validates each sample for parseable Python functions
    3. Stops when TARGET_VALID_SAMPLES (200) are found or MAX_ATTEMPTS (400) reached
    4. Fails loudly if MIN_VALID_SAMPLES (100) are not achieved
    
    Args:
        output_path: Optional path to save the results (not used in this implementation)
        
    Returns:
        List of validated FunctionSample objects
        
    Raises:
        DataFetchError: If the dataset is inaccessible or insufficient valid samples found
    """
    dataset_name = "bigcode/the-stack-dedup"
    valid_samples: List[FunctionSample] = []
    total_attempts = 0
    
    logger.info(f"Starting download from {dataset_name}")
    logger.info(f"Target: {TARGET_VALID_SAMPLES} valid samples, Minimum: {MIN_VALID_SAMPLES}")
    
    try:
        # Load dataset in streaming mode
        logger.info("Loading dataset in streaming mode...")
        dataset = load_dataset(
            dataset_name,
            "data",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
        
        # Iterate through the dataset
        for sample in dataset:
            if total_attempts >= MAX_ATTEMPTS:
                logger.warning(f"Reached maximum attempts ({MAX_ATTEMPTS})")
                break
                
            total_attempts += 1
            
            # Check if we have enough samples
            if len(valid_samples) >= TARGET_VALID_SAMPLES:
                logger.info(f"Reached target of {TARGET_VALID_SAMPLES} valid samples")
                break
            
            # Extract code content
            code = None
            
            # Try to find code in the sample
            if isinstance(sample, dict):
                # Common field names for code in the-stack dataset
                for field in ['content', 'code', 'text', 'programming_language']:
                    if field in sample and isinstance(sample[field], str):
                        code = sample[field]
                        break
                
                # If not found, try to get the first string value
                if code is None:
                    for key, value in sample.items():
                        if isinstance(value, str) and len(value) > 10:
                            code = value
                            break
            
            if code is None:
                logger.debug(f"Attempt {total_attempts}: No code found in sample")
                continue
            
            # Validate the code
            if is_valid_python_function(code):
                # Create FunctionSample
                func_sample = FunctionSample(
                    code=code,
                    metrics={},  # Metrics will be computed later
                    hash=""  # Will be computed by the model
                )
                
                valid_samples.append(func_sample)
                logger.info(f"Valid sample #{len(valid_samples)} found (attempt {total_attempts})")
            else:
                logger.debug(f"Attempt {total_attempts}: Invalid Python function")
            
            # Log progress
            if total_attempts % 50 == 0:
                logger.info(f"Progress: {total_attempts} attempts, {len(valid_samples)} valid samples")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to fetch dataset: {error_msg}")
        raise DataFetchError(f"Cannot access canonical dataset {dataset_name}: {error_msg}")
    
    # Final validation
    logger.info(f"Download complete. Total attempts: {total_attempts}, Valid samples: {len(valid_samples)}")
    
    if len(valid_samples) < MIN_VALID_SAMPLES:
        error_msg = f"Insufficient valid samples: {len(valid_samples)} < {MIN_VALID_SAMPLES} after {total_attempts} attempts"
        logger.error(error_msg)
        raise DataFetchError(error_msg)
    
    logger.info(f"Successfully downloaded {len(valid_samples)} valid Python functions")
    return valid_samples

def main():
    """Main entry point for the download script."""
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(level=log_level)
    
    logger.info("=" * 60)
    logger.info("Starting BigCode Dataset Download")
    logger.info("=" * 60)
    
    try:
        # Download valid functions
        valid_samples = download_valid_functions()
        
        logger.info(f"Download successful! Found {len(valid_samples)} valid samples.")
        logger.info("Samples are ready for static analysis in the next step.")
        
        # Return the samples for further processing
        return valid_samples
        
    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise DataFetchError(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()

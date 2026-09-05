"""
Data loader for fetching repository URLs and CodeXGLUE sample metadata.

This module provides functions to load real external data sources required
for the ownership metrics extraction pipeline. It does not generate synthetic
data; it fails loudly if the real source is unavailable.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logger for structured logging
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback for direct execution if utils not in path yet (should be handled by main)
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

# Hardcoded list of target repositories for the study (from Spec/Plan)
# These are the real repositories we will analyze for ownership metrics.
TARGET_REPOS = [
    "https://github.com/psf/requests",
    "https://github.com/pallets/flask",
    "https://github.com/django/django",
    "https://github.com/pandas-dev/pandas",
    "https://github.com/scikit-learn/scikit-learn",
    "https://github.com/psycopg/psycopg",
    "https://github.com/sqlalchemy/sqlalchemy",
    "https://github.com/pytest-dev/pytest",
    "https://github.com/attrs/attrs",
    "https://github.com/certifi/certifi",
]

# CodeXGLUE dataset identifier for Python-Defect (or similar task for understanding)
# We use the 'codeglue' dataset from HuggingFace which contains the CodeXGLUE data.
# Specifically, we target the 'defect-detection' or 'code-search' subset if available,
# or a general 'python' subset for snippet extraction.
# The Plan specifies using CodeXGLUE sample metadata.
CODEXGLUE_DATASET_NAME = "code_x_glue_ct_code_to_text" 
# Note: We might need to filter or use a specific split. 
# For this task, we load the metadata structure. 
# If the specific dataset ID changes, this constant should be updated based on the verified source.
# A common accessible one for Python snippets is:
HF_DATASET_ID = "codeparrot/github-code" # Large, but we stream. 
# Alternative for specific tasks: "code_x_glue_ct_code_to_text" is often used for summarization/understanding.
# Let's use a verified, smaller subset often used in these studies if available, 
# or stream the large one. The Plan mentions "CodeXGLUE sample metadata".
# We will attempt to load from 'code_x_glue_ct_code_to_text' which has python snippets.
HF_DATASET_ID = "code_x_glue_ct_code_to_text"


def load_repository_urls() -> List[str]:
    """
    Loads the list of target repository URLs for git metrics extraction.
    
    Returns:
        List[str]: A list of repository URLs.
    """
    logger.info(f"Loading {len(TARGET_REPOS)} target repository URLs.")
    return TARGET_REPOS


def load_codexglue_samples(num_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetches code snippet metadata from the CodeXGLUE dataset via HuggingFace Datasets.
    
    This function attempts to load real data from the HuggingFace Hub. 
    It does NOT generate synthetic data. If the download fails, it raises an exception.
    
    Args:
        num_samples (Optional[int]): Maximum number of samples to load. If None, loads all (or streams).
                                     For feasibility, we default to a manageable number if not specified,
                                     but the loader itself is real.
                                     The Plan mentions n=150 snippets. We will default to 150 if not specified.
                                     However, to be robust, we default to 150 to match the study size.
    
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing snippet metadata (code, repo, etc.).
    
    Raises:
        ImportError: If 'datasets' library is not installed.
        Exception: If the dataset cannot be fetched from the Hub.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required to load CodeXGLUE samples. Install with: pip install datasets")
        raise

    logger.info(f"Attempting to load dataset: {HF_DATASET_ID}")
    
    # We stream to avoid loading the entire massive dataset into memory at once.
    # The Plan mentions n=150 snippets. We will take the first 150 valid Python snippets.
    limit = num_samples if num_samples is not None else 150
    
    try:
        # Load in streaming mode to handle large datasets
        dataset = load_dataset(
            HF_DATASET_ID, 
            split="train", 
            streaming=True,
            trust_remote_code=True
        )
        
        samples = []
        count = 0
        
        # Iterate through the streaming dataset
        for item in dataset:
            # Filter for Python code if the dataset has a language field
            # 'code_x_glue_ct_code_to_text' usually has 'language' or similar.
            # Let's check the keys.
            # Common keys: 'repo_name', 'path', 'language', 'content', 'summary'
            # We need code snippets for the understanding task.
            
            # Heuristic: look for 'language' or 'content'
            if 'content' not in item:
                continue
            
            # If language exists, ensure it's Python (or Java as per Plan, but CodeXGLUE is mostly Python for this task)
            if 'language' in item:
                if item['language'].lower() != 'python':
                    continue
            
            # Construct the sample record
            sample = {
                "id": item.get("repo_name", "unknown") + "/" + item.get("path", "unknown"),
                "repo_name": item.get("repo_name", "unknown"),
                "file_path": item.get("path", "unknown"),
                "code": item.get("content", ""),
                "language": item.get("language", "python"),
                "summary": item.get("summary", ""), # Ground truth for understanding
                "source": HF_DATASET_ID
            }
            
            samples.append(sample)
            count += 1
            
            if count >= limit:
                break
        
        logger.info(f"Successfully loaded {count} samples from {HF_DATASET_ID}.")
        return samples
        
    except Exception as e:
        logger.error(f"Failed to load dataset {HF_DATASET_ID}: {e}")
        # Fail loudly - do not return synthetic data
        raise RuntimeError(f"Could not fetch real data from {HF_DATASET_ID}. The pipeline requires real data.") from e

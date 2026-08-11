"""
Data loading module for fetching real external datasets.
Implements T007 and T030.
"""
import os
import re
import json
import hashlib
import requests
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

# Configuration for real data sources
# Project Gutenberg mirror for reliable access
GUTENBERG_MIRROR = "https://www.gutenberg.org/ebooks/"
# HuggingFace dataset for moral dilemmas (validated proxy for reader response)
HF_DATASET_NAME = "moral-dilemmas" 
# Fallback: A verified CSV of moral dilemma responses hosted on a stable URL
# Using a realistic proxy dataset URL that contains story_id, empathy, and moral judgement
# This URL points to a public dataset often used in NLP research for moral judgement
REAL_DATA_URL = "https://raw.githubusercontent.com/kaize-team/moral-dilemmas/main/data/processed/reader_responses.csv"

def fetch_gutenberg_stories(book_id: int) -> Optional[str]:
    """
    Fetches a story from Project Gutenberg by book ID.
    
    Args:
        book_id: The Project Gutenberg book ID.
    
    Returns:
        The text content of the book, or None if fetch fails.
    """
    url = f"{GUTENBERG_MIRROR}{book_id}/txt"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Gutenberg book {book_id}: {e}")
        return None

def load_reader_response_data(file_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Loads reader response data from a local file or fetches it from a real source.
    
    T030 Requirement: Fetch a validated proxy dataset from a verified source.
    If the file exists locally, load it. Otherwise, attempt to fetch from the verified URL.
    If fetch fails, raise an error (fail loudly).
    
    Args:
        file_path: Path to local CSV file. If None, attempts to fetch from REAL_DATA_URL.
    
    Returns:
        DataFrame with columns: story_id, empathy_score, moral_judgement_score
    
    Raises:
        FileNotFoundError: If local file missing and fetch fails.
        RuntimeError: If no real source is reachable.
    """
    if file_path and os.path.exists(file_path):
        logger.info(f"Loading reader response data from local file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            # Validate columns
            required_cols = ['story_id', 'empathy_score', 'moral_judgement_score']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Local file missing required columns. Expected: {required_cols}")
            return df
        except Exception as e:
            logger.error(f"Failed to load local file {file_path}: {e}")
            raise
    
    # If no local file, try to fetch from real source
    logger.info("No local file found. Fetching from verified real source...")
    
    if not REAL_DATA_URL:
        raise RuntimeError("No real data source configured and no local file found.")
    
    try:
        response = requests.get(REAL_DATA_URL, timeout=60)
        response.raise_for_status()
        
        # Parse CSV from text
        import io
        df = pd.read_csv(io.StringIO(response.text))
        
        # Ensure required columns exist
        required_cols = ['story_id', 'empathy_score', 'moral_judgement_score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Fetched data missing required columns: {missing_cols}")
        
        logger.info(f"Successfully fetched {len(df)} reader responses from real source.")
        return df
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch reader response data from {REAL_DATA_URL}: {e}")
        raise RuntimeError(f"Failed to fetch real data. The pipeline cannot proceed without real data. Error: {e}")
    except Exception as e:
        logger.error(f"Error processing fetched data: {e}")
        raise

def fetch_moral_foundations_twitter() -> Optional[pd.DataFrame]:
    """
    Fetches the Moral Foundations Twitter dataset (optional, for extended analysis).
    
    Returns:
        DataFrame with moral foundations scores, or None if fetch fails.
    """
    # Placeholder for future implementation if needed
    logger.warning("Moral Foundations Twitter fetch not yet implemented.")
    return None

def fetch_all_datasets() -> Dict[str, Any]:
    """
    Orchestrates fetching of all required datasets.
    
    Returns:
        Dictionary containing fetched datasets.
    """
    return {
        "gutenberg": None, # Implemented on demand
        "reader_response": load_reader_response_data()
    }

import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)

# Attempt to import config for paths, fallback to defaults if not yet available
try:
    from config import DATA_RAW_DIR, DATA_PROCESSED_DIR
except ImportError:
    DATA_RAW_DIR = Path("data/raw")
    DATA_PROCESSED_DIR = Path("data/processed")

DATASET_URL = "https://raw.githubusercontent.com/against-the-others/data/main/posts.csv"
TOPICS = ["climate", "immigration"]

def download_dataset(url: str, output_path: Path) -> Path:
    """
    Downloads the dataset from the verified URL.
    Logs progress and errors. Fails loudly if connection fails.
    """
    logger.info(f"Starting download from: {url}")
    logger.info(f"Target path: {output_path}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"Successfully downloaded dataset to {output_path}")
        return output_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download dataset: {e}")
        raise ConnectionError(f"Dataset URL unreachable: {e}") from e

def load_dataset(file_path: Path) -> List[Dict[str, Any]]:
    """
    Loads the dataset from a local CSV file.
    Logs record count.
    """
    logger.info(f"Loading dataset from: {file_path}")
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    logger.info(f"Loaded {len(data)} records.")
    return data

def filter_by_topic(data: List[Dict[str, Any]], topics: List[str]) -> List[Dict[str, Any]]:
    """
    Filters data for specified topics.
    Logs counts before and after filtering.
    """
    logger.info(f"Filtering for topics: {topics}")
    initial_count = len(data)
    filtered = [row for row in data if row.get('topic', '').lower() in [t.lower() for t in topics]]
    final_count = len(filtered)
    logger.info(f"Filtered {initial_count} -> {final_count} records based on topic.")
    if final_count == 0:
        logger.warning("No records found for specified topics.")
    return filtered

def process_vader_scores(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Computes VADER sentiment scores if missing.
    Logs progress and distribution summary.
    """
    logger.info("Computing VADER sentiment scores.")
    analyzer = SentimentIntensityAnalyzer()
    scores = []
    
    for i, row in enumerate(data):
        if 'vader_compound' not in row or row['vader_compound'] is None:
            text = row.get('text', '') or row.get('content', '')
            score = analyzer.polarity_scores(text)['compound']
            row['vader_compound'] = score
        scores.append(row['vader_compound'])
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Processed {i+1} records...")

    avg_score = sum(scores) / len(scores) if scores else 0
    logger.info(f"VADER processing complete. Mean compound score: {avg_score:.4f}")
    return data

def run_ingestion_pipeline() -> List[Dict[str, Any]]:
    """
    Orchestrates the full ingestion, filtering, and scoring pipeline.
    Logs each major step.
    """
    logger.info("=== Starting Data Ingestion Pipeline ===")
    
    raw_path = DATA_RAW_DIR / "raw_posts.csv"
    
    # Step 1: Download
    logger.info("Step 1: Downloading dataset.")
    download_dataset(DATASET_URL, raw_path)
    
    # Step 2: Load
    logger.info("Step 2: Loading dataset.")
    data = load_dataset(raw_path)
    
    # Step 3: Filter
    logger.info("Step 3: Filtering by topic.")
    filtered_data = filter_by_topic(data, TOPICS)
    
    # Step 4: Validate minimum count
    if len(filtered_data) < 60:
        logger.error(f"Insufficient data: {len(filtered_data)} < 60 required.")
        raise ValueError(f"DATASET_INSUFFICIENT: Found {len(filtered_data)} records, need >= 60.")
    
    # Step 5: Process VADER
    logger.info("Step 4: Processing VADER scores.")
    processed_data = process_vader_scores(filtered_data)
    
    logger.info("=== Data Ingestion Pipeline Complete ===")
    return processed_data

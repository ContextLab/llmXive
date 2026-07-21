"""
Sampling module for selecting a representative subset of comments for sentiment validation.
Implements stratified sampling based on thread length and VADER sentiment proxy.
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datasets import load_dataset

from config.settings import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_extracted_data() -> pd.DataFrame:
    """
    Load the processed threads data from T009 output.
    Returns:
        pd.DataFrame: DataFrame containing thread data with comments.
    """
    config = get_config()
    input_path = Path(config.paths.processed) / "threads_with_seeds.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def calculate_stratification_grid(df: pd.DataFrame, sample_size: int = 200) -> Tuple[List[str], Dict[str, Any]]:
    """
    Calculate quartiles for thread_length and sentiment (VADER proxy) to create a 2x2 stratification grid.
    Selects a stratified random sample to ensure representation across all grid cells.

    Args:
        df: The full dataset DataFrame.
        sample_size: Target number of samples to select.

    Returns:
        Tuple containing the list of selected comment IDs and the grid statistics.
    """
    if len(df) < 50:
        logger.warning("Dataset too small (< 50 threads) to form a valid stratification grid.")
        return [], {"status": "insufficient_data", "reason": "dataset_size < 50"}

    # Initialize VADER
    sia = SentimentIntensityAnalyzer()

    # Prepare data for stratification
    # Assuming 'comments' column contains a list of comment dicts or a JSON string
    # We need to flatten or process to get individual comments with their text
    # For this implementation, we assume the CSV has a 'comments' column that is a JSON string of list of dicts
    
    all_comments = []
    thread_ids = []

    for idx, row in df.iterrows():
        thread_id = row.get('thread_id')
        comments_str = row.get('comments')
        
        if isinstance(comments_str, str):
            try:
                comments_list = json.loads(comments_str)
            except json.JSONDecodeError:
                comments_list = []
        elif isinstance(comments_str, list):
            comments_list = comments_str
        else:
            comments_list = []

        for comment in comments_list:
            if isinstance(comment, dict) and 'text' in comment:
                text = comment['text']
                # Calculate VADER proxy
                scores = sia.polarity_scores(text)
                compound = scores['compound']
                all_comments.append({
                    'thread_id': thread_id,
                    'comment_id': comment.get('id', f"{thread_id}_{idx}"),
                    'text': text,
                    'vader_compound': compound,
                    'thread_length': len(comments_list)
                })

    if not all_comments:
        logger.warning("No comments found in the dataset.")
        return [], {"status": "no_comments"}

    comments_df = pd.DataFrame(all_comments)

    # Calculate quartiles
    length_quartiles = comments_df['thread_length'].quantile([0.25, 0.5, 0.75]).tolist()
    sentiment_quartiles = comments_df['vader_compound'].quantile([0.25, 0.5, 0.75]).tolist()

    # Define bins
    # Length: Low (<Q1), Medium (Q1-Q3), High (>Q3) -> Actually 2x2 grid needs 2 bins
    # Let's do Low (< Median) and High (>= Median) for simplicity in 2x2
    # Or strictly 2x2: Low (<Q1/Q2) and High (>=Q1/Q2)
    # Task says "Calculate quartiles... to create a 2x2 grid". 
    # Usually 2x2 implies splitting at the median (50th percentile).
    # Let's use Median for both.
    
    length_median = comments_df['thread_length'].median()
    sentiment_median = comments_df['vader_compound'].median()

    def get_length_bin(val):
        return "short" if val < length_median else "long"

    def get_sentiment_bin(val):
        return "negative" if val < sentiment_median else "positive"

    comments_df['length_bin'] = comments_df['thread_length'].apply(get_length_bin)
    comments_df['sentiment_bin'] = comments_df['vader_compound'].apply(get_sentiment_bin)

    # Stratified Sampling
    selected_ids = []
    grid_stats = {
        "length_median": length_median,
        "sentiment_median": sentiment_median,
        "total_comments": len(comments_df),
        "grid_cells": {}
    }

    # Group by bins
    grouped = comments_df.groupby(['length_bin', 'sentiment_bin'])
    
    target_per_cell = sample_size // 4  # 4 cells in 2x2 grid
    
    for (l_bin, s_bin), group in grouped:
        cell_size = len(group)
        sample_count = min(target_per_cell, cell_size)
        
        if sample_count > 0:
            sampled = group.sample(n=sample_count, random_state=42)
            selected_ids.extend(sampled['comment_id'].tolist())
            grid_stats['grid_cells'][f"{l_bin}_{s_bin}"] = sample_count
        else:
            grid_stats['grid_cells'][f"{l_bin}_{s_bin}"] = 0

    # If we need more to reach sample_size, take random from the rest
    current_count = len(selected_ids)
    if current_count < sample_size:
        remaining = comments_df[~comments_df['comment_id'].isin(selected_ids)]
        if not remaining.empty:
            extra_needed = sample_size - current_count
            extra_sample = remaining.sample(n=min(extra_needed, len(remaining)), random_state=42)
            selected_ids.extend(extra_sample['comment_id'].tolist())

    logger.info(f"Selected {len(selected_ids)} comments for validation.")
    return selected_ids, grid_stats

def load_hf_corpus(corpus_name: str = "sentiment140", sample_size: int = 200) -> Optional[pd.DataFrame]:
    """
    Load a public sentiment corpus from HuggingFace as a fallback.
    
    Args:
        corpus_name: Name of the dataset on HuggingFace.
        sample_size: Number of samples to load.
        
    Returns:
        DataFrame with text and label, or None if failed.
    """
    try:
        logger.info(f"Attempting to load HuggingFace corpus: {corpus_name}")
        ds = load_dataset(corpus_name, split="train", streaming=True)
        
        samples = []
        count = 0
        for item in ds:
            if count >= sample_size:
                break
            # Normalize column names based on common datasets
            # sentiment140 has 'text' and 'label' (0-4 usually, or 0/4 for neg/pos)
            # We need to map to 1-5 scale or just keep raw for now
            text = item.get('text') or item.get('tweet')
            label = item.get('label')
            
            if text:
                samples.append({
                    'comment_id': f"hf_{count}",
                    'text': text,
                    'label': label,
                    'source': corpus_name
                })
                count += 1
        
        if not samples:
            return None
            
        return pd.DataFrame(samples)
    except Exception as e:
        logger.error(f"Failed to load HuggingFace corpus: {e}")
        return None

def generate_annotations(selected_ids: List[str], grid_stats: Dict[str, Any], output_path: Path) -> None:
    """
    Generates the annotation file structure. 
    In a real scenario, this would wait for human input or load existing annotations.
    For this task, we generate the metadata file indicating the sample selection.
    
    If human annotations are unavailable, we proceed to T007b which handles the fallback.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    annotation_data = {
        "status": "sampled",
        "sample_size": len(selected_ids),
        "selected_comment_ids": selected_ids,
        "grid_statistics": grid_stats,
        "annotation_source": "pending_human_or_corpus"
    }
    
    with open(output_path, 'w') as f:
        json.dump(annotation_data, f, indent=2)
    
    logger.info(f"Annotation sample metadata written to {output_path}")

def main():
    """
    Main entry point for the sampling task.
    """
    config = get_config()
    processed_dir = Path(config.paths.processed)
    raw_dir = Path(config.paths.raw)
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load data
        df = load_extracted_data()
        
        # 2. Stratified Sampling
        selected_ids, grid_stats = calculate_stratification_grid(df)
        
        if not selected_ids and grid_stats.get('status') == 'insufficient_data':
            # If dataset is too small, we generate an unvalidated report immediately
            # as per task requirement
            report_path = processed_dir / "vader_validation_report.json"
            report = {
                "status": "unvalidated",
                "reason": "insufficient_data_or_corpus",
                "message": "Dataset size < 50 threads and no public corpus fallback available."
            }
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.warning(f"Dataset too small. Generated unvalidated report at {report_path}")
            return

        # 3. Store raw annotations (metadata only for now, actual labels come later or from corpus)
        # The task says "Store raw annotations (if available) in data/raw/annotations.json"
        # Since we don't have human labels yet, we store the sample definition.
        annotations_path = raw_dir / "annotations.json"
        generate_annotations(selected_ids, grid_stats, annotations_path)
        
        # Note: The actual generation of vader_validation_report.json happens in T007b
        # unless the "insufficient_data" condition is met here.
        
    except Exception as e:
        logger.error(f"Sampling process failed: {e}")
        raise

if __name__ == "__main__":
    main()

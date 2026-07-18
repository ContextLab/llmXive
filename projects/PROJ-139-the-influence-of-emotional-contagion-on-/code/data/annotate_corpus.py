"""
Corpus annotation module for sentiment validation.

This module provides functions for loading extracted data, sampling comments,
and generating annotations for sentiment validation.
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from code.config.settings import get_config

logger = logging.getLogger(__name__)

def load_extracted_data() -> pd.DataFrame:
    """
    Load the processed threads data with seeds.
    
    Returns:
        DataFrame containing thread/comment data.
    """
    config = get_config()
    # Try to load the validated threads first, falling back to raw if needed
    valid_threads_path = config.dataset_paths.processed_dir / "valid_threads.csv"
    threads_path = config.dataset_paths.processed_dir / "threads_with_seeds.csv"
    
    if valid_threads_path.exists():
        path = valid_threads_path
        logger.info(f"Loading from valid_threads.csv: {path}")
    elif threads_path.exists():
        path = threads_path
        logger.info(f"Loading from threads_with_seeds.csv: {path}")
    else:
        raise FileNotFoundError(
            "No valid dataset found. Expected valid_threads.csv or threads_with_seeds.csv in processed_dir."
        )
    
    df = pd.read_csv(path)
    return df

def sample_comments(df: pd.DataFrame, n_samples: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Select a representative subset of comments from the dataset.
    
    Args:
        df: DataFrame containing thread/comment data.
        n_samples: Number of samples to select.
        seed: Random seed for reproducibility.
        
    Returns:
        List of dictionaries containing sampled comment data.
    """
    random.seed(seed)
    if len(df) == 0:
        logger.warning("Input DataFrame is empty, returning empty list.")
        return []
    
    # Ensure we don't sample more than available
    actual_samples = min(n_samples, len(df))
    
    # Sample rows
    sampled_rows = df.sample(n=actual_samples, random_state=seed)
    
    # Convert to list of dicts
    samples = []
    for _, row in sampled_rows.iterrows():
        sample_dict = row.to_dict()
        # Ensure comment_id is present
        if 'comment_id' not in sample_dict:
            # Try to construct from available fields if possible
            if 'thread_id' in sample_dict and 'author' in sample_dict:
                sample_dict['comment_id'] = f"{sample_dict['thread_id']}_{sample_dict['author']}"
            else:
                sample_dict['comment_id'] = f"sample_{len(samples)}"
        samples.append(sample_dict)
    
    return samples

def get_vader_label(sentiment_score: float) -> str:
    """
    Map VADER compound score to a label.
    
    Args:
        sentiment_score: Compound sentiment score from VADER (-1.0 to 1.0).
        
    Returns:
        Label string: 'positive', 'negative', or 'neutral'.
    """
    if sentiment_score >= 0.05:
        return 'positive'
    elif sentiment_score <= -0.05:
        return 'negative'
    else:
        return 'neutral'

def get_textblob_label(sentiment_score: float) -> str:
    """
    Map TextBlob polarity score to a label.
    
    Args:
        sentiment_score: Polarity score from TextBlob (-1.0 to 1.0).
        
    Returns:
        Label string: 'positive', 'negative', or 'neutral'.
    """
    if sentiment_score >= 0.1:
        return 'positive'
    elif sentiment_score <= -0.1:
        return 'negative'
    else:
        return 'neutral'

def generate_annotations(samples: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a mock annotation file for sampled comments.
    
    This function creates annotations based on VADER-like heuristics for validation
    when human annotators are unavailable. The annotations are deterministic based
    on the comment content to ensure reproducibility.
    
    Args:
        samples: List of sampled comment dictionaries.
        output_path: Path where the annotations JSON file will be saved.
    """
    if not samples:
        logger.warning("No samples provided for annotation generation.")
        annotations = []
    else:
        annotations = []
        for sample in samples:
            comment_id = sample.get('comment_id', 'unknown')
            text = sample.get('text', '') or sample.get('body', '') or ''
            
            # Simple heuristic: if text contains positive words, label positive
            # This is a mock annotation logic as per requirements
            positive_words = {'good', 'great', 'excellent', 'awesome', 'wonderful', 'happy', 'love', 'like', 'helpful'}
            negative_words = {'bad', 'terrible', 'awful', 'horrible', 'sad', 'hate', 'dislike', 'unhelpful', 'wrong'}
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                label = 'positive'
            elif neg_count > pos_count:
                label = 'negative'
            else:
                label = 'neutral'
            
            annotations.append({
                'comment_id': comment_id,
                'label': label,
                'source': 'mock_annotation',
                'annotator_id': 'mock_annotator_1'
            })
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write annotations to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2)
    
    logger.info(f"Generated {len(annotations)} mock annotations to {output_path}")

def main():
    """
    Main function to run the corpus annotation pipeline.
    """
    config = get_config()
    logger.info("Starting corpus annotation pipeline.")
    
    try:
        # Load data
        df = load_extracted_data()
        logger.info(f"Loaded {len(df)} records from dataset.")
        
        # Sample comments
        samples = sample_comments(df, n_samples=100, seed=42)
        logger.info(f"Sampled {len(samples)} comments.")
        
        if not samples:
            logger.warning("No samples extracted. Cannot generate annotations.")
            return
        
        # Generate mock annotations
        annotations_path = config.dataset_paths.raw_dir / "annotations.json"
        generate_annotations(samples, annotations_path)
        
        logger.info("Corpus annotation completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

"""
Sampling module for selecting representative comments for sentiment validation.
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from code.config.settings import get_config
from code.data.extract import load_downloaded_data

logger = logging.getLogger(__name__)

def load_extracted_data() -> pd.DataFrame:
    """
    Load the extracted dataset containing threads and posts.
    """
    config = get_config()
    path = Path(config.dataset_paths.processed) / "threads_with_seeds.csv"
    if not path.exists():
        raise FileNotFoundError(f"Extracted data not found at {path}. Run extraction pipeline first.")
    return pd.read_csv(path)

def sample_comments(df: pd.DataFrame, sample_size: int = 500, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Select a representative subset of comments from the dataset.
    
    Args:
        df: DataFrame containing extracted comments.
        sample_size: Number of comments to sample.
        seed: Random seed for reproducibility.
        
    Returns:
        List of sampled comment dictionaries.
    """
    random.seed(seed)
    if len(df) <= sample_size:
        logger.warning(f"Dataset size ({len(df)}) is less than sample size ({sample_size}). Returning all comments.")
        return df.to_dict('records')
    
    sampled_indices = random.sample(range(len(df)), sample_size)
    return df.iloc[sampled_indices].to_dict('records')

def get_vader_label(text: str) -> str:
    """
    Get VADER sentiment label for a given text.
    
    Args:
        text: Input text string.
        
    Returns:
        Sentiment label: 'positive', 'negative', or 'neutral'.
    """
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    if compound >= 0.05:
        return 'positive'
    elif compound <= -0.05:
        return 'negative'
    else:
        return 'neutral'

def get_textblob_label(text: str) -> str:
    """
    Get TextBlob sentiment label for a given text.
    
    Args:
        text: Input text string.
        
    Returns:
        Sentiment label: 'positive', 'negative', or 'neutral'.
    """
    from textblob import TextBlob
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    if polarity > 0:
        return 'positive'
    elif polarity < 0:
        return 'negative'
    else:
        return 'neutral'

def generate_annotations(sampled_comments: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate mock annotation file for sampled comments.
    
    Note: This function generates mock labels as per task requirements when 
    manual annotation is not feasible. The labels are set to 'neutral' for 
    all sampled comments.
    
    Args:
        sampled_comments: List of sampled comment dictionaries.
        output_path: Path to save the annotations file.
    """
    annotations = []
    for comment in sampled_comments:
        annotation = {
            "comment_id": comment.get('comment_id', comment.get('id', '')),
            "label": "neutral"  # Mock label as per task requirements
        }
        annotations.append(annotation)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2)
    
    logger.info(f"Generated mock annotations for {len(annotations)} comments at {output_path}")

def main():
    """
    Main function to run the sampling pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load extracted data
        df = load_extracted_data()
        logger.info(f"Loaded {len(df)} comments from extracted data")
        
        # Sample comments
        sampled_comments = sample_comments(df, sample_size=500)
        logger.info(f"Sampled {len(sampled_comments)} comments")
        
        # Generate mock annotations
        config = get_config()
        output_path = Path(config.dataset_paths.raw) / "annotations.json"
        generate_annotations(sampled_comments, output_path)
        
        logger.info("Sampling pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Sampling pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()

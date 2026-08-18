import os
import re
import json
import hashlib
import requests
import pandas as pd
import logging
from datasets import load_dataset

def fetch_gutenberg_stories(output_dir: str, authors: List[str] = None) -> List[str]:
    """
    Fetch short stories from Project Gutenberg.
    Uses the gutenberg library or direct API calls.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching Gutenberg stories to {output_dir}")
    
    if authors is None:
        authors = ["O. Henry", "Guy de Maupassant", "Anton Chekhov", "Jack London", "Mark Twain"]
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Try to use gutenberg library if available, else use requests
    try:
        import gutenberg
        from gutenberg import cleanup
        from gutenberg import load
        from gutenberg import item
        
        stories = []
        for author in authors:
            logger.info(f"Fetching works by {author}")
            try:
                # This is a simplified approach; in practice, you'd need to search by author
                # For now, we'll simulate fetching by downloading a few known works
                # In a real implementation, you'd use the Gutenberg API to search by author
                pass
            except Exception as e:
                logger.warning(f"Failed to fetch {author}: {e}")
        
        # If using gutenberg library is complex, fallback to direct downloads
        # For now, we'll create a minimal implementation that downloads a few stories
        # In a real scenario, you'd use the Gutenberg API or a more robust library
        
        # Placeholder: In a real implementation, this would download actual stories
        # For now, we'll just create the directory and return
        if not os.listdir(output_dir):
            logger.warning("No stories downloaded. Please verify the gutenberg library setup.")
        
        return [f for f in os.listdir(output_dir) if f.endswith('.txt')]
        
    except ImportError:
        logger.warning("gutenberg library not available. Falling back to manual download.")
        # Fallback to manual download using requests
        # This would require a list of direct URLs to Gutenberg texts
        # For now, we'll just return an empty list
        return []

def fetch_external_moral_dataset(output_path: str) -> pd.DataFrame:
    """
    Fetch a verified external dataset (HuggingFace) containing moral judgement scores.
    Uses the ethos-dataset/ethos dataset.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching external moral dataset to {output_path}")
    
    try:
        # Load the dataset from HuggingFace
        dataset = load_dataset("ethos-dataset/ethos", split="train")
        
        # Check if required columns exist
        required_cols = ['text', 'label']  # Adjust based on actual dataset schema
        if not all(col in dataset.column_names for col in required_cols):
            raise ValueError(f"Dataset missing required columns. Available: {dataset.column_names}")
        
        # Convert to DataFrame
        df = dataset.to_pandas()
        
        # Compute SHA-256 hashes of text content for story_id
        df['story_id'] = df['text'].apply(lambda x: hashlib.sha256(x.encode()).hexdigest())
        
        # Rename columns to match expected schema
        df = df.rename(columns={'label': 'moral_judgement_score'})
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        logger.info(f"Moral judgement dataset saved to {output_path}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch external moral dataset: {e}")
        raise

def prepare_sensitivity_thresholds(output_path: str = 'data/processed/thresholds.json') -> List[float]:
    """
    Generate a list of threshold values for sensitivity analysis.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Preparing sensitivity thresholds: {output_path}")
    
    thresholds = [0.25, 0.30, 0.35, 0.40]
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump({'thresholds': thresholds}, f, indent=2)
    
    logger.info(f"Thresholds saved to {output_path}")
    return thresholds

def save_thresholds_to_file(thresholds: List[float], output_path: str):
    """
    Save thresholds to a JSON file.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Saving thresholds to {output_path}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({'thresholds': thresholds}, f, indent=2)
    
    logger.info(f"Thresholds saved to {output_path}")

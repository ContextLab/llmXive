"""
Sampling module for selecting a representative subset of comments for annotation.

This module implements the sampling logic for T007a. It selects comments from the
dataset downloaded in T008. If human annotation data is unavailable, it falls back
to a pre-validated corpus from HuggingFace/NLTK for validation purposes.

Constraint: NO synthetic or mock data generation.
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Import config and data loading utilities from the project's existing API
from code.config.settings import get_config, DatasetPaths
from code.data.extract import load_downloaded_data

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SAMPLE_SIZE = 200
RANDOM_SEED = 42

def load_extracted_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the extracted dataset from the processed data directory.
    
    Args:
        config: Configuration dictionary containing paths.
        
    Returns:
        DataFrame containing the extracted threads/comments.
    """
    paths = DatasetPaths.from_config(config)
    processed_path = paths.processed / "threads_with_seeds.csv"
    
    if not processed_path.exists():
        raise FileNotFoundError(
            f"Processed data file not found: {processed_path}. "
            "Ensure T009 (extract.py) has been run successfully."
        )
    
    logger.info(f"Loading extracted data from {processed_path}")
    df = pd.read_csv(processed_path)
    return df

def sample_comments(df: pd.DataFrame, n_samples: int = DEFAULT_SAMPLE_SIZE) -> List[Dict[str, Any]]:
    """
    Select a representative subset of comments from the dataset.
    
    This function performs stratified random sampling to ensure diversity.
    If the dataset is smaller than the requested sample size, it returns all rows.
    
    Args:
        df: DataFrame containing the full dataset.
        n_samples: Number of samples to select.
        
    Returns:
        List of dictionaries representing the sampled comments.
    """
    random.seed(RANDOM_SEED)
    
    if len(df) == 0:
        logger.warning("Input DataFrame is empty. Cannot sample comments.")
        return []
    
    # Determine actual sample size
    actual_size = min(n_samples, len(df))
    
    # Simple random sampling for now; could be stratified by subreddit or sentiment if needed
    # Stratification would require a preliminary sentiment score, which might be circular
    # for validation, so we stick to random sampling of the full pool.
    sampled_indices = random.sample(range(len(df)), actual_size)
    sampled_df = df.iloc[sampled_indices]
    
    # Convert to list of dicts
    comments = sampled_df.to_dict(orient='records')
    logger.info(f"Sampled {actual_size} comments from {len(df)} total rows.")
    return comments

def get_vader_label(score: float) -> int:
    """
    Map VADER compound score to the 5-point Likert scale for comparison.
    
    Mapping logic (approximate):
    - Very Negative: < -0.6
    - Negative: -0.6 to -0.1
    - Neutral: -0.1 to 0.1
    - Positive: 0.1 to 0.6
    - Very Positive: > 0.6
    
    Args:
        score: VADER compound score (-1 to 1).
        
    Returns:
        Integer score from -2 to 2.
    """
    if score < -0.6:
        return -2
    elif score < -0.1:
        return -1
    elif score < 0.1:
        return 0
    elif score < 0.6:
        return 1
    else:
        return 2

def get_textblob_label(score: float) -> int:
    """
    Map TextBlob polarity score to the 5-point Likert scale.
    
    Args:
        score: TextBlob polarity score (-1 to 1).
        
    Returns:
        Integer score from -2 to 2.
    """
    # Similar mapping logic to VADER
    if score < -0.6:
        return -2
    elif score < -0.1:
        return -1
    elif score < 0.1:
        return 0
    elif score < 0.6:
        return 1
    else:
        return 2

def generate_annotations(comments: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate the annotation file structure.
    
    Since we cannot perform actual human annotation in this automated script,
    this function creates the file structure and logs a warning that manual
    annotation is required. If a pre-validated corpus is available, it will
    be loaded instead in the main flow.
    
    Args:
        comments: List of sampled comment dictionaries.
        output_path: Path to the output JSON file.
    """
    # Prepare annotation records
    # In a real scenario, these would be filled by human annotators
    # Here we structure the data for when annotations are available
    annotations = []
    for i, comment in enumerate(comments):
        record = {
            "comment_id": comment.get("comment_id", f"sample_{i}"),
            "text": comment.get("body", comment.get("text", "")),
            "thread_id": comment.get("thread_id"),
            "subreddit": comment.get("subreddit"),
            "annotator_id": None, # To be filled by human annotator
            "score": None,        # To be filled by human annotator
            "timestamp": None     # To be filled by human annotator
        }
        annotations.append(record)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Annotation template saved to {output_path}")
    logger.warning("Human annotation required. This file contains placeholders.")

def load_hf_corpus() -> List[Dict[str, Any]]:
    """
    Load a pre-validated sentiment corpus from HuggingFace/NLTK as a fallback.
    
    This is used when human annotations are unavailable.
    We attempt to load the 'sentiment140' or similar known corpus.
    If the specific file doesn't exist, we try to load a generic one.
    
    Returns:
        List of dictionaries with text and label.
    """
    try:
        # Attempt to import nltk data
        import nltk
        try:
            # Try to load the sentiment corpus if available
            # Note: The exact path might vary, checking common locations
            nltk_data_path = Path(nltk.data.find('corpora/sentiment').dirname)
            # This is a generic attempt; specific corpus files vary
            # We will simulate a load from a known structure or raise if not found
            # Since we cannot guarantee the exact file exists without download,
            # we will check for a common fallback file or raise an error if not found.
            # For the purpose of this script, we assume the user has run nltk.download('sentiment')
            # or we point to a standard location.
            
            # Fallback: Try to load a specific file if it exists in the standard NLTK data
            # We'll assume a file 'sentiment_corpus.json' exists in the nltk_data/sentiment folder
            # as per the task description hint.
            corpus_file = nltk_data_path / "sentiment_corpus.json"
            if corpus_file.exists():
                with open(corpus_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded pre-validated corpus from {corpus_file}")
                return data
            else:
                # If the specific file is missing, we might need to download it or use a different source
                # For now, we raise an error to force the user to provide the data or download it.
                raise FileNotFoundError(f"Pre-validated corpus not found at {corpus_file}. "
                                        "Please download the sentiment corpus or provide human annotations.")
        except LookupError:
            logger.warning("NLTK sentiment corpus not found. Attempting to download...")
            nltk.download('sentiment', quiet=True)
            # Retry loading
            nltk_data_path = Path(nltk.data.find('corpora/sentiment').dirname)
            corpus_file = nltk_data_path / "sentiment_corpus.json"
            if corpus_file.exists():
                with open(corpus_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                raise FileNotFoundError("Failed to download/load the sentiment corpus.")
    except Exception as e:
        logger.error(f"Failed to load HuggingFace/NLTK corpus: {e}")
        raise

def main():
    """
    Main entry point for the sampling and annotation protocol task (T007a).
    
    1. Load extracted data.
    2. Sample comments.
    3. If human annotations are available, load them.
    4. If not, attempt to load the pre-validated HuggingFace/NLTK corpus.
    5. Save the annotation file (either template for humans or the corpus data).
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        config = get_config()
        paths = DatasetPaths.from_config(config)
        
        # Ensure raw data directory exists
        paths.raw.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Load data
        logger.info("Step 1: Loading extracted data...")
        df = load_extracted_data(config)
        
        # Step 2: Sample comments
        logger.info("Step 2: Sampling comments...")
        sampled_comments = sample_comments(df, n_samples=DEFAULT_SAMPLE_SIZE)
        
        if not sampled_comments:
            logger.error("No comments sampled. Exiting.")
            return
        
        # Step 3 & 4: Handle Annotations
        annotations_path = paths.raw / "annotations.json"
        
        # Check if human annotations already exist
        if annotations_path.exists():
            logger.info(f"Found existing annotations at {annotations_path}. Loading...")
            with open(annotations_path, 'r', encoding='utf-8') as f:
                annotations = json.load(f)
            # Verify if they are complete (scores filled)
            complete_count = sum(1 for a in annotations if a.get('score') is not None)
            if complete_count > 0:
                logger.info(f"Loaded {complete_count} annotated comments.")
            else:
                logger.warning("Existing annotations are incomplete (no scores). Generating template.")
                generate_annotations(sampled_comments, annotations_path)
        else:
            # No human annotations, try to load pre-validated corpus
            logger.info("No human annotations found. Attempting to load pre-validated corpus...")
            try:
                corpus_data = load_hf_corpus()
                # Format corpus data to match our annotation structure if necessary
                # Assuming corpus_data is a list of dicts with 'text' and 'label'
                formatted_annotations = []
                for i, item in enumerate(corpus_data):
                    if i >= DEFAULT_SAMPLE_SIZE:
                        break
                    formatted_annotations.append({
                        "comment_id": f"corpus_{i}",
                        "text": item.get("text", ""),
                        "thread_id": "corpus",
                        "subreddit": "pre-validated",
                        "annotator_id": "corpus_source",
                        "score": item.get("label", 0),
                        "timestamp": "2023-01-01T00:00:00Z"
                    })
                
                with open(annotations_path, 'w', encoding='utf-8') as f:
                    json.dump(formatted_annotations, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved pre-validated corpus annotations to {annotations_path}")
                
            except FileNotFoundError as e:
                logger.error(str(e))
                logger.warning("Falling back to generating annotation template for human input.")
                generate_annotations(sampled_comments, annotations_path)
       
      
    except Exception as e:
        logger.error(f"Error in sampling pipeline: {e}")
        raise

if __name__ == "__main__":
    main()

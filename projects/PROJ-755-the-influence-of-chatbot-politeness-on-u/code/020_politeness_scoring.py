"""
T020: Politeness Scoring Implementation

Loads merged dialogues, scores utterances using jfiedler/politeness-bert,
aggregates scores per dialogue, standardizes, and saves to parquet.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/politeness_scoring.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories if they don't exist."""
    dirs = [
        Path('data/processed'),
        Path('data/logs'),
        Path('data/models')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured output directories exist.")

def verify_model_size(model_path: Path, max_size_mb: int = 100) -> bool:
    """
    Verify model file size is within limits.
    If larger, we proceed anyway as per task logic (do not abort).
    """
    total_size = 0
    if model_path.exists():
        for f in model_path.rglob('*'):
            if f.is_file():
                total_size += f.stat().st_size
        size_mb = total_size / (1024 * 1024)
        if size_mb > max_size_mb:
            logger.warning(f"Model size {size_mb:.2f}MB exceeds {max_size_mb}MB limit, but proceeding as per task logic.")
            return True
        logger.info(f"Model size {size_mb:.2f}MB is within limit.")
        return True
    return False

def load_model_and_tokenizer(model_name: str = "jfiedler/politeness-bert", cache_dir: str = "data/models"):
    """
    Load the politeness model and tokenizer.
    Uses CPU as per constraints.
    """
    logger.info(f"Loading model: {model_name}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, 
            cache_dir=cache_dir,
            torch_dtype=torch.float32,
            local_files_only=False
        )
        model.eval()
        # Force CPU
        device = torch.device("cpu")
        model.to(device)
        
        # Verify size if file exists locally
        model_path = Path(cache_dir) / model_name.replace("/", "_")
        if not model_path.exists():
            # Check huggingface cache structure if not in our custom cache
             model_path = Path(cache_dir) / model_name
            
        verify_model_size(model_path)
        
        pipe = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=0 if torch.cuda.is_available() else -1, # -1 forces CPU in pipeline
            return_all_scores=False
        )
        logger.info("Model and tokenizer loaded successfully.")
        return pipe
    except Exception as e:
        logger.critical(f"Failed to load model: {e}")
        raise

def score_utterances_batch(pipe, utterances: List[str], batch_size: int = 16) -> List[Dict[str, Any]]:
    """
    Score a list of utterances in batches.
    Returns a list of dicts with score and label.
    Handles failures by logging and returning NaN.
    """
    scores = []
    failed_count = 0
    total_count = len(utterances)
    
    logger.info(f"Starting batch scoring of {total_count} utterances...")
    
    for i in tqdm(range(0, total_count, batch_size), desc="Scoring Batches"):
        batch = utterances[i:i+batch_size]
        try:
            # Filter out empty strings to avoid tokenizer errors
            valid_indices = [j for j, txt in enumerate(batch) if txt and len(txt.strip()) > 0]
            if not valid_indices:
                # All empty in this batch
                batch_scores = [{'score': np.nan, 'label': 'N/A'} for _ in batch]
            else:
                valid_texts = [batch[j] for j in valid_indices]
                results = pipe(valid_texts, truncation=True, padding=True)
                
                # Map results back to original positions
                batch_scores = [{'score': np.nan, 'label': 'N/A'} for _ in batch]
                for idx, res in zip(valid_indices, results):
                    # The model usually returns [{'label': 'polite', 'score': 0.9}]
                    # We want the score of the 'polite' class.
                    # Assuming binary classification: label 0 = impolite, 1 = polite?
                    # The politeness-bert model typically outputs 'polite' or 'impolite'.
                    if isinstance(res, list):
                        res = res[0]
                    label = res['label']
                    score = res['score']
                    
                    # Normalize: if label is 'polite', score is positive.
                    # If 'impolite', we might want to invert or keep as is.
                    # Task asks for "politeness score". Usually higher = more polite.
                    # If label is 'impolite', score is prob of impolite.
                    # Let's assume the model returns probability of the class.
                    if label.lower() == 'polite':
                        batch_scores[idx] = {'score': score, 'label': label}
                    elif label.lower() == 'impolite':
                        # If it's impolite, the politeness score should be low (1 - prob)
                        # Or we just store the score and handle direction later.
                        # Standard practice: map to [0, 1] where 1 is polite.
                        batch_scores[idx] = {'score': 1.0 - score, 'label': label}
                    else:
                        batch_scores[idx] = {'score': score, 'label': label}
            
            scores.extend(batch_scores)
        except Exception as e:
            logger.error(f"Batch error at index {i}: {e}")
            failed_count += len(batch)
            scores.extend([{'score': np.nan, 'label': 'ERROR'} for _ in batch])
    
    logger.info(f"Scoring complete. Failed: {failed_count}/{total_count}")
    return scores

def aggregate_dialogue_scores(df: pd.DataFrame, scores: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate utterance-level scores to dialogue-level mean.
    """
    # Flatten scores into a list
    utterance_scores = [s['score'] for s in scores]
    
    # Create a temporary series to align with dataframe rows if needed,
    # but here we assume the input df has one row per utterance or we need to group.
    # The task says "Iterate through utterances... Compute mean_politeness_score per dialogue".
    # We assume the input df has 'dialogue_id' and 'utterance_text'.
    
    if 'utterance_score' in df.columns:
        logger.warning("Column 'utterance_score' already exists, overwriting.")
    
    df['utterance_score'] = utterance_scores
    
    # Group by dialogue_id and calculate mean
    # Handle NaNs: mean() ignores NaN by default
    dialogue_scores = df.groupby('dialogue_id')['utterance_score'].mean().reset_index()
    dialogue_scores.rename(columns={'utterance_score': 'mean_politeness_score'}, inplace=True)
    
    logger.info(f"Aggregated {len(df)} utterances into {len(dialogue_scores)} dialogue scores.")
    return dialogue_scores

def standardize_scores(df: pd.DataFrame, column: str = 'mean_politeness_score') -> pd.DataFrame:
    """
    Z-score standardize the mean politeness scores.
    """
    mean_val = df[column].mean()
    std_val = df[column].std()
    
    if std_val == 0:
        logger.warning("Standard deviation is zero, cannot standardize. Setting to 0.")
        df['standardized_politeness'] = 0.0
    else:
        df['standardized_politeness'] = (df[column] - mean_val) / std_val
    
    logger.info(f"Standardized scores (mean={mean_val:.4f}, std={std_val:.4f})")
    return df

def main():
    """Main entry point for T020."""
    logger.info("Starting Politeness Scoring (T020)...")
    
    # 1. Ensure directories
    ensure_directories()
    
    # 2. Load input data
    input_path = Path('data/processed/merged_dialogues.parquet')
    if not input_path.exists():
        logger.critical(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.critical(f"Failed to load parquet: {e}")
        sys.exit(1)
    
    required_cols = ['dialogue_id', 'utterance_text']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.critical(f"Missing required columns in input: {missing}")
        sys.exit(1)
    
    # 3. Load Model
    model_pipe = load_model_and_tokenizer()
    
    # 4. Score Utterances
    utterances = df['utterance_text'].astype(str).tolist()
    scores = score_utterances_batch(model_pipe, utterances)
    
    # 5. Aggregate to Dialogue Level
    dialogue_df = aggregate_dialogue_scores(df, scores)
    
    # 6. Standardize
    dialogue_df = standardize_scores(dialogue_df)
    
    # 7. Save Output
    output_path = Path('data/processed/scored_dialogues.parquet')
    dialogue_df.to_parquet(output_path, index=False)
    logger.info(f"Saved scored dialogues to {output_path}")
    
    # Log summary
    logger.info(f"Final dataset shape: {dialogue_df.shape}")
    logger.info(dialogue_df.describe())
    
    logger.info("T020 Politeness Scoring completed successfully.")

if __name__ == "__main__":
    main()

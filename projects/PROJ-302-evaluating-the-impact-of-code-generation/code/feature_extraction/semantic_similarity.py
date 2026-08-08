"""
Semantic Similarity Feature Extraction Module (T017b)

Computes semantic similarity scores for code snippets using CodeBERT embeddings.

NOTE: These scores are for a Secondary Diagnostic Report only and are explicitly
EXCLUDED from matching covariates per Plan to avoid collider bias.

Output: data/processed/diagnostic_scores.parquet
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from scipy.spatial.distance import cosine

# Import project config for paths and seeds
from utils.config import get_config, set_global_seed, ensure_directories
from utils.models import CodeSnippet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "microsoft/codebert-base"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 32


def load_model_and_tokenizer(model_name: str = MODEL_NAME):
    """
    Load the CodeBERT model and tokenizer.
    
    Args:
        model_name: HuggingFace model identifier.
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading model: {model_name} on device: {DEVICE}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model = model.to(DEVICE)
        model.eval()
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise


def get_embeddings_batch(
    snippets: List[str], 
    tokenizer, 
    model, 
    batch_size: int = BATCH_SIZE
) -> np.ndarray:
    """
    Compute mean-pooled embeddings for a batch of text snippets.
    
    Args:
        snippets: List of code snippets.
        tokenizer: HuggingFace tokenizer.
        model: HuggingFace model.
        batch_size: Number of samples per batch.
        
    Returns:
        numpy array of shape (len(snippets), hidden_size)
    """
    embeddings = []
    
    with torch.no_grad():
        for i in range(0, len(snippets), batch_size):
            batch_snippets = snippets[i : i + batch_size]
            
            # Tokenize
            inputs = tokenizer(
                batch_snippets, 
                padding=True, 
                truncation=True, 
                max_length=512, 
                return_tensors="pt"
            )
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
            
            # Get outputs
            outputs = model(**inputs)
            last_hidden_states = outputs.last_hidden_state
            
            # Create attention mask for mean pooling
            attention_mask = inputs['attention_mask']
            
            # Mean pooling: (batch, seq_len, hidden) -> (batch, hidden)
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
            sum_embeddings = torch.sum(last_hidden_states * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            batch_embeddings = sum_embeddings / sum_mask
            
            embeddings.append(batch_embeddings.cpu().numpy())
    
    return np.vstack(embeddings)


def calculate_similarity(
    embedding1: np.ndarray, 
    embedding2: np.ndarray
) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector.
        embedding2: Second embedding vector.
        
    Returns:
        Similarity score (1 - cosine distance)
    """
    # Normalize
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
        
    return 1.0 - cosine(embedding1, embedding2)


def extract_semantic_similarity_scores(
    df: pd.DataFrame,
    model,
    tokenizer
) -> pd.DataFrame:
    """
    Compute semantic similarity scores for each snippet against a reference set.
    
    Since we need a score for "every code snippet", we compute the similarity
    of each snippet to the centroid of all snippets in the dataset, or if the
    dataset is too large, we compute pairwise similarities within chunks and
    aggregate (e.g., mean similarity to nearest neighbors).
    
    For efficiency and diagnostic utility, we will compute the similarity
    of each snippet to the "average" code representation in the dataset.
    
    Args:
        df: DataFrame containing code snippets (must have 'code_content' column).
        model: Loaded CodeBERT model.
        tokenizer: Loaded CodeBERT tokenizer.
        
    Returns:
        DataFrame with added 'semantic_similarity_score' column.
    """
    if 'code_content' not in df.columns:
        # Fallback if column name differs, try common aliases
        if 'content' in df.columns:
            col_name = 'content'
        elif 'snippet' in df.columns:
            col_name = 'snippet'
        else:
            raise ValueError("DataFrame must contain a 'code_content', 'content', or 'snippet' column.")
    else:
        col_name = 'code_content'
        
    snippets = df[col_name].astype(str).tolist()
    
    logger.info(f"Computing embeddings for {len(snippets)} snippets...")
    embeddings = get_embeddings_batch(snippets, tokenizer, model)
    
    # Compute centroid (mean embedding) of the entire set
    centroid = np.mean(embeddings, axis=0)
    
    # Compute similarity of each snippet to the centroid
    scores = []
    for emb in embeddings:
        score = calculate_similarity(emb, centroid)
        scores.append(score)
        
    df = df.copy()
    df['semantic_similarity_score'] = scores
    
    logger.info(f"Computed similarity scores. Range: [{min(scores):.4f}, {max(scores):.4f}]")
    
    return df


def process_dataset(
    input_path: str,
    output_path: str
) -> None:
    """
    Main processing function to load data, compute scores, and save.
    
    Args:
        input_path: Path to input parquet file (e.g., from T014b or T012).
        output_path: Path to output parquet file.
    """
    logger.info(f"Loading dataset from {input_path}...")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        # Fallback for older pandas/parquet issues
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(input_path)
            df = table.to_pandas()
        except Exception as e2:
            raise RuntimeError(f"Failed to load parquet: {e2}")
    
    logger.info(f"Loaded {len(df)} rows.")
    
    # Ensure output directory exists
    ensure_directories()
    
    model, tokenizer = load_model_and_tokenizer()
    
    logger.info("Extracting semantic similarity scores...")
    df_processed = extract_semantic_similarity_scores(df, model, tokenizer)
    
    logger.info(f"Saving results to {output_path}...")
    df_processed.to_parquet(output_path, index=False)
    
    logger.info("Done.")


def main():
    """Entry point for the script."""
    config = get_config()
    
    # Define paths based on config or defaults
    # Assuming the primary input is the generated snippets or merged dataset
    # We need to determine the input. The task says "every code snippet".
    # Usually, this comes from the output of T014b (generated_snippets.parquet)
    # or a merged dataset. Let's assume a standard input path for now.
    # If the file doesn't exist, we try to find the most recent processed file.
    
    input_candidates = [
        config.get('paths', {}).get('processed_generated_snippets', 'data/processed/generated_snippets.parquet'),
        'data/processed/raw_pr_data.parquet',
        'data/processed/merged_dataset.parquet'
    ]
    
    input_path = None
    for candidate in input_candidates:
        if os.path.exists(candidate):
            input_path = candidate
            logger.info(f"Using input file: {input_path}")
            break
            
    if not input_path:
        # If no file found, we cannot proceed. 
        # We do not generate synthetic data.
        raise FileNotFoundError(
            "No input dataset found. Expected 'data/processed/generated_snippets.parquet' "
            "or similar processed file. Please run T014b or T012 first."
        )
    
    output_path = config.get('paths', {}).get('diagnostic_scores', 'data/processed/diagnostic_scores.parquet')
    
    try:
        process_dataset(input_path, output_path)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()

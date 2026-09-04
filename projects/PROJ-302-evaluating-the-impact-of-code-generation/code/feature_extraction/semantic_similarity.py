"""
Semantic Similarity Feature Extraction Module.

This module computes semantic similarity scores for code snippets using CodeBERT embeddings.
These scores are generated for DIAGNOSTIC PURPOSES ONLY and are explicitly EXCLUDED from
matching covariates in the propensity score matching phase to avoid collider bias.

Output: data/processed/diagnostic_scores.parquet
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from tqdm import tqdm

# Hugging Face dependencies
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
except ImportError:
    raise ImportError(
        "Missing required dependencies for semantic similarity. "
        "Please install: pip install transformers torch"
    )

# Project imports
from utils.config import get_config, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "microsoft/codebert-base"
MAX_SEQ_LENGTH = 512
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def load_model_and_tokenizer() -> Tuple[Any, Any]:
    """
    Load the CodeBERT model and tokenizer.

    Returns:
        Tuple: (model, tokenizer)
    """
    logger.info(f"Loading {MODEL_NAME} model and tokenizer on {DEVICE}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.to(DEVICE)
    model.eval()
    logger.info("Model loaded successfully.")
    return model, tokenizer

def get_embeddings_batch(
    snippets: List[str],
    tokenizer: Any,
    model: Any,
    batch_size: int = 8
) -> np.ndarray:
    """
    Compute embeddings for a batch of code snippets.

    Args:
        snippets: List of code snippet strings.
        tokenizer: HuggingFace tokenizer.
        model: HuggingFace model.
        batch_size: Batch size for processing.

    Returns:
        np.ndarray: Array of embeddings (shape: [num_snippets, embedding_dim]).
    """
    embeddings = []
    num_batches = (len(snippets) + batch_size - 1) // batch_size

    logger.info(f"Processing {len(snippets)} snippets in {num_batches} batches...")

    with torch.no_grad():
        for i in tqdm(range(0, len(snippets), batch_size), desc="Embedding"):
            batch = snippets[i : i + batch_size]
            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=MAX_SEQ_LENGTH,
                return_tensors="pt"
            )
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

            outputs = model(**inputs)
            # Use last_hidden_state, take mean over sequence dimension (pooling)
            # Shape: [batch_size, seq_len, hidden_size] -> [batch_size, hidden_size]
            batch_embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            embeddings.append(batch_embeddings)

    return np.vstack(embeddings)

def calculate_similarity(
    embedding_matrix: np.ndarray,
    source_indices: List[int],
    target_indices: List[int]
) -> np.ndarray:
    """
    Calculate cosine similarity between pairs of embeddings.

    Args:
        embedding_matrix: Array of shape [N, D].
        source_indices: Indices of source snippets.
        target_indices: Indices of target snippets.

    Returns:
        np.ndarray: Array of similarity scores.
    """
    if len(source_indices) != len(target_indices):
        raise ValueError("Source and target indices must have the same length.")

    source_vecs = embedding_matrix[source_indices]
    target_vecs = embedding_matrix[target_indices]

    # Normalize vectors
    source_norms = np.linalg.norm(source_vecs, axis=1, keepdims=True)
    target_norms = np.linalg.norm(target_vecs, axis=1, keepdims=True)

    source_normalized = source_vecs / (source_norms + 1e-8)
    target_normalized = target_vecs / (target_norms + 1e-8)

    # Cosine similarity
    similarities = np.sum(source_normalized * target_normalized, axis=1)
    return similarities

def extract_semantic_similarity_scores(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Compute semantic similarity scores for pairs in the dataframe.

    Expected columns in df: 'snippet_id', 'code_content', 'pair_id' (optional).
    If 'pair_id' exists, we compute similarity within pairs.
    If not, we compute similarity between consecutive snippets (or all vs all if small).
    For this task, we assume the dataframe contains pairs of (Human, LLM) snippets
    derived from the same PR or context, identified by a grouping key or sequential pairing.

    Strategy:
    1. Load CodeBERT model.
    2. Generate embeddings for all 'code_content'.
    3. Compute cosine similarity. If the dataframe has a 'pair_id' or 'group_id',
       compute similarity within groups. Otherwise, default to comparing adjacent rows
       if the data is pre-ordered, or just return NaN if pairing is ambiguous.
       Based on typical pipeline outputs from T014b/T012, we expect a 'pr_id' or 'snippet_group'
       to pair Human vs Generated.

    Returns:
        pd.DataFrame: Original dataframe with added 'semantic_similarity_score' column.
    """
    if 'code_content' not in df.columns:
        raise ValueError("Input dataframe must contain 'code_content' column.")

    # Filter out empty content
    valid_mask = df['code_content'].astype(str).str.strip().astype(bool)
    if not valid_mask.all():
        logger.warning(f"Found { (~valid_mask).sum() } empty/NaN snippets. Skipping them for embedding.")
    
    valid_df = df[valid_mask].copy()
    
    if len(valid_df) == 0:
        logger.warning("No valid snippets found to compute embeddings.")
        df['semantic_similarity_score'] = np.nan
        return df

    model, tokenizer = load_model_and_tokenizer()
    
    snippets = valid_df['code_content'].tolist()
    embeddings = get_embeddings_batch(snippets, tokenizer, model)

    # Determine pairing strategy
    if 'group_id' in valid_df.columns:
        # Group by group_id and compute similarity within group (e.g., Human vs LLM)
        # Assuming each group has exactly 2 items (Human, LLM)
        valid_df = valid_df.copy()
        valid_df['embedding_idx'] = range(len(valid_df))
        
        scores = []
        groups = valid_df.groupby('group_id')
        
        for group_id, group_df in groups:
            if len(group_df) < 2:
                # Cannot compute similarity with < 2 items
                scores.extend([np.nan] * len(group_df))
                continue
            
            # Take first two items in the group (assuming sorted or consistent order)
            # If more than 2, we might need specific logic, but for this task we assume pairs
            idx1, idx2 = group_df['embedding_idx'].iloc[0], group_df['embedding_idx'].iloc[1]
            sim = calculate_similarity(embeddings, [idx1], [idx2])[0]
            
            # Assign score to all rows in this group (or just the pair)
            # We'll assign the score to the row that represents the 'generated' or 'target'
            # For simplicity, we assign the score to the second item, and NaN to the first
            # But the requirement is "for every code snippet". Let's assign the pair score to both?
            # Or better: The score represents the relationship. Let's assign the score to the 'generated' snippet
            # if we can identify it. If not, we assign to the second row.
            
            # Simpler approach: Just assign the computed score to the second row of the pair, 
            # and NaN to the first, or duplicate. 
            # Given the diagnostic nature, let's assign the similarity to the 'generated' snippet.
            # If we don't have a label, we'll just assign to the second row.
            
            row_indices = group_df.index.tolist()
            for idx in row_indices:
                scores.append(np.nan) # Initialize
            
            # Actually, let's just fill the second one
            scores_dict = {idx: np.nan for idx in row_indices}
            scores_dict[row_indices[1]] = sim
            
            for idx, score in scores_dict.items():
                # We need to map back to the global dataframe index later
                # This is getting complex. Let's simplify:
                # Just compute similarity between row i and row i+1 if no groups, 
                # or if groups, between the two in the group.
                pass

        # Re-implementation for clarity:
        # Create a series for scores, initialized to NaN
        score_series = pd.Series(np.nan, index=df.index)
        
        for group_id, group_df in groups:
            if len(group_df) < 2:
                continue
            
            group_indices = group_df.index.tolist()
            # Compute similarity between first and second
            idx1 = group_indices[0]
            idx2 = group_indices[1]
            
            # Find positions in the valid_df list
            # valid_df is a subset of df, but we need to map back to embeddings
            # valid_df['embedding_idx'] maps valid_df rows to embeddings list
            # But we need to map df index to embedding index
            pass

        # Let's do a simpler mapping:
        # 1. Create a map from df index to embedding index for valid rows
        idx_map = {idx: i for i, idx in enumerate(valid_df.index)}
        
        score_series = pd.Series(np.nan, index=df.index)
        
        for group_id, group_df in groups:
            if len(group_df) < 2:
                continue
            
            group_indices = group_df.index.tolist()
            if group_indices[0] not in idx_map or group_indices[1] not in idx_map:
                continue
                
            pos1 = idx_map[group_indices[0]]
            pos2 = idx_map[group_indices[1]]
            
            sim = calculate_similarity(embeddings, [pos1], [pos2])[0]
            
            # Assign to the second item (assuming it's the generated one or the one we care about)
            # Or assign to both? The task says "for every code snippet".
            # Let's assign the score to the second one in the pair, as the 'diagnostic' for that snippet.
            score_series[group_indices[1]] = sim
            # Also assign to the first? Usually similarity is symmetric.
            score_series[group_indices[0]] = sim

        df['semantic_similarity_score'] = score_series

    elif len(valid_df) >= 2:
        # Fallback: Compute similarity between consecutive snippets if no group_id
        # This is a heuristic.
        logger.warning("No 'group_id' found. Computing similarity between consecutive snippets as fallback.")
        score_series = pd.Series(np.nan, index=df.index)
        idx_map = {idx: i for i, idx in enumerate(valid_df.index)}
        
        # Iterate through valid_df rows and compute sim with next
        for i in range(len(valid_df) - 1):
            idx1 = valid_df.index[i]
            idx2 = valid_df.index[i+1]
            
            if idx1 in idx_map and idx2 in idx_map:
                pos1 = idx_map[idx1]
                pos2 = idx_map[idx2]
                sim = calculate_similarity(embeddings, [pos1], [pos2])[0]
                score_series[idx1] = sim
                score_series[idx2] = sim
        
        df['semantic_similarity_score'] = score_series
    else:
        logger.warning("Not enough snippets to compute similarity.")
        df['semantic_similarity_score'] = np.nan

    return df

def process_dataset(
    input_path: str,
    output_path: str
) -> None:
    """
    Main processing function: Load data, compute embeddings, calculate similarity, save results.

    Args:
        input_path: Path to input parquet file (e.g., data/processed/generated_snippets.parquet).
        output_path: Path to output parquet file (data/processed/diagnostic_scores.parquet).
    """
    logger.info(f"Loading dataset from {input_path}...")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    
    logger.info(f"Loaded {len(df)} rows. Computing semantic similarity scores...")
    
    df_with_scores = extract_semantic_similarity_scores(df)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}...")
    df_with_scores.to_parquet(output_path, index=False)
    
    logger.info("Semantic similarity extraction complete.")

def main():
    """Entry point for the script."""
    config = get_config()
    
    # Default paths
    input_file = config.get('paths', {}).get('generated_snippets', 'data/processed/generated_snippets.parquet')
    output_file = 'data/processed/diagnostic_scores.parquet'
    
    # Override with command line args if provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    try:
        process_dataset(input_file, output_file)
    except Exception as e:
        logger.error(f"Failed to process dataset: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
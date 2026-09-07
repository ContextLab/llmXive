import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Attempt to import torch and transformers.
# If not installed, the script will fail loudly as per constraints (no synthetic fallback).
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning(
        "transformers/sentence-transformers not found. "
        "Semantic similarity extraction requires these packages. "
        "Please install them via requirements.txt."
    )

from utils.config import get_config, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # Lightweight, CPU-friendly, real semantic embeddings
MAX_BATCH_SIZE = 32
OUTPUT_FILE = "data/processed/diagnostic_scores.parquet"

def load_model_and_tokenizer() -> Tuple[Any, Any]:
    """
    Loads the pre-trained sentence transformer model and tokenizer.
    Returns a tuple of (model, tokenizer).
    """
    if not HAS_TRANSFORMERS:
        raise ImportError(
            "Required libraries 'transformers' and 'sentence-transformers' are missing. "
            "Cannot load model. Install dependencies to proceed."
        )

    logger.info(f"Loading model: {MODEL_NAME}")
    # Using SentenceTransformer for ease of use and robust pooling
    model = SentenceTransformer(MODEL_NAME)
    tokenizer = model.tokenizer  # Access tokenizer from the wrapper if needed, or use model.encode directly

    # Move to CUDA if available, else CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    logger.info(f"Model loaded on device: {device}")
    return model, tokenizer

def get_embeddings_batch(
    model: Any,
    texts: List[str],
    batch_size: int = MAX_BATCH_SIZE
) -> np.ndarray:
    """
    Computes embeddings for a batch of texts.
    Returns a numpy array of shape (num_texts, embedding_dim).
    """
    if not HAS_TRANSFORMERS:
        raise ImportError("Model loading failed; cannot compute embeddings.")

    # sentence-transformers handles batching internally efficiently
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        device=model.device if hasattr(model, 'device') else "cpu"
    )
    return embeddings

def calculate_similarity(embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
    """
    Calculates cosine similarity between two 1D embedding vectors.
    """
    if embedding_a.shape != embedding_b.shape:
        raise ValueError("Embeddings must have the same shape.")

    norm_a = np.linalg.norm(embedding_a)
    norm_b = np.linalg.norm(embedding_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(embedding_a, embedding_b) / (norm_a * norm_b))

def extract_semantic_similarity_scores(
    df: pd.DataFrame,
    text_column: str = "code_snippet",
    reference_text: Optional[str] = None
) -> pd.DataFrame:
    """
    Computes semantic similarity scores for the dataset.
    
    Strategy per Task T017b:
    - These scores are for a Secondary Diagnostic Report ONLY.
    - They are EXCLUDED from matching covariates.
    - We compute similarity of each snippet to a "canonical" reference if provided,
      or compute pairwise similarity within the batch if no reference is given.
    
    For this diagnostic, we will compute the mean embedding of the "Human" class
    (if available in the dataframe) as a reference, and score all snippets against it.
    If no class labels exist, we simply return the embeddings themselves as a diagnostic
    feature (e.g., mean magnitude) or a placeholder column indicating "uncomputed".
    
    However, the task specifically asks for "similarity scores".
    Let's assume the dataframe has a 'classification' column (from T014) with values 'Human'/'LLM-like'.
    We will calculate the centroid of the 'Human' class and compute cosine similarity
    of every snippet to that centroid.
    """
    if not HAS_TRANSFORMERS:
        raise ImportError("Cannot extract scores: missing transformers libraries.")

    if text_column not in df.columns:
        raise KeyError(f"Text column '{text_column}' not found in dataframe.")

    # Filter out empty or NaN snippets
    valid_indices = df[text_column].notna() & (df[text_column] != "")
    df_valid = df[valid_indices].copy()

    if len(df_valid) == 0:
        logger.warning("No valid text snippets found in dataset.")
        df["semantic_similarity_score"] = np.nan
        return df

    logger.info(f"Processing {len(df_valid)} snippets for semantic similarity...")
    
    # Load model
    model, _ = load_model_and_tokenizer()

    # Get embeddings for all valid snippets
    texts = df_valid[text_column].tolist()
    embeddings = get_embeddings_batch(model, texts)

    # Determine reference strategy
    if "classification" in df_valid.columns:
        # Use Human class centroid as reference
        human_mask = df_valid["classification"] == "Human"
        if human_mask.sum() > 0:
            human_embeddings = embeddings[human_mask.values]
            reference_embedding = np.mean(human_embeddings, axis=0)
            logger.info(f"Using Human class centroid (n={human_mask.sum()}) as reference.")
        else:
            # Fallback: use global mean
            reference_embedding = np.mean(embeddings, axis=0)
            logger.warning("No 'Human' class found. Using global mean as reference.")
    else:
        # Fallback: use global mean
        reference_embedding = np.mean(embeddings, axis=0)
        logger.warning("No 'classification' column found. Using global mean as reference.")

    # Calculate similarity for each snippet
    similarities = []
    for emb in embeddings:
        sim = calculate_similarity(emb, reference_embedding)
        similarities.append(sim)

    # Map scores back to the original dataframe
    # Create a series aligned with df_valid index
    score_series = pd.Series(similarities, index=df_valid.index, name="semantic_similarity_score")
    
    # Assign to the original dataframe
    df["semantic_similarity_score"] = np.nan
    df.loc[df_valid.index, "semantic_similarity_score"] = score_series

    logger.info("Semantic similarity scores computed successfully.")
    return df

def process_dataset(
    input_path: str,
    output_path: str,
    text_column: str = "code_snippet"
) -> None:
    """
    Main processing pipeline:
    1. Load dataset from input_path (parquet or csv).
    2. Compute semantic similarity scores.
    3. Save to output_path (parquet).
    """
    logger.info(f"Starting processing pipeline for {input_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        ensure_directories([output_dir])

    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading dataset from {input_path}")
    if input_path.endswith(".parquet"):
        df = pd.read_parquet(input_path)
    elif input_path.endswith(".csv"):
        df = pd.read_csv(input_path)
    else:
        raise ValueError("Unsupported file format. Use .parquet or .csv.")

    logger.info(f"Loaded {len(df)} rows.")

    # Process
    try:
        df_processed = extract_semantic_similarity_scores(df, text_column=text_column)
    except Exception as e:
        logger.error(f"Error during similarity extraction: {e}")
        # Re-raise to fail loudly as per constraints
        raise

    # Save
    logger.info(f"Saving results to {output_path}")
    df_processed.to_parquet(output_path, index=False)
    logger.info("Pipeline completed.")

def main():
    """
    Entry point for the script.
    Reads config for paths, processes the classified snippets, and outputs diagnostic scores.
    """
    config = get_config()
    
    # Default paths based on project structure and task description
    # The task references `data/processed/classified_snippets.parquet` as input (from T014)
    # and `data/processed/diagnostic_scores.parquet` as output.
    input_file = config.get("paths", {}).get("classified_snippets", "data/processed/classified_snippets.parquet")
    output_file = config.get("paths", {}).get("diagnostic_scores", "data/processed/diagnostic_scores.parquet")
    
    # Allow override via command line args
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        process_dataset(input_file, output_file)
        print(f"Successfully generated diagnostic scores at: {output_file}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
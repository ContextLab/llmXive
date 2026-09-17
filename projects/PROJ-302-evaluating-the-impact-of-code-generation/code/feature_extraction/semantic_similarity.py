import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
except ImportError:
    print("Error: transformers or torch not installed. Please install dependencies.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "microsoft/codebert-base"
MAX_SEQ_LENGTH = 512
DEVICE = "cpu"  # Enforce CPU as per constraints
BATCH_SIZE = 8

def load_model_and_tokenizer() -> Tuple[Any, Any]:
    """
    Load the pre-trained CodeBERT model and tokenizer.
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading model: {MODEL_NAME} on {DEVICE}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.to(DEVICE)
    model.eval()
    logger.info("Model loaded successfully.")
    return model, tokenizer

def preprocess_snippet(code_snippet: str) -> Dict[str, Any]:
    """
    Preprocess a code snippet for tokenization.
    Args:
        code_snippet: Raw code string
    Returns:
        Dictionary of tokenized inputs
    """
    if not isinstance(code_snippet, str) or not code_snippet.strip():
        raise ValueError("Invalid code snippet provided.")
    
    # Truncate if necessary and tokenize
    inputs = tokenizer(
        code_snippet,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=MAX_SEQ_LENGTH
    )
    return inputs

def get_embeddings_batch(model: Any, tokenizer: Any, snippets: List[str]) -> np.ndarray:
    """
    Compute embeddings for a batch of code snippets.
    Args:
        model: Loaded transformer model
        tokenizer: Loaded transformer tokenizer
        snippets: List of code strings
    Returns:
        Numpy array of shape (num_snippets, embedding_dim)
    """
    embeddings = []
    model.eval()
    
    # Process in batches to manage memory
    for i in range(0, len(snippets), BATCH_SIZE):
        batch_snippets = snippets[i:i + BATCH_SIZE]
        inputs = tokenizer(
            batch_snippets,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=MAX_SEQ_LENGTH
        )
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            # Use last hidden state mean pooling for sentence embedding
            # [batch, seq_len, hidden] -> [batch, hidden]
            last_hidden_states = outputs.last_hidden_state
            attention_mask = inputs['attention_mask']
            
            # Mask padding tokens
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
            sum_embeddings = torch.sum(last_hidden_states * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            batch_embeddings = sum_embeddings / sum_mask
            
            embeddings.append(batch_embeddings.cpu().numpy())
    
    return np.vstack(embeddings)

def calculate_similarity(embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.
    Args:
        embedding_a: 1D numpy array
        embedding_b: 1D numpy array
    Returns:
        Cosine similarity score (float)
    """
    norm_a = np.linalg.norm(embedding_a)
    norm_b = np.linalg.norm(embedding_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(embedding_a, embedding_b) / (norm_a * norm_b))

def extract_semantic_similarity_scores(df: pd.DataFrame, model: Any, tokenizer: Any) -> pd.DataFrame:
    """
    Compute semantic similarity scores for all code snippets in the DataFrame.
    Since we need to compare every snippet to a reference or compute pairwise,
    and the task implies diagnostic scores for the dataset, we will compute
    embeddings for all snippets.
    
    For a "score" per row in a diagnostic context without a specific pair target,
    we calculate the mean embedding of the entire dataset and compute the
    cosine similarity of each snippet to the global mean embedding.
    This serves as a density/centrality metric for diagnostics.
    
    Args:
        df: DataFrame containing 'code_snippet' column
        model: Loaded model
        tokenizer: Loaded tokenizer
    Returns:
        DataFrame with added 'semantic_similarity_score' column
    """
    if 'code_snippet' not in df.columns:
        raise KeyError("Input DataFrame must contain 'code_snippet' column.")
    
    logger.info(f"Processing {len(df)} snippets for semantic embeddings...")
    
    # Filter valid snippets
    valid_indices = []
    valid_snippets = []
    for idx, row in df.iterrows():
        snippet = row['code_snippet']
        if isinstance(snippet, str) and snippet.strip():
            valid_indices.append(idx)
            valid_snippets.append(snippet)
    
    if not valid_snippets:
        logger.warning("No valid code snippets found.")
        df['semantic_similarity_score'] = 0.0
        return df

    # Get embeddings for all valid snippets
    embeddings = get_embeddings_batch(model, tokenizer, valid_snippets)
    
    # Compute global mean embedding
    global_mean = embeddings.mean(axis=0)
    
    # Compute similarity of each snippet to the global mean
    scores = []
    for emb in embeddings:
        score = calculate_similarity(emb, global_mean)
        scores.append(score)
    
    # Map scores back to original indices
    score_map = dict(zip(valid_indices, scores))
    df['semantic_similarity_score'] = df.index.map(lambda x: score_map.get(x, 0.0))
    
    logger.info(f"Computed semantic scores for {len(valid_snippets)} snippets.")
    return df

def process_dataset(input_path: str, output_path: str) -> None:
    """
    Main processing pipeline:
    1. Load data from input_path
    2. Compute semantic scores
    3. Save to output_path
    
    Args:
        input_path: Path to input parquet/csv file
        output_path: Path to output parquet file
    """
    logger.info(f"Starting semantic similarity extraction from {input_path}")
    
    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if input_path.endswith('.parquet'):
        df = pd.read_parquet(input_path)
    elif input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        raise ValueError("Unsupported input file format. Use .parquet or .csv")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Load model
    model, tokenizer = load_model_and_tokenizer()
    
    # Extract scores
    df_result = extract_semantic_similarity_scores(df, model, tokenizer)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save results
    df_result.to_parquet(output_path, index=False)
    logger.info(f"Successfully saved results to {output_path}")

def main():
    """
    Entry point for the script.
    Reads from data/processed/classified_snippets.parquet (if exists) 
    or a specified input, and writes to data/processed/semantic_scores.parquet.
    """
    # Default paths relative to project root
    # The task description says output: data/processed/semantic_scores.parquet
    # We assume the input is the classified snippets from T014b-NEW
    input_file = "data/processed/classified_snippets.parquet"
    output_file = "data/processed/semantic_scores.parquet"
    
    # Allow override via command line
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    
    try:
        process_dataset(input_file, output_file)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
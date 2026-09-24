import logging
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import hashlib
import os

# Conditional imports for heavy dependencies
try:
    import torch
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None
    torch = None

from config import get_path, get_device, get_max_workers, set_seed, get_seed
from utils import setup_logging, get_logger, normalize_text

logger = get_logger(__name__)

# Constants
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 32

def get_embedding_model() -> Optional[SentenceTransformer]:
    """
    Load the sentence transformer model.
    Returns None if dependencies are missing.
    """
    if not HAS_SENTENCE_TRANSFORMERS:
        logger.error("sentence-transformers or torch not installed. Cannot load model.")
        return None
    
    device = get_device()
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME} on {device}")
    
    # Ensure reproducibility
    set_seed(get_seed())
    
    try:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        model.to(device)
        model.eval()
        return model
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return None

def clean_text_for_embedding(text: str) -> str:
    """
    Clean text for embedding: normalize, remove extra whitespace.
    """
    if not isinstance(text, str):
        return ""
    text = normalize_text(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_semantic_features(
    texts: List[str], 
    model: SentenceTransformer,
    batch_size: int = BATCH_SIZE
) -> np.ndarray:
    """
    Extract sentence embeddings for a list of texts.
    Returns a numpy array of shape [N, 384].
    Uses torch.no_grad() and batching to prevent OOM.
    """
    if not HAS_SENTENCE_TRANSFORMERS:
        raise RuntimeError("sentence-transformers not available")
    
    cleaned_texts = [clean_text_for_embedding(t) for t in texts]
    # Filter out empty texts to avoid model errors, though they should be handled upstream
    valid_indices = [i for i, t in enumerate(cleaned_texts) if len(t) > 0]
    invalid_indices = [i for i, t in enumerate(cleaned_texts) if len(t) == 0]
    
    if invalid_indices:
        logger.warning(f"Skipping {len(invalid_indices)} empty/invalid texts for embedding.")
    
    if not valid_indices:
        # Return zeros if no valid texts, shape [N, 384]
        return np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)
    
    valid_texts = [cleaned_texts[i] for i in valid_indices]
    
    embeddings_list = []
    
    logger.info(f"Processing {len(valid_texts)} texts in batches of {batch_size}")
    
    with torch.no_grad():
        for i in range(0, len(valid_texts), batch_size):
            batch_texts = valid_texts[i:i+batch_size]
            try:
                batch_embeddings = model.encode(
                    batch_texts, 
                    convert_to_numpy=True, 
                    show_progress_bar=False,
                    device=get_device()
                )
                embeddings_list.append(batch_embeddings)
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size}: {e}")
                raise
    
    if not embeddings_list:
        return np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)
    
    full_embeddings = np.vstack(embeddings_list)
    
    # Reconstruct full array with zeros for invalid entries
    final_embeddings = np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)
    final_embeddings[valid_indices] = full_embeddings
    
    return final_embeddings

def calculate_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Calculate the cosine similarity matrix for a set of embeddings.
    Returns a matrix of shape [N, N].
    """
    # Normalize embeddings to unit length for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1.0
    unit_embeddings = embeddings / norms
    
    similarity_matrix = np.dot(unit_embeddings, unit_embeddings.T)
    return similarity_matrix

def calculate_participant_similarity(embeddings: np.ndarray) -> np.ndarray:
    """
    Calculate the self-similarity (diagonal of the cosine similarity matrix) 
    for each participant's embeddings. 
    
    Note: If a participant has multiple sentences, we first average their embeddings
    or calculate similarity within their own cluster. 
    
    However, the task T024b asks for 'Sentence Embedding Cosine Similarity' (self-similarity).
    In the context of a single transcript per participant, this usually means:
    1. If the transcript is treated as a bag of sentences, we compute the average 
       cosine similarity between all pairs of sentences within that transcript.
    2. Or, if we treat the transcript as a single vector (by averaging sentence vectors),
       the self-similarity is trivially 1.0.
    
    Given the feature extraction context (US2), we interpret this as:
    "For each participant, compute the average cosine similarity between all pairs 
    of their sentence embeddings." This measures internal coherence.
    
    Input: embeddings of shape [Total_Sentences, 384]
    We need to group by participant_id first.
    """
    # This function is intended to be called after we have participant groupings.
    # However, if called directly on a flat array without grouping info, 
    # we cannot compute per-participant metrics.
    # We will implement the logic to accept a list of lists (per participant) 
    # or handle the grouping inside the main extraction function.
    
    # Placeholder for the specific logic that requires grouping.
    # The actual calculation happens in extract_all_features.
    return None

def extract_all_features(
    df: pd.DataFrame, 
    model: SentenceTransformer
) -> pd.DataFrame:
    """
    Extract all features (lexical, syntactic, semantic) and append to dataframe.
    This function assumes T024 (embeddings) has been run or runs it here.
    """
    if HAS_SENTENCE_TRANSFORMERS is False:
        raise RuntimeError("sentence-transformers not installed")

    # 1. Extract Semantic Features (Embeddings)
    logger.info("Extracting sentence embeddings...")
    texts = df['text'].tolist()
    
    # We need to handle the case where a row might contain multiple sentences
    # or the whole transcript. The prompt implies 'Sentence Embedding Cosine Similarity'
    # is a feature of the participant.
    # Strategy: 
    #   - Split text into sentences.
    #   - Embed all sentences.
    #   - For each participant, compute the average pairwise cosine similarity of their sentences.
    
    # Simple sentence splitting (could be improved with spaCy, but keeping it light)
    # We'll assume the 'text' column contains the full transcript.
    # We need to track which sentence belongs to which participant.
    
    participant_ids = df['participant_id'].tolist()
    participant_indices = {}
    for i, pid in enumerate(participant_ids):
        if pid not in participant_indices:
            participant_indices[pid] = []
        participant_indices[pid].append(i)
    
    # Collect all sentences and their participant IDs
    all_sentences = []
    sentence_to_participant = []
    
    for idx, row in df.iterrows():
        text = row['text']
        if not isinstance(text, str) or len(text.strip()) == 0:
            continue
        # Split by basic punctuation for sentence approximation
        # Using regex to split on ., !, ?
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for sent in sentences:
            sent_clean = clean_text_for_embedding(sent)
            if len(sent_clean) > 10: # Minimum length for meaningful embedding
                all_sentences.append(sent_clean)
                sentence_to_participant.append(row['participant_id'])
    
    if not all_sentences:
        logger.warning("No valid sentences found for embedding.")
        df['Sentence_Embedding_Cosine_Similarity'] = 0.0
        return df

    logger.info(f"Embedding {len(all_sentences)} sentences...")
    sentence_embeddings = extract_semantic_features(all_sentences, model)
    
    # Calculate self-similarity per participant
    # Group embeddings by participant
    participant_similarities = {}
    
    # Convert to list for easier manipulation
    sentence_embeddings_list = list(sentence_embeddings)
    
    # Map participant_id to list of embedding indices
    pid_to_indices = {}
    for i, pid in enumerate(sentence_to_participant):
        if pid not in pid_to_indices:
            pid_to_indices[pid] = []
        pid_to_indices[pid].append(i)
    
    logger.info("Calculating self-similarity per participant...")
    for pid, indices in pid_to_indices.items():
        if len(indices) < 2:
            # Only one sentence, self-similarity is 1.0 (or undefined, let's say 1.0)
            participant_similarities[pid] = 1.0
            continue
        
        # Get embeddings for this participant
        p_embs = sentence_embeddings_list[indices[0]:indices[1]+1] if len(indices)==1 else [sentence_embeddings_list[i] for i in indices]
        p_embs = np.array(p_embs)
        
        # Calculate cosine similarity matrix for this participant's sentences
        # Normalize
        norms = np.linalg.norm(p_embs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        unit_p_embs = p_embs / norms
        
        sim_matrix = np.dot(unit_p_embs, unit_p_embs.T)
        
        # Extract upper triangle (excluding diagonal) to get pairwise similarities
        # We want the average similarity between distinct sentences
        upper_tri_indices = np.triu_indices(len(p_embs), k=1)
        if len(upper_tri_indices[0]) > 0:
            avg_sim = np.mean(sim_matrix[upper_tri_indices])
        else:
            avg_sim = 1.0 # Only one sentence effectively
        
        participant_similarities[pid] = avg_sim

    # Map back to the original dataframe
    df['Sentence_Embedding_Cosine_Similarity'] = df['participant_id'].map(participant_similarities)
    
    # Fill NaN if any participant was missed (shouldn't happen if logic is correct)
    df['Sentence_Embedding_Cosine_Similarity'] = df['Sentence_Embedding_Cosine_Similarity'].fillna(1.0)

    return df

def process_dataset(
    input_path: str, 
    output_path: str
) -> None:
    """
    Main pipeline function to load data, extract embeddings, calculate self-similarity,
    and save the feature matrix.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['participant_id', 'text', 'label']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    model = get_embedding_model()
    if model is None:
        raise RuntimeError("Could not initialize embedding model")
    
    # Extract features
    logger.info("Extracting features...")
    df_features = extract_all_features(df, model)
    
    # Select columns for output
    # We need to include the new column 'Sentence_Embedding_Cosine_Similarity'
    # and other existing features if any.
    # The task implies appending to the feature matrix.
    # Assuming the input CSV already has some features (T022, T023) or just raw data.
    # We will output all columns except 'text' to keep it compact, or all if needed.
    # Let's keep all non-text columns.
    output_cols = [c for c in df_features.columns if c != 'text']
    df_output = df_features[output_cols]
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving features to {output_path}")
    df_output.to_csv(output_path, index=False)
    
    # Also save embeddings if needed for T024c? 
    # T024b specifically asks to append the column.
    # T024 asks to save embeddings.npy. We should ensure that happens too if not done.
    # But T024 is marked done. We assume embeddings.npy exists or is generated here.
    # Let's generate embeddings.npy as part of this flow to be safe, 
    # mapping back to participants if possible, or just saving the sentence embeddings?
    # The spec says: "Save embeddings to data/processed/embeddings.npy (shape [N, 384])"
    # where N is participants? Or sentences? 
    # T024 says "shape [N, 384] where D=384". Usually N=participants in feature matrix context.
    # If we average sentence embeddings per participant to get a participant vector:
    
    logger.info("Generating participant-level embeddings for storage...")
    participant_embeddings = {}
    for pid, indices in pid_to_indices.items():
        p_embs = np.array([sentence_embeddings_list[i] for i in indices])
        participant_embeddings[pid] = np.mean(p_embs, axis=0)
    
    # Order by participant_id to match the dataframe
    ordered_pids = df['participant_id'].unique()
    final_embeddings = np.array([participant_embeddings[pid] for pid in ordered_pids], dtype=np.float32)
    
    embeddings_path = str(Path(output_path).parent / "embeddings.npy")
    np.save(embeddings_path, final_embeddings)
    logger.info(f"Saved embeddings to {embeddings_path}")
    
    # Generate derivation log
    log_path = str(Path(output_path).parent / "embeddings.derivation.log")
    with open(log_path, 'w') as f:
        f.write(f"Participant Count: {len(ordered_pids)}\n")
        f.write(f"Embedding Dimension: {EMBEDDING_DIM}\n")
        f.write(f"Model: {EMBEDDING_MODEL_NAME}\n")
        f.write(f"Self-similarity calculated as average pairwise cosine similarity of sentences.\n")
    
    logger.info("Feature extraction complete.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract features and calculate self-similarity")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    args = parser.parse_args()
    
    setup_logging()
    process_dataset(args.input, args.output)

if __name__ == "__main__":
    main()
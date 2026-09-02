"""
Feature extraction module for cognitive decline analysis.
Implements lexical, syntactic, and semantic feature extraction.
"""
import logging
import re
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import spacy
from sentence_transformers import SentenceTransformer
from config import get_path, get_max_workers, set_seed, get_seed
from utils import get_logger, normalize_text

# Constants
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 32

logger = get_logger(__name__)

# Lexical Feature Functions
def calculate_ttr(text: str) -> float:
    """Calculate Type-Token Ratio."""
    if not text or not isinstance(text, str):
        return 0.0
    tokens = re.findall(r'\b\w+\b', text.lower())
    if not tokens:
        return 0.0
    unique_tokens = set(tokens)
    return len(unique_tokens) / len(tokens)

def calculate_mtld(text: str) -> float:
    """Calculate Measure of Textual Lexical Diversity (MTLD)."""
    if not text or not isinstance(text, str):
        return 0.0
    tokens = re.findall(r'\b\w+\b', text.lower())
    if len(tokens) < 50:
        return 0.0
    
    # Simplified MTLD calculation (forward direction)
    # This is a simplified version for performance; full implementation would be more complex
    segment_length = 0
    types = set()
    mtld_sum = 0.0
    count = 0
    
    for token in tokens:
        segment_length += 1
        types.add(token)
        ttr = len(types) / segment_length
        
        if ttr < 0.72: # Threshold for MTLD
            # Calculate MTLD for this segment
            mtld_sum += segment_length
            count += 1
            segment_length = 0
            types = set()
    
    if count == 0:
        return 100.0 # Default if no segments crossed threshold
    
    return mtld_sum / count

def calculate_noun_verb_ratio(text: str, nlp) -> float:
    """Calculate Noun to Verb ratio."""
    if not text or not isinstance(text, str):
        return 0.0
    doc = nlp(text)
    nouns = [token for token in doc if token.pos_ in ('NOUN', 'PROPN')]
    verbs = [token for token in doc if token.pos_ == 'VERB']
    
    if not verbs:
        return 0.0 if not nouns else float('inf')
    return len(nouns) / len(verbs)

def extract_lexical_features(texts: List[str], nlp) -> pd.DataFrame:
    """Extract lexical features for a list of texts."""
    features = []
    for text in texts:
        norm_text = normalize_text(text) if isinstance(text, str) else ""
        row = {
            'ttr': calculate_ttr(norm_text),
            'mtld': calculate_mtld(norm_text),
            'noun_verb_ratio': calculate_noun_verb_ratio(norm_text, nlp)
        }
        features.append(row)
    return pd.DataFrame(features)

# Syntactic Feature Functions
def calculate_mean_clause_length(text: str, nlp) -> float:
    """Calculate mean clause length."""
    if not text or not isinstance(text, str):
        return 0.0
    doc = nlp(text)
    clauses = [sent for sent in doc.sents]
    if not clauses:
        return 0.0
    
    total_tokens = 0
    clause_count = 0
    
    for clause in clauses:
        tokens = [token for token in clause if not token.is_space and not token.is_punct]
        if tokens:
            total_tokens += len(tokens)
            clause_count += 1
    
    return total_tokens / clause_count if clause_count > 0 else 0.0

def calculate_t_unit_count(text: str, nlp) -> int:
    """Calculate T-unit count (main clause + dependent clauses)."""
    if not text or not isinstance(text, str):
        return 0
    doc = nlp(text)
    # Simplified: count sentences as T-units for now
    # A more robust implementation would parse dependency trees
    return len(list(doc.sents))

def extract_syntactic_features(texts: List[str], nlp) -> pd.DataFrame:
    """Extract syntactic features for a list of texts."""
    features = []
    for text in texts:
        norm_text = normalize_text(text) if isinstance(text, str) else ""
        row = {
            'mean_clause_length': calculate_mean_clause_length(norm_text, nlp),
            't_unit_count': calculate_t_unit_count(norm_text, nlp)
        }
        features.append(row)
    return pd.DataFrame(features)

# Semantic Feature Functions
def extract_semantic_features(texts: List[str]) -> np.ndarray:
    """
    Extract semantic features using sentence embeddings.
    Returns a numpy array of shape [N, 384] with dtype float32.
    """
    if not texts:
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

    logger.info(f"Loading semantic embedding model: {EMBEDDING_MODEL_NAME}")
    # Load model in CPU-only mode as per constraints
    model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
    
    # Preprocess texts
    processed_texts = []
    for text in texts:
        if isinstance(text, str) and text.strip():
            processed_texts.append(normalize_text(text))
        else:
            processed_texts.append("") # Handle empty/invalid texts

    # Filter out completely empty strings to avoid model errors
    valid_indices = [i for i, t in enumerate(processed_texts) if t.strip()]
    valid_texts = [processed_texts[i] for i in valid_indices]

    if not valid_texts:
        logger.warning("No valid texts found for embedding generation.")
        # Return zeros for all original texts
        return np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)

    logger.info(f"Generating embeddings for {len(valid_texts)} texts...")
    # Generate embeddings in batches to manage memory
    embeddings_list = []
    
    for i in range(0, len(valid_texts), BATCH_SIZE):
        batch = valid_texts[i:i+BATCH_SIZE]
        batch_embeddings = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
        embeddings_list.append(batch_embeddings)
    
    all_embeddings = np.vstack(embeddings_list)
    
    # Ensure correct dtype
    all_embeddings = all_embeddings.astype(np.float32)
    
    # Create full embeddings array (including zeros for invalid texts)
    full_embeddings = np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)
    full_embeddings[valid_indices] = all_embeddings
    
    logger.info(f"Semantic embeddings generated with shape: {full_embeddings.shape}, dtype: {full_embeddings.dtype}")
    return full_embeddings

def extract_all_features(df: pd.DataFrame, nlp) -> pd.DataFrame:
    """Extract all features (lexical, syntactic, semantic) from a DataFrame."""
    texts = df['text'].tolist()
    
    logger.info("Extracting lexical features...")
    lexical_df = extract_lexical_features(texts, nlp)
    
    logger.info("Extracting syntactic features...")
    syntactic_df = extract_syntactic_features(texts, nlp)
    
    logger.info("Extracting semantic features...")
    semantic_embeddings = extract_semantic_features(texts)
    
    # Combine lexical and syntactic features
    features_df = pd.concat([df.reset_index(drop=True), lexical_df, syntactic_df], axis=1)
    
    # Save embeddings to file
    output_path = get_path('processed_embeddings')
    np.save(output_path, semantic_embeddings)
    logger.info(f"Saved embeddings to {output_path}")
    
    return features_df

def process_dataset(input_path: str, output_path: str) -> None:
    """
    Process a dataset file, extract all features, and save the results.
    Also saves semantic embeddings to data/processed/embeddings.npy
    """
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'text' not in df.columns:
        raise ValueError("Input dataset must contain a 'text' column")
    
    logger.info(f"Loaded {len(df)} records")
    
    # Load spaCy model
    logger.info("Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm")
    
    # Extract features
    features_df = extract_all_features(df, nlp)
    
    # Save feature matrix
    logger.info(f"Saving feature matrix to {output_path}")
    features_df.to_csv(output_path, index=False)
    
    logger.info("Feature extraction completed successfully")

def main():
    """Main entry point for feature extraction."""
    set_seed(get_seed())
    
    input_path = get_path('interim_cleaned')
    output_path = get_path('processed_features')
    
    process_dataset(input_path, output_path)

if __name__ == "__main__":
    main()

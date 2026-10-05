import logging
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import spacy
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
from config import get_path, get_max_workers, get_device

logger = logging.getLogger(__name__)

# Global cache for NLP models to avoid reloading
_nlp_model = None
_embedding_model = None

def get_nlp_model():
    """Load spaCy model (en_core_web_sm) with caching."""
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            # If model not found, try to download it
            logger.warning("spaCy model not found. Attempting download...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            _nlp_model = spacy.load("en_core_web_sm")
            logger.info("Downloaded and loaded spaCy model: en_core_web_sm")
    return _nlp_model

def get_embedding_model():
    """Load sentence transformer model with caching."""
    global _embedding_model
    if _embedding_model is None:
        device = get_device()
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        logger.info(f"Loading embedding model: {model_name} on {device}")
        _embedding_model = SentenceTransformer(model_name, device=device)
        logger.info("Loaded embedding model successfully")
    return _embedding_model

def clean_text_for_embedding(text: str) -> str:
    """Clean text specifically for embedding generation."""
    if not isinstance(text, str):
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable())
    return text

def extract_ttr(text: str) -> float:
    """Calculate Type-Token Ratio (TTR)."""
    if not text or not isinstance(text, str):
        return 0.0
    tokens = text.lower().split()
    if not tokens:
        return 0.0
    unique_tokens = set(tokens)
    return len(unique_tokens) / len(tokens)

def extract_mtld(text: str) -> float:
    """Calculate Mean Length of Textual Discourse (MTLD)."""
    if not text or not isinstance(text, str):
        return 0.0
    
    tokens = text.lower().split()
    if len(tokens) < 50:
        # Not enough tokens for a reliable MTLD
        return 0.0
    
    # Simplified MTLD calculation (Maclaurin's method)
    # Count how many segments of 50 words maintain a TTR >= 0.72
    segment_length = 50
    min_ttr = 0.72
    valid_segments = 0
    total_segments = 0
    
    for i in range(0, len(tokens) - segment_length + 1, segment_length):
        segment = tokens[i:i+segment_length]
        unique = len(set(segment))
        ttr = unique / len(segment)
        total_segments += 1
        if ttr >= min_ttr:
            valid_segments += 1
    
    if total_segments == 0:
        return 0.0
    
    # MTLD is the average length of segments that meet the TTR threshold
    # Simplified: return the proportion of valid segments * segment_length
    return (valid_segments / total_segments) * segment_length

def extract_noun_verb_ratio(text: str) -> float:
    """
    Calculate Noun/Verb Ratio.
    Uses spaCy to identify nouns and verbs in the text.
    Returns the ratio of nouns to verbs. If verbs are 0, returns 0.0.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    nlp = get_nlp_model()
    doc = nlp(text)
    
    noun_count = 0
    verb_count = 0
    
    for token in doc:
        # Count nouns (NN, NNS, NNP, NNPS)
        if token.pos_ in ["NOUN", "PROPN"]:
            noun_count += 1
        # Count verbs (VB, VBD, VBG, VBN, VBP, VBZ)
        elif token.pos_ == "VERB":
            verb_count += 1
    
    if verb_count == 0:
        return 0.0
    
    return noun_count / verb_count

def extract_syntactic_features(text: str) -> Dict[str, float]:
    """
    Extract syntactic features: Mean Clause Length and T-unit Count.
    """
    if not text or not isinstance(text, str):
        return {"mean_clause_length": 0.0, "t_unit_count": 0}
    
    nlp = get_nlp_model()
    doc = nlp(text)
    
    # T-unit: one main clause plus any subordinate clauses attached to it
    # Simplified: count sentences as T-units for this implementation
    # A more complex implementation would parse dependency trees
    t_unit_count = len(list(doc.sents))
    
    if t_unit_count == 0:
        return {"mean_clause_length": 0.0, "t_unit_count": 0}
    
    # Clause length approximation: average tokens per sentence
    total_tokens = len([token for token in doc if not token.is_punct and not token.is_space])
    mean_clause_length = total_tokens / t_unit_count if t_unit_count > 0 else 0.0
    
    return {
        "mean_clause_length": mean_clause_length,
        "t_unit_count": t_unit_count
    }

def extract_semantic_features(text: str) -> np.ndarray:
    """
    Extract semantic embeddings for the text.
    Splits text into sentences and computes mean embedding.
    """
    if not text or not isinstance(text, str):
        return np.zeros(384)  # all-MiniLM-L6-v2 dimension
    
    model = get_embedding_model()
    
    # Split into sentences
    nlp = get_nlp_model()
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents if len(sent.text.strip()) > 10]
    
    if not sentences:
        return np.zeros(384)
    
    # Batch encode sentences
    with torch.no_grad():
        embeddings = model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
    
    # Mean pooling
    return np.mean(embeddings, axis=0)

def calculate_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Calculate pairwise cosine similarity matrix."""
    if embeddings.size == 0:
        return np.array([])
    
    # Normalize embeddings for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    
    return np.dot(normalized, normalized.T)

def calculate_participant_similarity(embeddings: np.ndarray) -> float:
    """
    Calculate average intra-document sentence similarity.
    Input: embeddings (N, D) where N is number of sentences, D is embedding dim.
    Output: scalar mean of pairwise similarities (excluding self).
    """
    if embeddings.shape[0] < 2:
        return 0.0
    
    sim_matrix = calculate_cosine_similarity_matrix(embeddings)
    
    # Extract upper triangle excluding diagonal
    n = sim_matrix.shape[0]
    upper_tri_indices = np.triu_indices(n, k=1)
    similarities = sim_matrix[upper_tri_indices]
    
    return np.mean(similarities)

def extract_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract all linguistic features for the dataset.
    Expected columns in df: 'text', 'label' (optional)
    Returns: DataFrame with added feature columns
    """
    logger.info(f"Starting feature extraction for {len(df)} records")
    
    # Initialize feature lists
    ttr_list = []
    mtld_list = []
    noun_verb_ratio_list = []
    mean_clause_length_list = []
    t_unit_count_list = []
    cosine_similarity_list = []
    
    for idx, row in df.iterrows():
        text = row.get('text', '')
        if not text:
            # Handle missing text
            ttr_list.append(0.0)
            mtld_list.append(0.0)
            noun_verb_ratio_list.append(0.0)
            mean_clause_length_list.append(0.0)
            t_unit_count_list.append(0)
            cosine_similarity_list.append(0.0)
            continue
        
        # Extract lexical features
        ttr = extract_ttr(text)
        mtld = extract_mtld(text)
        noun_verb_ratio = extract_noun_verb_ratio(text)
        
        # Extract syntactic features
        syntactic = extract_syntactic_features(text)
        
        # Extract semantic features
        try:
            model = get_embedding_model()
            nlp = get_nlp_model()
            doc = nlp(text)
            sentences = [sent.text for sent in doc.sents if len(sent.text.strip()) > 10]
            
            if len(sentences) >= 2:
                with torch.no_grad():
                    embeddings = model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
                cosine_sim = calculate_participant_similarity(embeddings)
            else:
                cosine_sim = 0.0
        except Exception as e:
            logger.warning(f"Embedding extraction failed for record {idx}: {e}")
            cosine_sim = 0.0
        
        ttr_list.append(ttr)
        mtld_list.append(mtld)
        noun_verb_ratio_list.append(noun_verb_ratio)
        mean_clause_length_list.append(syntactic['mean_clause_length'])
        t_unit_count_list.append(syntactic['t_unit_count'])
        cosine_similarity_list.append(cosine_sim)
        
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} records")
    
    # Add features to dataframe
    df['TTR'] = ttr_list
    df['MTLD'] = mtld_list
    df['Noun_Verb_Ratio'] = noun_verb_ratio_list
    df['Mean_Clause_Length'] = mean_clause_length_list
    df['T_Unit_Count'] = t_unit_count_list
    df['Sentence_Embedding_Cosine_Similarity'] = cosine_similarity_list
    
    logger.info("Feature extraction completed")
    return df

def process_dataset(input_path: str, output_path: str) -> None:
    """
    Process dataset from input CSV, extract features, and save to output CSV.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Extracting features for {len(df)} records")
    df_features = extract_all_features(df)
    
    logger.info(f"Saving results to {output_path}")
    df_features.to_csv(output_path, index=False)
    logger.info("Successfully saved feature matrix")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract linguistic features from transcripts")
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    process_dataset(args.input, args.output)

if __name__ == "__main__":
    main()
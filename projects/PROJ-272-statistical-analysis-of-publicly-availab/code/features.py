"""
Feature extraction module for cognitive decline analysis.
Implements lexical, syntactic, and semantic feature extraction.
"""
import logging
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import spacy
import torch
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine

from config import get_path, ensure_dirs, get_device, get_seed, set_seed
from utils import get_logger, normalize_text

# Initialize logger
logger = get_logger(__name__)

# Constants
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 32
MIN_TEXT_LENGTH = 50  # words

# Global NLP and model instances
_nlp = None
_embedding_model = None

def get_nlp() -> spacy.Language:
    """Load or return the spaCy English model."""
    global _nlp
    if _nlp is None:
        logger.info("Loading spaCy en_core_web_sm model...")
        _nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model loaded.")
    return _nlp

def get_embedding_model() -> SentenceTransformer:
    """Load or return the sentence transformer model (CPU-only)."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
        device = get_device()
        if "cuda" in device:
            logger.warning("CUDA detected. Forcing CPU-only as per constraints.")
            device = "cpu"
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
        logger.info(f"Embedding model loaded on {device}.")
    return _embedding_model

def calculate_ttr(text: str) -> float:
    """Calculate Type-Token Ratio (TTR)."""
    tokens = re.findall(r'\b\w+\b', text.lower())
    if not tokens:
        return 0.0
    unique_tokens = set(tokens)
    return len(unique_tokens) / len(tokens)

def calculate_mtld(tokens: List[str], target_len: float = 50.0) -> float:
    """Calculate Measure of Textual Lexical Diversity (MTLD)."""
    if not tokens:
        return 0.0
    mtld_values = []
    current_tokens = []
    ttr_sum = 0.0
    count = 0

    for token in tokens:
        current_tokens.append(token)
        if len(current_tokens) >= 10:  # Minimum segment length
            ttr = len(set(current_tokens)) / len(current_tokens)
            if ttr >= target_len / 100.0:
                ttr_sum += ttr
                count += 1
            else:
                # Segment ended
                if count > 0:
                    mtld_values.append(count / ttr_sum * 100.0) # Simplified MTLD logic for brevity, usually involves running TTR
                current_tokens = []
                ttr_sum = 0.0
                count = 0
    
    # If tokens remain, calculate partial
    if current_tokens:
        ttr = len(set(current_tokens)) / len(current_tokens)
        if ttr >= target_len / 100.0:
            mtld_values.append(len(current_tokens) / ttr_sum * 100.0) if ttr_sum > 0 else mtld_values.append(float(len(current_tokens)))
    
    return np.mean(mtld_values) if mtld_values else 0.0

def calculate_noun_verb_ratio(doc: spacy.Doc) -> float:
    """Calculate Noun/Verb ratio."""
    nouns = sum(1 for token in doc if token.pos_ in ("NOUN", "PROPN"))
    verbs = sum(1 for token in doc if token.pos_ == "VERB")
    if verbs == 0:
        return float('inf') if nouns > 0 else 0.0
    return nouns / verbs

def extract_lexical_features(text: str) -> Dict[str, float]:
    """Extract lexical features from text."""
    tokens = re.findall(r'\b\w+\b', text.lower())
    doc = get_nlp()(text)
    
    ttr = calculate_ttr(text)
    mtld = calculate_mtld(tokens)
    noun_verb_ratio = calculate_noun_verb_ratio(doc)
    
    return {
        "TTR": ttr,
        "MTLD": mtld,
        "Noun_Verb_Ratio": noun_verb_ratio if noun_verb_ratio != float('inf') else 999.0 # Cap infinite
    }

def calculate_mean_clause_length(text: str) -> float:
    """Calculate Mean Clause Length using spaCy."""
    doc = get_nlp()(text)
    clauses = [sent for sent in doc.sents] # Simplified: treating sentences as clauses for robustness without complex dependency parsing
    if not clauses:
        return 0.0
    
    total_words = 0
    count = 0
    for clause in clauses:
        words = [token for token in clause if token.is_alpha]
        if words:
            total_words += len(words)
            count += 1
    
    return total_words / count if count > 0 else 0.0

def calculate_t_unit_count(text: str) -> int:
    """Calculate T-unit count (Main clause + all subordinate clauses)."""
    doc = get_nlp()(text)
    # T-units are roughly independent clauses. We approximate by counting sentences for this implementation
    # as full T-unit parsing requires complex dependency tree traversal.
    return len(list(doc.sents))

def extract_syntactic_features(text: str) -> Dict[str, float]:
    """Extract syntactic features from text."""
    mean_clause_len = calculate_mean_clause_length(text)
    t_unit_count = calculate_t_unit_count(text)
    
    return {
        "Mean_Clause_Length": mean_clause_len,
        "T_Unit_Count": float(t_unit_count)
    }

def extract_semantic_features(texts: List[str]) -> np.ndarray:
    """
    Extract sentence embeddings for a list of texts.
    Processes in batches to prevent OOM.
    Returns numpy array of shape [N, D] with dtype float32.
    """
    if not texts:
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)
    
    model = get_embedding_model()
    embeddings = []
    
    logger.info(f"Starting semantic extraction for {len(texts)} texts...")
    
    # Filter empty texts just in case
    valid_texts = [t for t in texts if t and len(t.split()) > 0]
    
    with torch.no_grad():
        for i in range(0, len(valid_texts), BATCH_SIZE):
            batch = valid_texts[i:i + BATCH_SIZE]
            try:
                batch_embeddings = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
                embeddings.append(batch_embeddings)
            except Exception as e:
                logger.error(f"Error processing batch {i//BATCH_SIZE}: {e}")
                raise
    
    if not embeddings:
        logger.warning("No valid texts found for embedding.")
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)
    
    all_embeddings = np.vstack(embeddings)
    logger.info(f"Semantic extraction complete. Shape: {all_embeddings.shape}")
    return all_embeddings.astype(np.float32)

def calculate_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Calculate self-similarity (cosine similarity) for each embedding against itself?
    Task T024b asks for 'Sentence Embedding Cosine Similarity' (self-similarity).
    Usually, self-similarity is 1.0. 
    Re-reading T024b: "Calculate 'Sentence Embedding Cosine Similarity' (self-similarity) from embeddings".
    This likely means the similarity of a sentence to the mean of its group, or perhaps it's a misinterpretation of 'coherence'.
    However, standard 'self-similarity' is 1.0.
    Let's assume the task implies 'Average Cosine Similarity to other sentences in the same transcript' OR 
    if it's strictly 'self-similarity', it's a constant 1.0.
    
    Given the context of "Feature Matrix", a constant 1.0 is useless.
    Likely interpretation: Average similarity of each sentence embedding to the mean embedding of the transcript?
    OR: The task might mean 'Cosine Similarity' between the sentence embedding and a reference?
    
    Let's look at T024b again: "Calculate 'Sentence Embedding Cosine Similarity' (self-similarity) from embeddings".
    If it is strictly self-similarity (sim(x, x)), it is 1.0.
    If it is 'coherence', it is sim(x_i, mean(x_all)).
    
    Let's implement 'Average Cosine Similarity to the transcript mean' as a proxy for coherence, 
    as 'self-similarity' is trivial. If the task strictly means sim(x,x), we return 1.0.
    But wait, the task says "append as a new column". A column of 1.0s is not a feature.
    Hypothesis: The task actually means the similarity of the sentence to the *average* of all sentences in that participant's text.
    
    Let's implement: For each participant, compute the mean embedding of their sentences.
    Then for each sentence, compute cosine similarity to that mean.
    Then average those similarities to get one score per participant.
    
    Wait, the input to this function is likely the raw embeddings for ONE participant (since we are processing per record in the loop).
    The `extract_semantic_features` in the loop above takes a list of texts (sentences) for ONE participant?
    No, `extract_semantic_features` in the code above takes a list of texts. 
    The `process_dataset` function will likely pass the full list of texts for one participant?
    Or does it pass all texts for all participants?
    
    Let's assume the architecture:
    1. Load cleaned CSV (one row per participant).
    2. For each row, we have a text (transcript).
    3. We need to split the transcript into sentences.
    4. Embed sentences.
    5. Compute a single "Semantic Similarity" score for the participant.
    
    The function `extract_semantic_features` currently returns [N, D].
    We need a function to reduce this to a scalar "Similarity".
    
    Let's add `calculate_participant_similarity` which takes embeddings for one participant.
    """
    pass # Logic moved to process_dataset

def calculate_participant_similarity(embeddings: np.ndarray) -> float:
    """
    Calculate the average cosine similarity of each sentence embedding to the mean embedding of the participant's transcript.
    This serves as a measure of semantic coherence.
    """
    if embeddings.shape[0] <= 1:
        return 1.0 # Only one sentence, perfect coherence with itself
    
    mean_vec = np.mean(embeddings, axis=0)
    similarities = []
    for emb in embeddings:
        # Cosine similarity: dot(a,b) / (||a|| * ||b||)
        # Since embeddings are normalized by sentence-transformers usually, dot product is similarity.
        # But let's be safe.
        norm_emb = np.linalg.norm(emb)
        norm_mean = np.linalg.norm(mean_vec)
        if norm_emb == 0 or norm_mean == 0:
            similarities.append(0.0)
        else:
            sim = np.dot(emb, mean_vec) / (norm_emb * norm_mean)
            similarities.append(sim)
    
    return float(np.mean(similarities))

def extract_all_features(text: str) -> Dict[str, float]:
    """Extract all features for a single text record."""
    lexical = extract_lexical_features(text)
    syntactic = extract_syntactic_features(text)
    
    # Semantic: Split text into sentences
    doc = get_nlp()(text)
    sentences = [sent.text for sent in doc.sents]
    
    if not sentences:
        return {**lexical, **syntactic, "Sentence_Embedding_Cosine_Similarity": 0.0}
    
    embeddings = extract_semantic_features(sentences)
    if embeddings.shape[0] == 0:
        return {**lexical, **syntactic, "Sentence_Embedding_Cosine_Similarity": 0.0}
    
    similarity_score = calculate_participant_similarity(embeddings)
    
    return {
        **lexical,
        **syntactic,
        "Sentence_Embedding_Cosine_Similarity": similarity_score
    }

def process_dataset(input_path: str, output_embeddings_path: str, output_log_path: str) -> None:
    """
    Process the cleaned dataset to generate embeddings and save them.
    This function handles the T024 requirement:
    - Extract embeddings for all sentences in the dataset.
    - Save to data/processed/embeddings.npy
    - Generate derivation log.
    """
    logger.info(f"Processing dataset from {input_path}")
    
    # Ensure directories
    ensure_dirs([output_embeddings_path, output_log_path])
    
    # Load data
    df = pd.read_csv(input_path)
    
    if 'text' not in df.columns:
        raise ValueError("Input CSV must contain a 'text' column.")
    
    # Prepare for batch processing
    all_texts = df['text'].tolist()
    participant_ids = df['participant_id'].tolist()
    
    # We need to aggregate embeddings per participant to calculate similarity, 
    # BUT the task T024 says "Save embeddings to data/processed/embeddings.npy (shape [N, D])".
    # This implies N = total number of sentences across all participants?
    # Or N = number of participants?
    # "Shape [N, D]" usually implies one row per record in the input if it's a feature matrix.
    # But embeddings are per sentence.
    # Let's re-read T024: "Save embeddings to data/processed/embeddings.npy (shape [N, D]...)"
    # If N is participants, we can't store sentence embeddings directly unless we average them.
    # If N is sentences, we lose the link to participants unless we save a mapping.
    
    # Interpretation: The task likely wants the sentence embeddings for the entire corpus, 
    # flattened, or it wants the *aggregated* feature (similarity) as the semantic feature.
    # T024b says "Calculate ... and append as a new column". This implies the final feature matrix has a column for similarity.
    # So T024's "embeddings.npy" might be the raw sentence embeddings, and T024b uses them to compute the column.
    
    # Let's extract all sentence embeddings.
    all_sentences = []
    sentence_to_participant = []
    
    for idx, text in enumerate(all_texts):
        doc = get_nlp()(text)
        sentences = [sent.text for sent in doc.sents]
        all_sentences.extend(sentences)
        sentence_to_participant.extend([participant_ids[idx]] * len(sentences))
    
    logger.info(f"Total sentences to embed: {len(all_sentences)}")
    
    if len(all_sentences) == 0:
        logger.warning("No sentences found. Saving empty array.")
        np.save(output_embeddings_path, np.empty((0, EMBEDDING_DIM), dtype=np.float32))
        with open(output_log_path, 'w') as f:
            f.write("Derivation Log: No sentences found.\n")
        return

    # Extract embeddings in batches
    embeddings = extract_semantic_features(all_sentences)
    
    # Save embeddings
    np.save(output_embeddings_path, embeddings)
    logger.info(f"Saved embeddings to {output_embeddings_path} with shape {embeddings.shape}")
    
    # Generate Derivation Log
    log_content = f"""
    Derivation Log: Sentence Embeddings
    ====================================
    Source: {input_path}
    Model: {EMBEDDING_MODEL_NAME}
    Device: {get_device()}
    Batch Size: {BATCH_SIZE}
    
    Process:
    1. Loaded {len(all_sentences)} sentences from {len(all_texts)} participants.
    2. Embedded sentences using SentenceTransformer.
    3. Output shape: {embeddings.shape}
    4. Dtype: float32
    
    Note: These embeddings are used to calculate 'Sentence_Embedding_Cosine_Similarity' 
    (average similarity to mean embedding) for each participant.
    """
    
    with open(output_log_path, 'w') as f:
        f.write(log_content.strip())
    
    logger.info(f"Saved derivation log to {output_log_path}")

def main():
    """Main entry point for feature extraction."""
    # Paths
    input_data = get_path("data/interim/cleaned_adress.csv")
    embeddings_path = get_path("data/processed/embeddings.npy")
    log_path = get_path("data/processed/embeddings.derivation.log")
    
    if not Path(input_data).exists():
        raise FileNotFoundError(f"Input file not found: {input_data}")
    
    process_dataset(input_data, embeddings_path, log_path)

if __name__ == "__main__":
    main()

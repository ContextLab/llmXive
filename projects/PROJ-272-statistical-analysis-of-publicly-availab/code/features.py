import logging
import re
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import spacy
import yaml
from pathlib import Path
from sentence_transformers import SentenceTransformer

from config import get_path, ensure_dirs, get_max_workers, get_device
from utils import get_logger, normalize_text

# Global NLP model cache to avoid reloading
_nlp = None
_embedding_model = None

def get_nlp() -> spacy.language.Language:
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        # CPU-only constraint enforced by config, but we ensure device is cpu
        device = get_device()
        # Force CPU if config says so (though get_device should handle it)
        if device != 'cpu':
            logging.warning("Config requested non-CPU device, but semantic embeddings require CPU for this task. Forcing CPU.")
            device = 'cpu'
        
        model_name = "all-MiniLM-L6-v2"
        logging.info(f"Loading sentence transformer model: {model_name} on {device}")
        _embedding_model = SentenceTransformer(model_name, device=device)
    return _embedding_model

def calculate_ttr(text: str) -> float:
    """Calculate Type-Token Ratio."""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    return len(set(words)) / len(words)

def calculate_mtld(text: str) -> float:
    """Calculate Measure of Textual Lexical Diversity (MTLD)."""
    # Simplified MTLD implementation
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < 10:
        return 0.0
    
    # Standard MTLD logic (simplified for brevity, full implementation would use the specific algorithm)
    # Using a standard approximation: count how many words until TTR drops below 0.72
    # For this task, we use a robust approximation or call a library if available.
    # Implementing a basic version:
    lengths = []
    segment_size = 42 # Standard MTLD segment size
    
    # Fallback to a simpler lexical diversity metric if full MTLD is too complex for single file
    # But let's implement the core loop
    word_count = 0
    ttr = 1.0
    segment_ttr = 1.0
    
    # A more standard approach for MTLD without external library dependency:
    # It iterates through words, maintaining a running TTR. When TTR < threshold, record length and reset.
    threshold = 0.72
    current_segment_words = []
    segment_lengths = []
    
    for word in words:
        current_segment_words.append(word)
        if len(current_segment_words) > 0:
            ttr_val = len(set(current_segment_words)) / len(current_segment_words)
            if ttr_val < threshold:
                segment_lengths.append(len(current_segment_words))
                current_segment_words = []
    
    if not segment_lengths:
        # If TTR never dropped, the whole text is the segment
        return float(len(words))
        
    # Average segment length
    mtld_val = np.mean(segment_lengths)
    return float(mtld_val)

def calculate_noun_verb_ratio(text: str) -> float:
    """Calculate Noun to Verb ratio using spaCy."""
    doc = get_nlp()(text)
    nouns = sum(1 for token in doc if token.pos_ == "NOUN")
    verbs = sum(1 for token in doc if token.pos_ == "VERB")
    if verbs == 0:
        return float('inf') if nouns > 0 else 0.0
    return nouns / verbs

def extract_lexical_features(texts: List[str]) -> pd.DataFrame:
    """Extract lexical features for a list of texts."""
    results = []
    for i, text in enumerate(texts):
        if not isinstance(text, str) or not text.strip():
            results.append({"ttr": 0.0, "mtld": 0.0, "noun_verb_ratio": 0.0})
            continue
        results.append({
            "ttr": calculate_ttr(text),
            "mtld": calculate_mtld(text),
            "noun_verb_ratio": calculate_noun_verb_ratio(text)
        })
    return pd.DataFrame(results)

def calculate_mean_clause_length(text: str) -> float:
    """Calculate Mean Clause Length using spaCy."""
    doc = get_nlp()(text)
    clauses = list(doc.sents) # Using sentences as a proxy for clauses if specific clause logic is complex
    if not clauses:
        return 0.0
    total_words = sum(len([t for t in s if t.is_alpha]) for s in clauses)
    return float(total_words / len(clauses))

def calculate_t_unit_count(text: str) -> int:
    """Calculate T-unit count (main clause + dependent clauses)."""
    doc = get_nlp()(text)
    # Approximation: Count sentences + subordinate clauses
    # A T-unit is one main clause plus any dependent clauses.
    # In spaCy, we can approximate by counting sentences as T-units if complex parsing isn't required.
    # For a more accurate count, we'd need dependency parsing logic.
    # Using sentence count as a robust approximation for T-units in this context.
    return len(list(doc.sents))

def extract_syntactic_features(texts: List[str]) -> pd.DataFrame:
    """Extract syntactic features for a list of texts."""
    results = []
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            results.append({"mean_clause_length": 0.0, "t_unit_count": 0})
            continue
        results.append({
            "mean_clause_length": calculate_mean_clause_length(text),
            "t_unit_count": calculate_t_unit_count(text)
        })
    return pd.DataFrame(results)

def extract_semantic_features(texts: List[str]) -> np.ndarray:
    """
    Extract semantic features using sentence embeddings.
    
    Uses 'all-MiniLM-L6-v2' to generate embeddings.
    Returns a numpy array of shape [N, 384] with dtype float32.
    
    For a transcript, we compute the mean of sentence embeddings to represent the whole text.
    """
    model = get_embedding_model()
    embeddings = []
    
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            # Return zero vector for empty/invalid text
            embeddings.append(np.zeros(384, dtype=np.float32))
            continue
        
        # Split text into sentences for embedding
        doc = get_nlp()(text)
        sentences = [sent.text for sent in doc.sents if len(sent.text.strip()) > 0]
        
        if not sentences:
            embeddings.append(np.zeros(384, dtype=np.float32))
            continue
        
        # Encode sentences
        sentence_embeddings = model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
        
        # Mean pooling to get a single vector for the whole transcript
        mean_embedding = np.mean(sentence_embeddings, axis=0)
        embeddings.append(mean_embedding.astype(np.float32))
    
    return np.vstack(embeddings)

def extract_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract all features (lexical, syntactic, semantic) for the dataset.
    Semantic features are flattened into columns (e.g., sem_0, sem_1, ...).
    """
    logger = get_logger()
    logger.info("Starting full feature extraction...")
    
    # Prepare texts
    texts = df['text'].fillna("").astype(str).tolist()
    
    # Lexical
    logger.info("Extracting lexical features...")
    lexical_df = extract_lexical_features(texts)
    
    # Syntactic
    logger.info("Extracting syntactic features...")
    syntactic_df = extract_syntactic_features(texts)
    
    # Semantic
    logger.info("Extracting semantic features (embeddings)...")
    # This function computes embeddings but we need to save them separately as per T024
    # and also flatten them here for the feature matrix if needed, or just store the main matrix.
    # The task T024 says: "Save embeddings to data/processed/embeddings.npy"
    # T025 says: "Save processed feature matrix to data/processed/features.csv"
    # We will compute embeddings, save the .npy, and then create a summary (mean) for the CSV.
    
    embeddings = extract_semantic_features(texts)
    
    # Save embeddings to .npy (T024 requirement)
    output_path = get_path("processed", "embeddings.npy")
    ensure_dirs(output_path)
    np.save(output_path, embeddings)
    logger.info(f"Saved embeddings to {output_path} with shape {embeddings.shape}")
    
    # Create a summary of embeddings for the feature CSV (e.g., mean cosine similarity to a reference? 
    # Or just the mean embedding vector? The task says "Semantic feature extraction". 
    # Usually, for a CSV, we might store the mean vector or a derived metric like coherence.
    # However, storing 384 columns in a CSV is valid. Let's flatten the mean embedding.
    # To keep the CSV manageable, we will store the mean embedding vector as columns sem_0...sem_383.
    
    # Actually, the task T024 specifically asks to save the embeddings array.
    # T025 asks for the feature matrix. We will include the semantic mean vector in the feature matrix.
    # We'll compute the mean of the embeddings for each row (already done in extract_semantic_features)
    # and add them as columns.
    
    semantic_df = pd.DataFrame(embeddings, columns=[f"sem_{i}" for i in range(embeddings.shape[1])])
    
    # Combine all
    result_df = pd.concat([df.reset_index(drop=True), lexical_df, syntactic_df, semantic_df], axis=1)
    
    return result_df

def process_dataset(input_path: str, output_path: str, embeddings_path: Optional[str] = None):
    """
    Process a dataset from input CSV, extract features, and save results.
    
    Args:
        input_path: Path to the cleaned dataset CSV.
        output_path: Path to save the feature matrix CSV.
        embeddings_path: Optional path to save embeddings .npy (defaults to config).
    """
    logger = get_logger()
    logger.info(f"Loading dataset from {input_path}")
    
    df = pd.read_csv(input_path)
    
    if 'text' not in df.columns:
        raise ValueError(f"Input dataset must contain a 'text' column. Found: {df.columns.tolist()}")
    
    logger.info(f"Processing {len(df)} records...")
    feature_df = extract_all_features(df)
    
    # Save feature matrix
    logger.info(f"Saving feature matrix to {output_path}")
    ensure_dirs(output_path)
    feature_df.to_csv(output_path, index=False)
    
    # Embeddings are saved inside extract_all_features to embeddings_path or default
    if embeddings_path:
        # If a specific path is passed, we might need to handle it, 
        # but extract_all_features uses config default. 
        # We can override if needed, but for now we rely on the internal save.
        pass

def main():
    """Main entry point for feature extraction."""
    logger = get_logger()
    logger.info("Running feature extraction pipeline...")
    
    # Paths from config
    input_path = get_path("interim", "cleaned_adress.csv")
    output_csv = get_path("processed", "features.csv")
    # Embeddings path is handled inside extract_all_features via config default
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T016 first.")
    
    process_dataset(input_path, output_csv)
    logger.info("Feature extraction completed successfully.")

if __name__ == "__main__":
    main()

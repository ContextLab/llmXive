import os
import sys
import json
import logging
import traceback
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Importing from sibling modules as per API surface
# Note: In a real execution environment, these imports would resolve via sys.path
# For this implementation, we assume the project structure is correct.

try:
    from config import get_config_summary
except ImportError:
    # Fallback for standalone execution context if config is not in path
    def get_config_summary():
        return {"root": Path.cwd()}

# Constants
DEFAULT_DIM = 384  # Default dimension for all-MiniLM-L6-v2
MAX_NGRAM = 3      # Max n-gram size
VOCAB_SIZE = 50000 # Approximate vocabulary size for OOV handling

logger = logging.getLogger(__name__)

def load_nlp_model():
    """Loads the SpaCy model for POS tagging."""
    try:
        import spacy
        # Load small English model
        nlp = spacy.load("en_core_web_sm")
        logger.info("Loaded SpaCy model: en_core_web_sm")
        return nlp
    except OSError:
        logger.error("SpaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
        raise

def load_embedding_model():
    """Loads the sentence-transformers model for semantic similarity."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        return model
    except Exception as e:
        logger.error(f"Failed to load sentence-transformers model: {e}")
        raise

def extract_ngram_features(text: str, n: int) -> Dict[str, int]:
    """Extracts n-gram counts from text."""
    words = text.lower().split()
    ngrams = {}
    if len(words) < n:
        return ngrams
    for i in range(len(words) - n + 1):
        ngram = " ".join(words[i:i+n])
        ngrams[ngram] = ngrams.get(ngram, 0) + 1
    return ngrams

def extract_pos_features(doc) -> Dict[str, int]:
    """Extracts POS tag counts from a SpaCy document."""
    pos_counts = {}
    for token in doc:
        tag = token.pos_
        pos_counts[tag] = pos_counts.get(tag, 0) + 1
    return pos_counts

def compute_semantic_similarity(model, sentence1: str, sentence2: str) -> float:
    """Computes cosine similarity between two sentences."""
    try:
        embeddings = model.encode([sentence1, sentence2], convert_to_numpy=True)
        # Normalize and dot product
        norm = np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        if norm == 0:
            return 0.0
        return float(np.dot(embeddings[0], embeddings[1]) / norm)
    except Exception as e:
        logger.warning(f"Error computing semantic similarity: {e}")
        return 0.0

def load_gsm8k_verified() -> pd.DataFrame:
    """Loads the verified GSM8K dataset."""
    path = Path("data/raw/gsm8k_verified.parquet")
    if not path.exists():
        raise FileNotFoundError(f"Verified GSM8K dataset not found at {path}. Run T012 first.")
    logger.info(f"Loading verified GSM8K from {path}")
    return pd.read_parquet(path)

def extract_token_features(
    nlp,
    embedding_model,
    text: str,
    target_token: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extracts features for a specific token in a text.
    Implements OOV handling by assigning default vectors.
    """
    doc = nlp(text)
    token_found = False
    token_pos = None
    token_index = -1

    # Find the token in the document
    for i, token in enumerate(doc):
        if token.text == target_token:
            token_found = True
            token_pos = token.pos_
            token_index = i
            break

    # N-gram features
    ngram_features = {}
    for n in range(1, MAX_NGRAM + 1):
        ngram_features.update(extract_ngram_features(text, n))

    # POS features
    pos_features = extract_pos_features(doc)

    # Semantic similarity
    # If context is provided, compare token context to a reference or just the sentence
    sim_score = 0.0
    if context:
        # Use the full sentence containing the token as context if not provided
        sent_start = doc.sent.start
        sent_end = doc.sent.end
        sentence = " ".join([t.text for t in doc[sent_start:sent_end]])
        sim_score = compute_semantic_similarity(embedding_model, sentence, context)
    else:
        # Fallback: compare token text to itself (1.0) or use a generic similarity
        # Here we just use 0.0 if no context, or compute against the sentence
        sentence = " ".join([t.text for t in doc])
        sim_score = compute_semantic_similarity(embedding_model, target_token, sentence)

    # OOV Handling Logic (Task T019)
    # Check if token is OOV based on a simple heuristic (e.g., not in standard vocab or rare)
    # In a real scenario, we might check against the embedding model's vocabulary.
    # For this implementation, we assume if the token is very short or contains special chars, it might be OOV.
    # However, the robust way is to check if the token exists in the model's tokenizer.
    is_oov = False
    try:
        # Attempt to encode the token with the transformer model to check validity
        # all-MiniLM-L6-v2 uses BERT tokenizer
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
        tokens = tokenizer.tokenize(target_token)
        # If the token is split into multiple subwords, it might be considered OOV in a strict sense
        # or if it maps to [UNK]
        if tokenizer.convert_tokens_to_ids(tokens[0]) == tokenizer.unk_token_id:
            is_oov = True
    except Exception:
        # If tokenizer check fails, assume not OOV for safety, or rely on other heuristics
        pass

    # Feature Vector Construction
    # We will construct a dense vector for the MLP.
    # Since we have sparse features (ngrams, POS) and dense (sim), we need a fixed size.
    # Strategy:
    # 1. Map POS to a fixed size vector (one-hot or count)
    # 2. Map top N n-grams to a vector
    # 3. Append semantic similarity

    # For this specific task T019, the requirement is to "Filter OOV tokens or assign default vectors".
    # We will assign a default vector of zeros if the token is OOV.
    
    feature_vector = []
    
    if is_oov:
        # Assign default vector (zeros) to prevent training errors
        # The dimension should match what the MLP expects. 
        # We'll define a standard dimension here for the feature vector.
        # Let's assume a dimension of 128 for the combined features + 1 for similarity.
        default_dim = 128 
        feature_vector = [0.0] * (default_dim + 1)
        logger.debug(f"Token '{target_token}' marked as OOV. Assigned default zero vector.")
    else:
        # Construct actual features
        # 1. POS One-hot (simplified for demonstration, assuming ~20 POS tags)
        pos_tags = ["NOUN", "VERB", "ADJ", "ADV", "PRON", "DET", "ADP", "NUM", "PUNCT", "SYM", "X", "INTJ", "PART", "CONJ", "PROPN", "SCONJ", "CCONJ", "AUX", "BE", "DO"]
        pos_vec = [1.0 if token_pos == tag else 0.0 for tag in pos_tags]
        
        # 2. N-gram features (Top 100 frequent n-grams from the corpus would be mapped here)
        # For this implementation, we'll hash the n-grams to a fixed size bucket
        ngram_vec = [0.0] * 100
        for ngram, count in ngram_features.items():
            idx = hash(ngram) % 100
            ngram_vec[idx] += count
        
        # Normalize n-gram vector
        norm = np.linalg.norm(ngram_vec)
        if norm > 0:
            ngram_vec = (ngram_vec / norm).tolist()
        
        # 3. Semantic similarity
        sim_vec = [sim_score]
        
        # Combine
        feature_vector = pos_vec + ngram_vec + sim_vec

    return {
        "token": target_token,
        "is_oov": is_oov,
        "pos": token_pos,
        "feature_vector": feature_vector,
        "feature_dimension": len(feature_vector)
    }

def save_features(features_list: List[Dict], output_path: Path):
    """Saves features to JSON and Parquet."""
    # Save to JSON for schema compliance
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(features_list, f, indent=2)
    logger.info(f"Saved features to {json_path}")

    # Save to Parquet for efficient loading
    # Flatten feature vectors
    data = []
    for item in features_list:
        row = {
            "token": item["token"],
            "is_oov": item["is_oov"],
            "pos": item["pos"],
            "feature_dimension": item["feature_dimension"]
        }
        # Expand feature vector columns
        for i, val in enumerate(item["feature_vector"]):
            row[f"f_{i}"] = val
        data.append(row)
    
    df = pd.DataFrame(data)
    df.to_parquet(output_path)
    logger.info(f"Saved features to {output_path}")

def validate_features(features_list: List[Dict]) -> bool:
    """Validates that all features have correct dimensions and no NaNs."""
    dim = None
    for item in features_list:
        vec = item["feature_vector"]
        if dim is None:
            dim = len(vec)
        elif len(vec) != dim:
            logger.error(f"Feature dimension mismatch: expected {dim}, got {len(vec)}")
            return False
        if np.any(np.isnan(vec)):
            logger.error("NaN found in feature vector")
            return False
    return True

def main():
    """Main entry point for feature extraction."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        nlp = load_nlp_model()
        embedding_model = load_embedding_model()
        
        df = load_gsm8k_verified()
        
        # Sample 200 examples as per config (N=200)
        # Assuming 'answer' or 'solution' column contains the text
        # We need to extract tokens. For this example, we'll process the 'question' and 'answer'
        # and pick a few tokens from the answer.
        
        # Limit to 200 examples
        if len(df) > 200:
            df = df.sample(n=200, random_state=42)
        
        features_list = []
        
        # Process each example
        # Note: This is a simplified extraction. In reality, we'd map specific tokens to coefficients.
        # Here we extract features for the first 10 tokens of the answer for demonstration.
        for idx, row in df.iterrows():
            question = str(row.get('question', ''))
            answer = str(row.get('answer', ''))
            
            # Combine for context
            full_text = f"{question} {answer}"
            
            # Extract tokens from answer
            doc = nlp(answer)
            tokens_to_process = [token.text for token in doc][:10] # Limit tokens per example
            
            for token_text in tokens_to_process:
                if not token_text.strip() or token_text.isspace():
                    continue
                
                feature_data = extract_token_features(
                    nlp, 
                    embedding_model, 
                    full_text, 
                    token_text,
                    context=question # Use question as context for similarity
                )
                feature_data["example_id"] = idx
                features_list.append(feature_data)
        
        if not validate_features(features_list):
            raise ValueError("Feature validation failed")
        
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        save_features(features_list, output_dir / "static_features.parquet")
        
        logger.info("Feature extraction completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
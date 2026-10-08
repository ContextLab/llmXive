"""
Semantic similarity utilities for docstring analysis.

Uses sentence-transformers to calculate cosine similarity between
human-written and generated docstrings.
"""
import logging
from typing import List, Optional, Tuple
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not installed. Install via: pip install sentence-transformers")

from utils.exceptions import StatsException

logger = logging.getLogger(__name__)

# Default model as per task specification
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

class SimilarityException(Exception):
    """Exception raised when similarity calculation fails."""
    pass

def load_similarity_model(model_name: Optional[str] = None) -> 'SentenceTransformer':
    """
    Load the sentence-transformer model for embedding generation.
    
    Args:
        model_name: Name of the model to load. Defaults to DEFAULT_MODEL_NAME.
        
    Returns:
        Loaded SentenceTransformer model.
        
    Raises:
        SimilarityException: If the model cannot be loaded or sentence-transformers is not installed.
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        raise SimilarityException(
            "sentence-transformers library is not installed. "
            "Install it via: pip install sentence-transformers"
        )
    
    if model_name is None:
        model_name = DEFAULT_MODEL_NAME
    
    logger.info(f"Loading semantic similarity model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        raise SimilarityException(f"Failed to load model '{model_name}': {e}") from e

def calculate_pair_similarity(
    text1: Optional[str], 
    text2: Optional[str], 
    model: 'SentenceTransformer'
) -> float:
    """
    Calculate cosine similarity between two text strings.
    
    Args:
        text1: First text string.
        text2: Second text string.
        model: Loaded SentenceTransformer model.
        
    Returns:
        Cosine similarity score between -1.0 and 1.0.
        Returns 0.0 if either text is None or empty.
    """
    if not text1 or not text1.strip():
        return 0.0
    if not text2 or not text2.strip():
        return 0.0
        
    try:
        embeddings = model.encode([text1, text2], convert_to_numpy=True)
        # Normalize embeddings
        norm1 = np.linalg.norm(embeddings[0])
        norm2 = np.linalg.norm(embeddings[1])
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        similarity = np.dot(embeddings[0], embeddings[1]) / (norm1 * norm2)
        return float(similarity)
    except Exception as e:
        logger.warning(f"Error calculating similarity for texts: {e}")
        return 0.0

def calculate_batch_similarities(
    records: List[dict], 
    model: Optional['SentenceTransformer'] = None
) -> List[dict]:
    """
    Calculate semantic similarity for a batch of records.
    
    Args:
        records: List of dictionaries containing 'human_docstring' and 'generated_docstring'.
        model: Optional pre-loaded model. If None, loads the default model.
        
    Returns:
        List of records with added 'semantic_similarity' field.
        
    Raises:
        SimilarityException: If similarity calculation fails.
    """
    if model is None:
        model = load_similarity_model()
    
    results = []
    for i, record in enumerate(records):
        human_doc = record.get('human_docstring')
        generated_doc = record.get('generated_docstring')
        
        similarity = calculate_pair_similarity(human_doc, generated_doc, model)
        
        new_record = record.copy()
        new_record['semantic_similarity'] = similarity
        results.append(new_record)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(records)} records")
    
    return results

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from transformers import DistilBertTokenizer, DistilBertModel
import torch
import logging
from lib.metrics import cosine_similarity_safe, compute_centroid
from lib.config import MODEL_CACHE_DIR, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)

# Global model and tokenizer cache
_tokenizer = None
_model = None

def get_model_and_tokenizer():
    """
    Load or retrieve the cached DistilBERT model and tokenizer.
    Ensures single loading for efficiency.
    """
    global _tokenizer, _model
    
    if _tokenizer is None or _model is None:
        logger.info("Loading DistilBERT model and tokenizer...")
        try:
            _tokenizer = DistilBertTokenizer.from_pretrained(
                "distilbert-base-uncased",
                cache_dir=str(MODEL_CACHE_DIR)
            )
            _model = DistilBertModel.from_pretrained(
                "distilbert-base-uncased",
                cache_dir=str(MODEL_CACHE_DIR)
            )
            _model.eval()  # Set to evaluation mode
            logger.info("DistilBERT model and tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load DistilBERT model: {e}")
            raise
    
    return _model, _tokenizer

def encode_text(text: str, model, tokenizer, max_length: int = 512) -> np.ndarray:
    """
    Encode text into a fixed-size embedding vector using the pooled output.
    
    Args:
        text: The input text string.
        model: The DistilBERT model.
        tokenizer: The DistilBERT tokenizer.
        max_length: Maximum sequence length.
        
    Returns:
        Numpy array of shape (embedding_dimension,) representing the text embedding.
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for encoding. Returning zero vector.")
        return np.zeros(EMBEDDING_DIMENSION)
    
    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=max_length
        )
        
        with torch.no_grad():
            outputs = model(**inputs)
            # Use the last hidden state of the [CLS] token (pooled output)
            # For DistilBERT, we take the mean of the last hidden state over the sequence length
            # or use the [CLS] token representation. DistilBERT doesn't have a direct pooled output
            # like BERT, so we take the mean of the last hidden state.
            last_hidden_states = outputs.last_hidden_state
            # Mean pooling over the sequence length dimension
            attention_mask = inputs['attention_mask']
            # Expand attention_mask to match the hidden state dimensions
            attention_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size())
            # Sum the hidden states where attention mask is 1
            sum_embeddings = torch.sum(last_hidden_states * attention_mask_expanded, 1)
            # Count the number of non-padded tokens
            sum_mask = torch.clamp(attention_mask_expanded.sum(1), min=1e-9)
            # Mean embedding
            mean_embeddings = sum_embeddings / sum_mask
            embedding = mean_embeddings.squeeze(0).numpy()
            
        return embedding
        
    except Exception as e:
        logger.error(f"Error encoding text: {e}")
        return np.zeros(EMBEDDING_DIMENSION)

def compute_thinking_embedding(thinking_prefix: str, model, tokenizer) -> np.ndarray:
    """
    Compute the embedding for the thinking prefix.
    
    Args:
        thinking_prefix: The thinking prefix text.
        model: The DistilBERT model.
        tokenizer: The DistilBERT tokenizer.
        
    Returns:
        Numpy array representing the thinking embedding.
    """
    logger.debug(f"Computing thinking embedding for prefix length: {len(thinking_prefix)}")
    return encode_text(thinking_prefix, model, tokenizer)

def compute_tool_centroid_embedding(tool_descriptions: List[str], model, tokenizer) -> np.ndarray:
    """
    Compute the centroid embedding of a list of tool descriptions.
    
    Args:
        tool_descriptions: List of tool description strings.
        model: The DistilBERT model.
        tokenizer: The DistilBERT tokenizer.
        
    Returns:
        Numpy array representing the centroid of tool embeddings.
    """
    if not tool_descriptions:
        logger.warning("No tool descriptions provided for centroid computation. Returning zero vector.")
        return np.zeros(EMBEDDING_DIMENSION)
    
    embeddings = []
    for desc in tool_descriptions:
        emb = encode_text(desc, model, tokenizer)
        if not np.allclose(emb, np.zeros(EMBEDDING_DIMENSION)):
            embeddings.append(emb)
    
    if not embeddings:
        logger.warning("All tool descriptions resulted in zero vectors. Returning zero vector.")
        return np.zeros(EMBEDDING_DIMENSION)
    
    return compute_centroid(embeddings)

def calculate_divergence_score(thinking_embedding: np.ndarray, tool_centroid_embedding: np.ndarray) -> float:
    """
    Calculate the semantic divergence score based on cosine similarity.
    Divergence = 1 - cosine_similarity
    
    Args:
        thinking_embedding: The thinking prefix embedding.
        tool_centroid_embedding: The tool centroid embedding.
        
    Returns:
        Float representing the divergence score (0.0 = identical, 1.0 = orthogonal).
    """
    similarity = cosine_similarity_safe(thinking_embedding, tool_centroid_embedding)
    divergence = 1.0 - similarity
    return divergence

def process_problem(
    thinking_prefix: str,
    tool_descriptions: List[str],
    model: Optional[Any] = None,
    tokenizer: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Process a single problem to compute divergence metrics.
    
    Args:
        thinking_prefix: The thinking prefix text.
        tool_descriptions: List of tool descriptions associated with the problem.
        model: Optional pre-loaded model.
        tokenizer: Optional pre-loaded tokenizer.
        
    Returns:
        Dictionary containing:
            - thinking_embedding: numpy array (list)
            - tool_centroid_embedding: numpy array (list)
            - cosine_similarity: float
            - semantic_divergence_score: float
            - embedding_dimension: int
            - tools_retrieved_count: int (number of tool descriptions processed)
    """
    # Load model/tokenizer if not provided
    if model is None or tokenizer is None:
        model, tokenizer = get_model_and_tokenizer()
    
    # Compute embeddings
    thinking_emb = compute_thinking_embedding(thinking_prefix, model, tokenizer)
    tool_centroid_emb = compute_tool_centroid_embedding(tool_descriptions, model, tokenizer)
    
    # Calculate similarity and divergence
    similarity = cosine_similarity_safe(thinking_emb, tool_centroid_emb)
    divergence = 1.0 - similarity
    
    # Log retrieval stats and embedding dimensions as per T018
    logger.info(
        f"Processed problem: tools_count={len(tool_descriptions)}, "
        f"embedding_dim={EMBEDDING_DIMENSION}, "
        f"similarity={similarity:.4f}, divergence={divergence:.4f}"
    )
    
    return {
        "thinking_embedding": thinking_emb.tolist(),
        "tool_centroid_embedding": tool_centroid_emb.tolist(),
        "cosine_similarity": float(similarity),
        "semantic_divergence_score": float(divergence),
        "embedding_dimension": EMBEDDING_DIMENSION,
        "tools_retrieved_count": len(tool_descriptions)
    }

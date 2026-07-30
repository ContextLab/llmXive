"""
Divergence Model: Embeddings and scoring using DistilBERT.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from transformers import DistilBertTokenizer, DistilBertModel
import torch
import logging
from lib.metrics import cosine_similarity_safe, compute_centroid

logger = logging.getLogger(__name__)

class DivergenceModelError(Exception):
    """Custom exception for divergence model errors."""
    pass

def get_model_and_tokenizer():
    """Load DistilBERT model and tokenizer."""
    logger.info("Loading DistilBERT model and tokenizer...")
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertModel.from_pretrained('distilbert-base-uncased')
    model.eval()
    return model, tokenizer

def encode_text(text: str, tokenizer, model) -> np.ndarray:
    """Encode text to embedding vector."""
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    # Use last hidden state mean pooling
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return embeddings

def compute_thinking_embedding(thinking_text: str, model, tokenizer) -> np.ndarray:
    """Compute embedding for thinking prefix."""
    return encode_text(thinking_text, model, tokenizer)

def compute_tool_centroid_embedding(tool_descriptions: List[str], model, tokenizer) -> np.ndarray:
    """Compute centroid of tool descriptions embeddings."""
    if not tool_descriptions:
        return np.zeros(768) # Default dim for DistilBERT
    
    embeddings = []
    for desc in tool_descriptions:
        emb = encode_text(desc, model, tokenizer)
        embeddings.append(emb)
    
    return compute_centroid(embeddings)

def calculate_divergence_score(thinking_emb: np.ndarray, tool_emb: np.ndarray) -> float:
    """Calculate semantic divergence score (1 - cosine similarity)."""
    sim = cosine_similarity_safe(thinking_emb, tool_emb)
    return 1.0 - sim

def process_problem(problem_data: Dict[str, Any], model, tokenizer) -> Dict[str, Any]:
    """
    Process a single problem: encode thinking, encode tools, compute score.
    """
    thinking_text = problem_data.get("thinking", "")
    tool_descs = problem_data.get("tool_descriptions", [])
    
    if not thinking_text:
        logger.warning("Missing thinking text, skipping.")
        return None
    
    thinking_emb = compute_thinking_embedding(thinking_text, model, tokenizer)
    tool_emb = compute_tool_centroid_embedding(tool_descs, model, tokenizer)
    
    score = calculate_divergence_score(thinking_emb, tool_emb)
    
    return {
        "problem_id": problem_data.get("problem_id"),
        "thinking_embedding": thinking_emb.tolist(),
        "tool_centroid_embedding": tool_emb.tolist(),
        "cosine_similarity": cosine_similarity_safe(thinking_emb, tool_emb),
        "semantic_divergence_score": score
    }

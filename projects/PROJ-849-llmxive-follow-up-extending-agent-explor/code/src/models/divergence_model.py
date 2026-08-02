import os
import torch
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from transformers import DistilBertTokenizer, DistilBertModel
import logging
from lib.metrics import cosine_similarity_safe, compute_centroid

logger = logging.getLogger(__name__)

class DivergenceModelError(Exception):
    """Custom exception for divergence model errors."""
    pass

@dataclass
class DivergenceResult:
    """Data class to hold divergence calculation results."""
    problem_id: str
    thinking_embedding: List[float]
    tool_centroid_embedding: List[float]
    cosine_similarity: float
    semantic_divergence_score: float
    retrieval_stats: Dict[str, Any]  # Added to store retrieval stats (num tools, embedding dim)

class DivergenceModel:
    """
    Model to compute semantic divergence scores using DistilBERT embeddings and BM25 retrieval.
    """
    def __init__(self, tokenizer: DistilBertTokenizer, model: DistilBertModel):
        self.tokenizer = tokenizer
        self.model = model
        self.device = torch.device("cpu")  # CPU-first as per spec
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"DivergenceModel initialized on {self.device}")

    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text into embeddings using DistilBERT.
        
        Args:
            text: Input text string.
            
        Returns:
            Numpy array of embeddings (mean pooling over tokens).
        """
        if not text:
            raise DivergenceModelError("Input text cannot be empty")
        
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Mean pooling over the last hidden state
        last_hidden_states = outputs.last_hidden_state
        attention_mask = inputs['attention_mask']
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
        embeddings = torch.sum(last_hidden_states * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        return embeddings.cpu().numpy().flatten()

    def compute_thinking_embedding(self, thinking_prefix: str) -> np.ndarray:
        """
        Compute embedding for the thinking prefix.
        
        Args:
            thinking_prefix: The thinking prefix string.
            
        Returns:
            Embedding vector as numpy array.
        """
        return self.encode_text(thinking_prefix)

    def compute_tool_centroid_embedding(self, tool_embeddings: List[np.ndarray]) -> np.ndarray:
        """
        Compute centroid of tool embeddings.
        
        Args:
            tool_embeddings: List of tool embedding vectors.
            
        Returns:
            Centroid embedding vector.
        """
        if not tool_embeddings:
            # Return zero vector if no tools retrieved
            return np.zeros(768)  # DistilBERT dimension
        
        return compute_centroid(tool_embeddings)

    def calculate_divergence_score(
        self, 
        thinking_embedding: np.ndarray, 
        tool_centroid_embedding: np.ndarray
    ) -> float:
        """
        Calculate semantic divergence score as 1 - cosine_similarity.
        
        Args:
            thinking_embedding: Embedding of the thinking prefix.
            tool_centroid_embedding: Centroid embedding of retrieved tools.
            
        Returns:
            Divergence score (1 - cosine_similarity).
        """
        sim = cosine_similarity_safe(thinking_embedding, tool_centroid_embedding)
        return 1.0 - sim

    def process_problem(
        self,
        problem_id: str,
        thinking_prefix: str,
        tool_embeddings: List[np.ndarray],
        retrieval_stats: Dict[str, Any]
    ) -> DivergenceResult:
        """
        Process a single problem to compute divergence metrics.
        
        Args:
            problem_id: Problem identifier.
            thinking_prefix: Thinking prefix string.
            tool_embeddings: List of embeddings for retrieved tools.
            retrieval_stats: Dictionary containing retrieval statistics (e.g., num_tools, embedding_dim).
            
        Returns:
            DivergenceResult object with all computed metrics.
        """
        try:
            thinking_emb = self.compute_thinking_embedding(thinking_prefix)
            tool_centroid = self.compute_tool_centroid_embedding(tool_embeddings)
            divergence = self.calculate_divergence_score(thinking_emb, tool_centroid)
            
            logger.info(
                f"Processed problem {problem_id}: "
                f"retrieved {retrieval_stats.get('num_tools', 0)} tools, "
                f"embedding_dim={retrieval_stats.get('embedding_dim', 768)}, "
                f"divergence_score={divergence:.4f}"
            )
            
            return DivergenceResult(
                problem_id=problem_id,
                thinking_embedding=thinking_emb.tolist(),
                tool_centroid_embedding=tool_centroid.tolist(),
                cosine_similarity=1.0 - divergence,
                semantic_divergence_score=divergence,
                retrieval_stats=retrieval_stats
            )
        except Exception as e:
            logger.error(f"Error processing problem {problem_id}: {e}")
            raise DivergenceModelError(f"Failed to process problem {problem_id}: {e}")

def get_model_and_tokenizer() -> Tuple[DistilBertTokenizer, DistilBertModel]:
    """
    Load DistilBERT tokenizer and model.
    
    Returns:
        Tuple of (tokenizer, model).
    """
    model_name = "distilbert-base-uncased"
    logger.info(f"Loading {model_name}...")
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    model = DistilBertModel.from_pretrained(model_name)
    return tokenizer, model

def encode_text(text: str, tokenizer: DistilBertTokenizer, model: DistilBertModel) -> np.ndarray:
    """
    Convenience function to encode text.
    
    Args:
        text: Input text.
        tokenizer: DistilBertTokenizer.
        model: DistilBertModel.
        
    Returns:
        Embedding vector.
    """
    # Create a temporary model instance for this call if needed, 
    # or assume model is already on correct device. 
    # For simplicity in this utility, we re-use the logic from the class.
    device = torch.device("cpu")
    model.to(device)
    model.eval()
    
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    last_hidden_states = outputs.last_hidden_state
    attention_mask = inputs['attention_mask']
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
    embeddings = torch.sum(last_hidden_states * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return embeddings.cpu().numpy().flatten()

def compute_thinking_embedding(thinking_prefix: str, tokenizer: DistilBertTokenizer, model: DistilBertModel) -> np.ndarray:
    return encode_text(thinking_prefix, tokenizer, model)

def compute_tool_centroid_embedding(tool_embeddings: List[np.ndarray]) -> np.ndarray:
    return compute_centroid(tool_embeddings)

def calculate_divergence_score(thinking_embedding: np.ndarray, tool_centroid_embedding: np.ndarray) -> float:
    sim = cosine_similarity_safe(thinking_embedding, tool_centroid_embedding)
    return 1.0 - sim

def process_problem(
    problem_id: str,
    thinking_prefix: str,
    tool_embeddings: List[np.ndarray],
    retrieval_stats: Dict[str, Any],
    tokenizer: DistilBertTokenizer,
    model: DistilBertModel
) -> DivergenceResult:
    """
    Process a problem using standalone functions.
    """
    model_instance = DivergenceModel(tokenizer, model)
    return model_instance.process_problem(problem_id, thinking_prefix, tool_embeddings, retrieval_stats)

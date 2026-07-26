import os
import torch
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from transformers import DistilBertTokenizer, DistilBertModel

class DivergenceModelError(Exception):
    """Custom exception for errors in the DivergenceModel."""
    pass

@dataclass
class DivergenceResult:
    """
    Result container for a single divergence calculation.
    
    Attributes:
        problem_id: Unique identifier for the problem.
        thinking_prefix: The extracted thinking trace prefix (or None if missing).
        retrieved_tools: List of tool descriptions retrieved via BM25.
        semantic_divergence_score: Calculated score (1 - cosine_similarity).
        centroid_vector: The averaged embedding of retrieved tool descriptions (or None if zero-retrieval).
        status: 'success', 'skipped_missing_prefix', or 'zero_retrieval'.
        error_message: Optional error details if status is not 'success'.
    """
    problem_id: str
    thinking_prefix: Optional[str]
    retrieved_tools: List[str]
    semantic_divergence_score: Optional[float]
    centroid_vector: Optional[np.ndarray]
    status: str
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "thinking_prefix": self.thinking_prefix,
            "retrieved_tools": self.retrieved_tools,
            "semantic_divergence_score": float(self.semantic_divergence_score) if self.semantic_divergence_score is not None else None,
            "centroid_vector": self.centroid_vector.tolist() if self.centroid_vector is not None else None,
            "status": self.status,
            "error_message": self.error_message
        }

class DivergenceModel:
    """
    Model for calculating Semantic Divergence Scores between thinking traces and tool descriptions.
    
    This class handles:
    1. Loading the DistilBERT tokenizer and model (CPU-only).
    2. Encoding thinking prefixes and tool descriptions.
    3. Calculating cosine similarity and divergence scores.
    4. Robust error handling for missing prefixes and zero-retrieval scenarios.
    """

    def __init__(self, model_name: str = "distilbert-base-uncased"):
        """
        Initializes the DivergenceModel.
        
        Args:
            model_name: HuggingFace model identifier for DistilBERT.
        
        Raises:
            DivergenceModelError: If the model or tokenizer cannot be loaded.
        """
        self.model_name = model_name
        self.device = torch.device("cpu")
        
        try:
            self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_name)
            self.model = DistilBertModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            raise DivergenceModelError(f"Failed to load model '{self.model_name}': {e}")

    def _encode_text(self, text: str) -> np.ndarray:
        """
        Encodes a single text string into a pooled embedding vector.
        
        Args:
            text: The input text string.
        
        Returns:
            numpy.ndarray: The pooled embedding vector.
        
        Raises:
            DivergenceModelError: If encoding fails.
        """
        if not text or not text.strip():
            raise DivergenceModelError("Cannot encode empty or whitespace-only text.")
        
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use last hidden state [CLS] token or mean pooling
            # DistilBERT output.last_hidden_state shape: (batch, seq_len, hidden_dim)
            # We'll use mean pooling over the sequence length for robustness
            input_mask = inputs['attention_mask'].unsqueeze(-1).expand(outputs.last_hidden_state.shape).float()
            sum_embeddings = torch.sum(outputs.last_hidden_state * input_mask, 1)
            sum_mask = torch.clamp(input_mask.sum(1), min=1e-9)
            pooled_embedding = sum_embeddings / sum_mask
        
        return pooled_embedding.cpu().numpy().flatten()

    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculates cosine similarity between two vectors.
        
        Args:
            vec1: First vector.
            vec2: Second vector.
        
        Returns:
            float: Cosine similarity value in [-1, 1].
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def process_single(self, problem_id: str, thinking_prefix: Optional[str], retrieved_tools: List[str]) -> DivergenceResult:
        """
        Processes a single problem instance to calculate the divergence score.
        
        Implements robust error handling:
        - If `thinking_prefix` is missing or empty, the record is SKIPPED (status: 'skipped_missing_prefix').
        - If `retrieved_tools` is empty (zero-retrieval), the centroid is treated as a zero vector,
          resulting in a similarity of 0 and a divergence score of 1.0 (status: 'zero_retrieval').
        
        Args:
            problem_id: Unique identifier for the problem.
            thinking_prefix: The thinking trace prefix. Can be None or empty.
            retrieved_tools: List of tool description strings retrieved by BM25.
        
        Returns:
            DivergenceResult: The calculated result with status and metrics.
        """
        # Case 1: Missing Thinking Prefix
        if not thinking_prefix or not thinking_prefix.strip():
            return DivergenceResult(
                problem_id=problem_id,
                thinking_prefix=thinking_prefix,
                retrieved_tools=retrieved_tools,
                semantic_divergence_score=None,
                centroid_vector=None,
                status="skipped_missing_prefix",
                error_message="Thinking prefix is missing or empty. Record skipped."
            )

        # Case 2: Zero Retrieval (Empty Tool List)
        if not retrieved_tools:
            # We still encode the thinking prefix, but the tool centroid is effectively a zero vector.
            # Similarity with a zero vector is 0, so divergence = 1 - 0 = 1.0.
            try:
                thinking_vector = self._encode_text(thinking_prefix)
            except Exception as e:
                return DivergenceResult(
                    problem_id=problem_id,
                    thinking_prefix=thinking_prefix,
                    retrieved_tools=retrieved_tools,
                    semantic_divergence_score=None,
                    centroid_vector=None,
                    status="zero_retrieval",
                    error_message=f"Failed to encode thinking prefix: {e}"
                )
            
            return DivergenceResult(
                problem_id=problem_id,
                thinking_prefix=thinking_prefix,
                retrieved_tools=retrieved_tools,
                semantic_divergence_score=1.0, # Maximum divergence
                centroid_vector=None, # No centroid to represent
                status="zero_retrieval",
                error_message="No tools retrieved. Centroid is zero vector. Divergence set to 1.0."
            )

        # Case 3: Normal Processing
        try:
            thinking_vector = self._encode_text(thinking_prefix)
            
            # Encode all retrieved tools and compute centroid
            tool_embeddings = []
            for tool_desc in retrieved_tools:
                if tool_desc and tool_desc.strip():
                    tool_embeddings.append(self._encode_text(tool_desc))
            
            if not tool_embeddings:
                # Fallback if all tool descriptions were empty strings
                return DivergenceResult(
                    problem_id=problem_id,
                    thinking_prefix=thinking_prefix,
                    retrieved_tools=retrieved_tools,
                    semantic_divergence_score=1.0,
                    centroid_vector=None,
                    status="zero_retrieval",
                    error_message="All retrieved tool descriptions were empty. Treated as zero-retrieval."
                )
            
            centroid_vector = np.mean(tool_embeddings, axis=0)
            
            similarity = self._calculate_cosine_similarity(thinking_vector, centroid_vector)
            divergence_score = 1.0 - similarity
            
            return DivergenceResult(
                problem_id=problem_id,
                thinking_prefix=thinking_prefix,
                retrieved_tools=retrieved_tools,
                semantic_divergence_score=divergence_score,
                centroid_vector=centroid_vector,
                status="success",
                error_message=None
            )
            
        except Exception as e:
            raise DivergenceModelError(f"Error processing problem {problem_id}: {e}")

def create_divergence_model() -> DivergenceModel:
    """
    Factory function to create and return a DivergenceModel instance.
    
    Returns:
        DivergenceModel: Initialized model instance.
    """
    return DivergenceModel()
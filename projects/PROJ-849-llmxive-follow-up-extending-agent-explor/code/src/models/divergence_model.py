"""
Divergence Model for Semantic Divergence Diagnostic.

Implements DistilBERT-based encoding and cosine similarity calculation
to compute the Semantic Divergence Score between thinking processes
and tool descriptions.
"""

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
    """Result container for a single problem's divergence calculation."""
    problem_id: str
    thinking_embedding: List[float]
    tool_centroid_embedding: List[float]
    cosine_similarity: float
    semantic_divergence_score: float
    retrieved_tool_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class DivergenceModel:
    """
    Handles loading DistilBERT, encoding text, and computing
    semantic divergence scores.
    """

    def __init__(self, device: Optional[str] = None):
        """
        Initialize the model and tokenizer.

        Args:
            device: Device to run inference on ('cpu', 'cuda', or None for auto).
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Initializing DivergenceModel on device: {self.device}")

        try:
            self.tokenizer = DistilBertTokenizer.from_pretrained(
                "distilbert-base-uncased"
            )
            self.model = DistilBertModel.from_pretrained(
                "distilbert-base-uncased"
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info("DistilBERT model and tokenizer loaded successfully.")
        except Exception as e:
            raise DivergenceModelError(f"Failed to load DistilBERT: {e}")

        self.embedding_dim = self.model.config.hidden_size

    def encode_text(self, text: str, prefix: str = "") -> np.ndarray:
        """
        Encode a text string into a dense embedding vector.

        Args:
            text: The text to encode.
            prefix: Optional prefix to prepend (e.g., "Thinking: ").

        Returns:
            numpy array of shape (embedding_dim,) representing the mean-pooled embedding.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for encoding, returning zero vector.")
            return np.zeros(self.embedding_dim, dtype=np.float32)

        full_text = f"{prefix} {text}".strip() if prefix else text

        inputs = self.tokenizer(
            full_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Mean pooling over the last hidden state
        # attention_mask shape: (batch, seq_len)
        # last_hidden_state shape: (batch, seq_len, hidden_dim)
        attention_mask = inputs['attention_mask']
        last_hidden_state = outputs.last_hidden_state

        # Expand attention_mask to match hidden state dimensions for broadcasting
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(
            last_hidden_state.size()
        ).float()

        sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)

        embedding = sum_embeddings / sum_mask
        embedding = embedding.squeeze(0).cpu().numpy()

        if embedding.shape[0] != self.embedding_dim:
            raise DivergenceModelError(
                f"Unexpected embedding dimension: {embedding.shape[0]}, expected {self.embedding_dim}"
            )

        return embedding

    def compute_thinking_embedding(self, thinking_text: str) -> np.ndarray:
        """
        Compute the embedding for the 'thinking' prefix of a problem.

        Args:
            thinking_text: The raw thinking text from the dataset.

        Returns:
            Embedding vector.
        """
        # The task specifies encoding the "thinking prefix".
        # We prepend a semantic tag to ensure the model understands context.
        return self.encode_text(thinking_text, prefix="Thinking Process:")

    def compute_tool_centroid_embedding(
        self,
        retrieved_tool_descriptions: List[str]
    ) -> np.ndarray:
        """
        Compute the centroid embedding of a list of tool descriptions.

        Args:
            retrieved_tool_descriptions: List of tool description strings.

        Returns:
            Centroid embedding vector (mean of all tool embeddings).
        """
        if not retrieved_tool_descriptions:
            logger.warning("No tool descriptions provided, returning zero vector.")
            return np.zeros(self.embedding_dim, dtype=np.float32)

        embeddings = []
        for i, desc in enumerate(retrieved_tool_descriptions):
            if not desc or not desc.strip():
                continue
            emb = self.encode_text(desc, prefix="Tool Description:")
            embeddings.append(emb)

        if not embeddings:
            logger.warning("All tool descriptions were empty, returning zero vector.")
            return np.zeros(self.embedding_dim, dtype=np.float32)

        # Compute centroid (mean)
        stacked = np.stack(embeddings, axis=0)
        centroid = np.mean(stacked, axis=0)
        return centroid

    def calculate_divergence_score(
        self,
        thinking_embedding: np.ndarray,
        tool_centroid_embedding: np.ndarray
    ) -> float:
        """
        Calculate the Semantic Divergence Score.

        Score = 1 - CosineSimilarity(thinking, tool_centroid)

        Args:
            thinking_embedding: Thinking process embedding.
            tool_centroid_embedding: Tool centroid embedding.

        Returns:
            Divergence score (0.0 = identical, 1.0 = orthogonal/opposite).
        """
        # Handle zero vectors safely
        if np.allclose(thinking_embedding, 0) or np.allclose(tool_centroid_embedding, 0):
            # If one is zero, similarity is 0, so divergence is 1.0
            return 1.0

        similarity = cosine_similarity_safe(thinking_embedding, tool_centroid_embedding)
        divergence = 1.0 - similarity
        return float(divergence)

    def process_problem(
        self,
        problem_id: str,
        thinking_text: str,
        retrieved_tool_descriptions: List[str]
    ) -> DivergenceResult:
        """
        Process a single problem to compute its divergence score.

        Args:
            problem_id: Unique identifier for the problem.
            thinking_text: The thinking trace text.
            retrieved_tool_descriptions: List of tool descriptions retrieved by BM25.

        Returns:
            DivergenceResult object containing embeddings and score.
        """
        logger.debug(f"Processing problem {problem_id}")

        # 1. Compute Thinking Embedding
        thinking_emb = self.compute_thinking_embedding(thinking_text)

        # 2. Compute Tool Centroid Embedding
        tool_centroid_emb = self.compute_tool_centroid_embedding(retrieved_tool_descriptions)

        # 3. Calculate Divergence Score
        score = self.calculate_divergence_score(thinking_emb, tool_centroid_emb)

        # 4. Return Result
        return DivergenceResult(
            problem_id=problem_id,
            thinking_embedding=thinking_emb.tolist(),
            tool_centroid_embedding=tool_centroid_emb.tolist(),
            cosine_similarity=1.0 - score,
            semantic_divergence_score=score,
            retrieved_tool_count=len(retrieved_tool_descriptions)
        )


def create_divergence_model(device: Optional[str] = None) -> DivergenceModel:
    """Factory function to create a DivergenceModel instance."""
    return DivergenceModel(device=device)
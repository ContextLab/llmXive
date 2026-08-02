import os
import re
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
import logging
import numpy as np

logger = logging.getLogger(__name__)

class RetrievalServiceError(Exception):
    """Custom exception for retrieval service errors."""
    pass

class RetrievalService:
    """
    Service for retrieving relevant tool descriptions based on a query using BM25.
    """
    def __init__(self, tool_descriptions: List[str], problem_ids: List[str]):
        """
        Initialize the retrieval service with tool descriptions and problem IDs.
        
        Args:
            tool_descriptions: List of tool description strings.
            problem_ids: List of problem IDs corresponding to the tool descriptions.
        """
        if len(tool_descriptions) != len(problem_ids):
            raise RetrievalServiceError(
                f"Length mismatch: {len(tool_descriptions)} descriptions vs {len(problem_ids)} IDs"
            )
        
        self.tool_descriptions = tool_descriptions
        self.problem_ids = problem_ids
        
        # Pre-process tool descriptions for BM25
        self.tokenized_corpus = [
          self._tokenize(doc) for doc in tool_descriptions
        ]
        
        # Build BM25 index
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        logger.info(f"RetrievalService initialized with {len(self.tool_descriptions)} tools")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into lowercase words, removing non-alphanumeric characters.
        
        Args:
            text: Input text string.
            
        Returns:
            List of tokenized words.
        """
        text = text.lower()
        # Remove non-alphanumeric characters except spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Split into words and filter empty strings
        tokens = [word for word in text.split() if word]
        return tokens

    def retrieve_top_tools(
        self, 
        query: str, 
        top_k: int = 5
    ) -> Tuple[List[str], List[float], int]:
        """
        Retrieve top-k most relevant tool descriptions for a given query.
        
        Args:
            query: The query string (e.g., thinking prefix).
            top_k: Number of top results to return.
            
        Returns:
            Tuple of (retrieved_tool_ids, scores, embedding_dimension)
            - retrieved_tool_ids: List of problem IDs for the top-k tools.
            - scores: List of BM25 scores for the top-k tools.
            - embedding_dimension: Dimension of the embedding vector used for downstream scoring (fixed at 768 for DistilBERT).
            
        Raises:
            RetrievalServiceError: If retrieval fails or input is invalid.
        """
        if not query or not isinstance(query, str):
            raise RetrievalServiceError("Query must be a non-empty string")
        
        if top_k <= 0:
            raise RetrievalServiceError("top_k must be a positive integer")
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            # Handle zero-retrieval edge case: return empty lists and zero score
            logger.warning(f"Query '{query}' resulted in no tokens. Returning empty retrieval.")
            return [], [], 768  # DistilBERT base model dimension is 768
        
        # Compute BM25 scores
        doc_scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_k_indices = np.argsort(doc_scores)[::-1][:top_k]
        
        # Filter out zero scores (no match) if necessary, but keep top_k regardless for consistency
        retrieved_ids = []
        retrieved_scores = []
        
        for idx in top_k_indices:
            if doc_scores[idx] > 0:  # Only include if there's a match
                retrieved_ids.append(self.problem_ids[idx])
                retrieved_scores.append(float(doc_scores[idx]))
            else:
                # If we hit a zero score, we can stop or continue with zeros depending on requirement
                # Here we stop to avoid returning irrelevant tools
                break
        
        # Log retrieval stats
        logger.info(
            f"Retrieval stats for query '{query[:50]}...': "
            f"retrieved {len(retrieved_ids)} tools, "
            f"embedding dimension = 768"
        )
        
        return retrieved_ids, retrieved_scores, 768

def create_retrieval_service(
    tool_descriptions: List[str], 
    problem_ids: List[str]
) -> RetrievalService:
    """
    Factory function to create a RetrievalService instance.
    
    Args:
        tool_descriptions: List of tool description strings.
        problem_ids: List of problem IDs.
        
    Returns:
        Configured RetrieualService instance.
    """
    return RetrievalService(tool_descriptions, problem_ids)

def retrieve_top_tools(
    service: RetrievalService,
    query: str,
    top_k: int = 5
) -> Tuple[List[str], List[float], int]:
    """
    Convenience function to retrieve tools using a service instance.
    
    Args:
        service: RetrievalService instance.
        query: Query string.
        top_k: Number of top results.
        
    Returns:
        Tuple of (retrieved_tool_ids, scores, embedding_dimension).
    """
    return service.retrieve_top_tools(query, top_k)

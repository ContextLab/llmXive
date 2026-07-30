"""
Retrieval Service for LLMXive.

Implements BM25-based retrieval of tool descriptions based on thinking traces.
"""
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
import logging
import numpy as np

from src.lib.tool_mapper import extract_tool_descriptions, ToolMapperError
from lib.config import DATA_ROOT

logger = logging.getLogger(__name__)

class RetrievalServiceError(Exception):
    """Custom exception for retrieval service errors."""
    pass

class RetrievalService:
    """
    Service for building and querying BM25 index of tool descriptions.
    """
    
    def __init__(self, tool_map_path: Optional[str] = None):
        """
        Initialize the retrieval service.
        
        Args:
            tool_map_path: Optional path to the tool mapping JSON.
        """
        self.bm25_index: Optional[BM25Okapi] = None
        self.tool_descriptions: List[str] = []
        self.tokenized_corpus: List[List[str]] = []
        self.tool_map_path = tool_map_path
        self._built = False
        
        logger.info("RetrievalService initialized")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenizer: lowercases and splits on non-alphanumeric characters.
        
        Args:
            text: Input text to tokenize.
            
        Returns:
            List of token strings.
        """
        if not text or not isinstance(text, str):
            return []
        
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def build_index(self, problems: List[Dict[str, Any]]) -> None:
        """
        Build the BM25 index from a list of problems.
        
        Args:
            problems: List of problem dictionaries, each expected to have
                     'tool_descriptions' key.
                     
        Raises:
            RetrievalServiceError: If building the index fails.
        """
        if not problems:
            raise RetrievalServiceError("Cannot build index with empty problems list")
        
        self.tool_descriptions = []
        self.tokenized_corpus = []
        
        for i, problem in enumerate(problems):
            try:
                descs = extract_tool_descriptions(problem)
                if not descs:
                    continue
                
                # Store all descriptions for this problem
                for desc in descs:
                    self.tool_descriptions.append(desc)
                    tokenized = self._tokenize(desc)
                    if tokenized:
                        self.tokenized_corpus.append(tokenized)
                    else:
                        logger.warning(f"Empty tokenization for description {len(self.tool_descriptions)}")
                        
            except ToolMapperError as e:
                logger.warning(f"Skipping problem {i} due to tool mapping error: {e}")
        
        if not self.tokenized_corpus:
            raise RetrievalServiceError(
                "Failed to build index: No valid tool descriptions found in problems"
            )
        
        try:
            self.bm25_index = BM25Okapi(self.tokenized_corpus)
            self._built = True
            logger.info(f"BM25 index built successfully with {len(self.tokenized_corpus)} documents")
        except Exception as e:
            raise RetrievalServiceError(f"Failed to create BM25 index: {e}")
    
    def retrieve_top_k(
        self,
        thinking_trace: str,
        k: int = 3
    ) -> Tuple[List[str], List[float]]:
        """
        Retrieve top-k tool descriptions based on thinking trace.
        
        Args:
            thinking_trace: The thinking trace text to search against.
            k: Number of results to return.
            
        Returns:
            Tuple of (list of tool descriptions, list of scores).
            
        Raises:
            RetrievalServiceError: If the index is not built or retrieval fails.
        """
        if not self._built or self.bm25_index is None:
            raise RetrievalServiceError(
                "BM25 index not built. Call build_index() first."
            )
        
        if not thinking_trace or not isinstance(thinking_trace, str):
            # Handle empty or invalid thinking trace
            logger.warning("Empty or invalid thinking trace provided")
            return [], []
        
        try:
            query_tokens = self._tokenize(thinking_trace)
            
            if not query_tokens:
                logger.warning("Query tokenization resulted in empty list")
                return [], []
            
            # Get BM25 scores
            doc_scores = self.bm25_index.get_scores(query_tokens)
            
            # Handle edge case where scores might be NaN or inf
            doc_scores = np.nan_to_num(doc_scores, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Get top-k indices
            if len(doc_scores) == 0:
                return [], []
            
            top_k_indices = np.argsort(doc_scores)[::-1][:k]
            
            results = []
            scores = []
            
            for idx in top_k_indices:
                if doc_scores[idx] > 0:  # Only include if score is positive
                    results.append(self.tool_descriptions[idx])
                    scores.append(float(doc_scores[idx]))
            
            logger.debug(f"Retrieved {len(results)} tools for query")
            return results, scores
            
        except Exception as e:
            raise RetrievalServiceError(f"Retrieval failed: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the built index.
        
        Returns:
            Dictionary with index statistics.
        """
        return {
            "built": self._built,
            "num_documents": len(self.tool_descriptions),
            "num_tokens_corpus": len(self.tokenized_corpus),
            "avg_doc_length": (
                np.mean([len(t) for t in self.tokenized_corpus])
                if self.tokenized_corpus else 0.0
            )
        }

def create_retrieval_service(tool_map_path: Optional[str] = None) -> RetrievalService:
    """
    Factory function to create a RetrievalService instance.
    
    Args:
        tool_map_path: Optional path to the tool mapping JSON.
        
    Returns:
        Configured RetrievalService instance.
    """
    return RetrievalService(tool_map_path=tool_map_path)

def retrieve_top_tools(
    problems: List[Dict[str, Any]],
    thinking_traces: List[str],
    k: int = 3
) -> List[Dict[str, Any]]:
    """
    Convenience function to retrieve top-k tools for multiple problems.
    
    Args:
        problems: List of problem dictionaries.
        thinking_traces: List of thinking traces corresponding to each problem.
        k: Number of results per query.
        
    Returns:
        List of dictionaries with problem_id, retrieved_tools, and scores.
        
    Raises:
        RetrievalServiceError: If retrieval fails.
    """
    if len(problems) != len(thinking_traces):
        raise RetrievalServiceError(
            "problems and thinking_traces must have the same length"
        )
    
    service = RetrievalService()
    service.build_index(problems)
    
    results = []
    for i, trace in enumerate(thinking_traces):
        problem_id = problems[i].get('problem_id', f'problem_{i}')
        
        try:
            tools, scores = service.retrieve_top_k(trace, k=k)
            results.append({
                'problem_id': problem_id,
                'retrieved_tools': tools,
                'tool_scores': scores,
                'num_tools_retrieved': len(tools)
            })
        except RetrievalServiceError as e:
            logger.error(f"Retrieval failed for problem {problem_id}: {e}")
            results.append({
                'problem_id': problem_id,
                'retrieved_tools': [],
                'tool_scores': [],
                'num_tools_retrieved': 0,
                'error': str(e)
            })
    
    return results

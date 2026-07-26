import os
from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
from rank_bm25 import BM25Okapi
import re

logger = logging.getLogger(__name__)

class RetrievalService:
    """
    Service to build BM25 index from tool descriptions and retrieve
    the top-ranked tools for a given problem thinking prefix.
    """

    def __init__(self, tool_descriptions: List[str]):
        """
        Initialize the RetrievalService with a list of tool descriptions.
        
        Args:
            tool_descriptions: List of tool description strings to index.
        """
        self.tool_descriptions = tool_descriptions
        self.bm25_index = None
        self._build_index()

    def _build_index(self):
        """
        Build the BM25 index from the provided tool descriptions.
        Tokenizes each description and creates the index.
        """
        if not self.tool_descriptions:
            logger.warning("No tool descriptions provided for BM25 indexing.")
            self.bm25_index = None
            return

        # Tokenize descriptions: lowercase, split on non-alphanumeric
        tokenized_docs = [
            re.findall(r'\w+', doc.lower()) 
            for doc in self.tool_descriptions
        ]
        
        try:
            self.bm25_index = BM25Okapi(tokenized_docs)
            logger.info(f"BM25 index built successfully with {len(self.tool_descriptions)} tools.")
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            self.bm25_index = None

    def retrieve_top_k(self, query_text: str, k: int = 5) -> Tuple[List[str], List[int]]:
        """
        Retrieve the top-k tool descriptions most relevant to the query text.
        
        Args:
            query_text: The thinking prefix or query string to search against.
            k: Number of top results to retrieve.
            
        Returns:
            Tuple of (list of retrieved tool descriptions, list of their original indices).
            Returns empty lists if index is missing or query yields no results.
        """
        if self.bm25_index is None or not self.tool_descriptions:
            logger.warning("BM25 index is not available. Returning empty results.")
            return [], []

        # Tokenize query
        query_tokens = re.findall(r'\w+', query_text.lower())
        
        if not query_tokens:
            logger.warning("Query yielded no tokens. Returning empty results.")
            return [], []

        try:
            # Get scores for all documents
            doc_scores = self.bm25_index.get_scores(query_tokens)
            
            # Get indices of top-k scores
            # Handle case where all scores might be 0 or negative
            top_k_indices = np.argsort(doc_scores)[::-1][:k]
            
            retrieved_tools = []
            retrieved_indices = []
            
            for idx in top_k_indices:
                # Only include if score > 0 (meaningful match)
                if doc_scores[idx] > 0:
                    retrieved_tools.append(self.tool_descriptions[idx])
                    retrieved_indices.append(int(idx))
                
                # If we have enough valid results, stop
                if len(retrieved_tools) >= k:
                    break
                    
            logger.debug(f"Retrieved {len(retrieved_tools)} tools for query (k={k})")
            return retrieved_tools, retrieved_indices
            
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return [], []

    def get_retrieval_stats(self, query_text: str, k: int = 5) -> Dict[str, Any]:
        """
        Get statistics about the retrieval for a specific query.
        
        Args:
            query_text: The query string.
            k: Number of top results to consider.
            
        Returns:
            Dictionary containing retrieval statistics.
        """
        retrieved_tools, retrieved_indices = self.retrieve_top_k(query_text, k)
        
        stats = {
            "query_tokens": len(re.findall(r'\w+', query_text.lower())),
            "tools_retrieved_count": len(retrieved_tools),
            "tools_retrieved": retrieved_tools,
            "retrieved_indices": retrieved_indices,
            "index_size": len(self.tool_descriptions) if self.tool_descriptions else 0
        }
        
        return stats

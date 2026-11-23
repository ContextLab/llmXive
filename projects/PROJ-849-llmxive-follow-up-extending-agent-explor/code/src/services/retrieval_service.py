"""
Retrieval Service for Semantic Divergence Diagnostic.
Implements BM25-based tool description retrieval.
"""

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
    Service to build BM25 index from tool descriptions and retrieve relevant tools.
    """

    def __init__(self, corpus: List[List[str]]):
        """
        Initialize the retrieval service with a corpus of tool descriptions.

        Args:
            corpus: List of lists of strings, where each inner list represents
                    the tool descriptions for a specific problem.
        """
        if not corpus:
            logger.warning("Empty corpus provided to RetrievalService. Index will be empty.")

        # Tokenize the corpus for BM25
        self.tokenized_corpus = []
        for doc in corpus:
            if not isinstance(doc, list):
                raise RetrievalServiceError(f"Corpus document must be a list of strings, got {type(doc)}")
            tokenized_doc = []
            for sentence in doc:
                if not isinstance(sentence, str):
                    raise RetrievalServiceError(f"Document item must be a string, got {type(sentence)}")
                # Simple tokenization: lowercase and split by non-alphanumeric
                tokens = re.findall(r'\w+', sentence.lower())
                tokenized_doc.extend(tokens)
            self.tokenized_corpus.append(tokenized_doc)

        # Build BM25 index
        try:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        except Exception as e:
            raise RetrievalServiceError(f"Failed to initialize BM25 index: {e}")

        logger.info(f"RetrievalService initialized with {len(self.tokenized_corpus)} documents.")

    def retrieve(self, query: str, top_k: int = 10) -> List[str]:
        """
        Retrieve the top-k most relevant tool descriptions for a given query.

        Args:
            query: The query string (e.g., the thinking prefix of a problem).
            top_k: Number of results to retrieve (default 10).

        Returns:
            List of retrieved tool description strings. Returns empty list if
            no results are found or query is empty.
        """
        if not query or not query.strip():
            logger.debug("Empty query provided, returning empty list.")
            return []

        # Tokenize query
        query_tokens = re.findall(r'\w+', query.lower())

        if not query_tokens:
            logger.debug("Query tokenized to empty list, returning empty list.")
            return []

        # Get BM25 scores
        try:
            scores = self.bm25.get_scores(query_tokens)
        except Exception as e:
            logger.error(f"Error during BM25 scoring: {e}")
            return []

        # Handle edge case where all scores are zero or NaN
        if np.all(scores == 0) or np.all(np.isnan(scores)):
            logger.debug("All scores are zero or NaN, returning empty list.")
            return []

        # Get indices of top-k scores
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Filter out zero-score results (optional, but ensures relevance)
        retrieved = []
        for idx in top_indices:
            if scores[idx] > 0:
                # Map index back to original document string list
                # We need to return the original strings, not tokens
                original_doc = corpus[idx]  # type: ignore
                # Concatenate or return list? Task says "Retrieve up to 10 tool descriptions"
                # Assuming we return the individual strings from the top docs
                # If a doc has multiple sentences, we might want to return all or just the top one?
                # The spec says "corpus (list of lists of strings)", and we retrieve "tool descriptions".
                # Let's return the full list of strings for the top-k documents, flattened or kept as list?
                # "Retrieve up to 10 plausible tool descriptions" -> implies individual strings.
                # However, the BM25 operates on documents (lists of strings combined).
                # Let's return the list of strings corresponding to the top-k documents.
                # To be safe and consistent with "up to 10", we will take the top-k documents
                # and return their content. If a document has multiple strings, we return them.
                # But the constraint is "up to 10". If a document has 5 strings, and we take 3 docs,
                # we get 15 strings. That might violate "up to 10".
                # Interpretation: "Retrieve up to 10 [documents] of tool descriptions".
                # Or "Retrieve up to 10 [individual strings]".
                # Given BM25 ranks documents, we return the top-k documents.
                # If the downstream expects a flat list of strings, we might need to flatten.
                # Let's assume the input to downstream is a list of strings (the tool descriptions).
                # We will flatten the top-k documents into a single list of strings,
                # but limit the total count to `top_k` if necessary?
                # Actually, the task says: "Retrieve up to 10 plausible tool descriptions per problem".
                # This likely means 10 individual strings.
                # So we need to flatten the top-k documents and take the first 10 strings.
                
                # Let's flatten all top-k documents first
                flat_results = []
                for i in top_indices:
                    if scores[i] > 0:
                        flat_results.extend(corpus[i]) # type: ignore

                # Limit to top_k strings
                final_results = flat_results[:top_k]
                return final_results

        # Fallback if no positive scores
        return []

# Helper function to create the service easily
def create_retrieval_service(corpus: List[List[str]]) -> RetrievalService:
    """
    Create a RetrievalService instance from a corpus.

    Args:
        corpus: List of lists of strings.

    Returns:
        RetrievalService instance.
    """
    return RetrievalService(corpus)

# Helper function for direct retrieval
def retrieve_top_tools(corpus: List[List[str]], query: str, top_k: int = 10) -> List[str]:
    """
    Convenience function to retrieve top-k tools from a corpus given a query.

    Args:
        corpus: List of lists of strings.
        query: Query string.
        top_k: Number of tools to retrieve.

    Returns:
        List of retrieved tool description strings.
    """
    service = create_retrieval_service(corpus)
    return service.retrieve(query, top_k)
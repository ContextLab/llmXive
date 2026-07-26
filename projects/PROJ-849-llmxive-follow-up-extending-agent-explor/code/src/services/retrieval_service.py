"""
Retrieval Service for Semantic Divergence Diagnostic.

This module implements the BM25 retrieval logic to match thinking traces
against a repository of tool descriptions. It builds an index from the
loaded tool mappings and retrieves the top-k most relevant tool descriptions
for a given query (thinking prefix).
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple

from rank_bm25 import BM25Okapi

from src.lib.tool_loader import load_tool_mapping, ToolLoaderError
from src.lib import config


class RetrievalServiceError(Exception):
    """Custom exception for retrieval service errors."""
    pass


class RetrievalService:
    """
    Service class to handle BM25 index creation and retrieval operations.

    This service loads the tool mapping, tokenizes the tool descriptions,
    builds a BM25 index, and provides methods to retrieve top-ranked
    tools based on a query string.
    """

    def __init__(self, tool_mapping: Dict[str, Any]):
        """
        Initialize the RetrievalService with a tool mapping.

        Args:
            tool_mapping: A dictionary containing tool definitions,
                          expected to have a 'tools' key with a list of
                          tool objects containing 'name' and 'description'.

        Raises:
            RetrievalServiceError: If the tool mapping is invalid or empty.
        """
        if not tool_mapping or 'tools' not in tool_mapping:
            raise RetrievalServiceError(
                "Invalid tool mapping: missing 'tools' key or empty mapping."
            )

        tools = tool_mapping['tools']
        if not isinstance(tools, list) or len(tools) == 0:
            raise RetrievalServiceError(
                "Invalid tool mapping: 'tools' must be a non-empty list."
            )

        self.tool_mapping = tool_mapping
        self.tools = tools
        self.bm25_index: Optional[BM25Okapi] = None
        self.tokenized_corpus: List[List[str]] = []

        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize a text string into a list of lowercase words.

        Args:
            text: The input text to tokenize.

        Returns:
            A list of lowercase alphanumeric tokens.
        """
        if not text:
            return []
        # Convert to lowercase and split by non-alphanumeric characters
        tokens = re.findall(r'\w+', text.lower())
        return tokens

    def _build_index(self) -> None:
        """
        Build the BM25 index from the loaded tool descriptions.

        This method iterates over the tools, extracts their descriptions,
        tokenizes them, and creates a BM25Okapi index.

        Raises:
            RetrievalServiceError: If index building fails.
        """
        try:
            self.tokenized_corpus = []
            for tool in self.tools:
                description = tool.get('description', '')
                if not description:
                    # Skip tools without descriptions but log a warning if needed
                    continue
                tokens = self._tokenize(description)
                if tokens:
                    self.tokenized_corpus.append(tokens)

            if not self.tokenized_corpus:
                raise RetrievalServiceError(
                    "No valid tool descriptions found to build the BM25 index."
                )

            self.bm25_index = BM25Okapi(self.tokenized_corpus)

        except Exception as e:
            raise RetrievalServiceError(f"Failed to build BM25 index: {e}") from e

    def retrieve_top_k(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve the top-k most relevant tools for a given query.

        Args:
            query: The search query (e.g., a thinking trace prefix).
            k: The number of top results to return.

        Returns:
            A list of dictionaries containing tool details (name, description, score).

        Raises:
            RetrievalServiceError: If retrieval fails or index is not built.
        """
        if not self.bm25_index:
            raise RetrievalServiceError("BM25 index is not built.")

        if not query or not query.strip():
            # Return empty list for empty query
            return []

        try:
            query_tokens = self._tokenize(query)
            if not query_tokens:
                return []

            # Get BM25 scores
            scores = self.bm25_index.get_scores(query_tokens)

            # Get indices of top-k scores
            top_k_indices = scores.argsort()[::-1][:k]

            results = []
            # We need to map back to the original tools list.
            # Since we might have skipped tools without descriptions,
            # we need to track which tool corresponds to which tokenized entry.
            # To do this robustly, we rebuild the mapping or filter tools first.
            
            # Re-approach: Filter tools with descriptions first to align indices
            valid_tools = [
                tool for tool in self.tools
                if tool.get('description') and self._tokenize(tool['description'])
            ]

            # Re-calculate scores for valid tools only (BM25 index was built on valid_tools)
            # The index is already built on self.tokenized_corpus which corresponds to valid_tools
            
            for idx in top_k_indices:
                if idx < len(valid_tools):
                    tool = valid_tools[idx]
                    results.append({
                        'name': tool.get('name', 'Unknown'),
                        'description': tool.get('description', ''),
                        'score': float(scores[idx])
                    })

            return results

        except Exception as e:
            raise RetrievalServiceError(f"Retrieval failed: {e}") from e


def create_retrieval_service() -> RetrievalService:
    """
    Factory function to create a RetrievalService instance.

    Loads the tool mapping from the configured path and initializes the service.

    Returns:
        A configured RetrievalService instance.

    Raises:
        RetrievalServiceError: If tool mapping cannot be loaded or is invalid.
    """
    try:
        tool_mapping = load_tool_mapping()
        return RetrievalService(tool_mapping)
    except ToolLoaderError as e:
        raise RetrievalServiceError(f"Failed to load tool mapping: {e}") from e
    except Exception as e:
        raise RetrievalServiceError(f"Unexpected error creating retrieval service: {e}") from e


def retrieve_top_tools(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to retrieve top-k tools for a query.

    Creates a service instance and performs retrieval in one step.

    Args:
        query: The search query.
        k: Number of results to return.

    Returns:
        List of top-k tools with scores.

    Raises:
        RetrievalServiceError: If service creation or retrieval fails.
    """
    service = create_retrieval_service()
    return service.retrieve_top_k(query, k)
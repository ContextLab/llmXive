"""
BM25 Retriever Implementation for Code Search.

This module implements a BM25-based retrieval system using the rank_bm25 library.
It processes preprocessed code snippets and queries to perform efficient text-based
retrieval for the RAG code search pipeline.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from rank_bm25 import BM25

from src.data.models import CodeSnippet
from src.lib.utils import tokenize_and_truncate, set_random_seed

logger = logging.getLogger(__name__)


class BM25Retriever:
    """
    A BM25-based retriever for code snippets.

    This class builds an inverted index from a corpus of code snippets and
    performs retrieval based on BM25 scoring.
    """

    def __init__(self, snippets: List[CodeSnippet], index_path: Optional[Path] = None):
        """
        Initialize the BM25 retriever.

        Args:
            snippets: List of CodeSnippet objects to index.
            index_path: Optional path to save/load the index.
        """
        self.snippets = snippets
        self.index_path = index_path
        self.bm25_index = None
        self.tokenized_corpus = None

        # Tokenize the corpus for indexing
        logger.info(f"Tokenizing {len(snippets)} snippets for BM25 index...")
        self.tokenized_corpus = [self._tokenize_snippet(snippet) for snippet in snippets]

        # Build the BM25 index
        logger.info("Building BM25 index...")
        self.bm25_index = BM25(self.tokenized_corpus)

        # Save index if path provided
        if index_path:
            self.save_index(index_path)

    def _tokenize_snippet(self, snippet: CodeSnippet) -> List[str]:
        """
        Tokenize a single code snippet for BM25 indexing.

        Args:
            snippet: The code snippet to tokenize.

        Returns:
            List of tokens.
        """
        # Use the existing tokenization logic from utils
        # Note: This assumes the snippet text has been preprocessed (non-ASCII stripped, truncated)
        text = snippet.text
        tokens = tokenize_and_truncate(text, max_tokens=256)
        return tokens

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[CodeSnippet, float]]:
        """
        Retrieve the top-k snippets for a given query.

        Args:
            query: The query string.
            top_k: Number of results to return.

        Returns:
            List of (snippet, score) tuples sorted by score descending.
        """
        # Tokenize the query
        query_tokens = tokenize_and_truncate(query, max_tokens=256)

        # Compute scores
        scores = self.bm25_index.get_scores(query_tokens)

        # Get indices of top-k scores
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Create results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                results.append((self.snippets[idx], float(scores[idx])))

        return results

    def save_index(self, path: Path) -> None:
        """
        Save the BM25 index and corpus to disk.

        Args:
            path: Path to save the index.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump({
                'tokenized_corpus': self.tokenized_corpus,
                'snippets': self.snippets,
                'index_path': str(path)
            }, f)
        logger.info(f"BM25 index saved to {path}")

    @classmethod
    def load_index(cls, path: Path) -> 'BM25Retriever':
        """
        Load a BM25 index from disk.

        Args:
            path: Path to the index file.

        Returns:
            A BM25Retriever instance with the loaded index.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Index file not found: {path}")

        with open(path, 'rb') as f:
            data = pickle.load(f)

        # Reconstruct the retriever
        retriever = cls.__new__(cls)
        retriever.snippets = data['snippets']
        retriever.tokenized_corpus = data['tokenized_corpus']
        retriever.index_path = Path(data['index_path'])

        # Rebuild the BM25 index
        retriever.bm25_index = BM25(retriever.tokenized_corpus)

        logger.info(f"BM25 index loaded from {path}")
        return retriever


def load_bm25_retriever(data_path: Path, index_path: Optional[Path] = None) -> BM25Retriever:
    """
    Load or create a BM25 retriever from preprocessed data.

    Args:
        data_path: Path to the preprocessed JSONL/CSV file containing code snippets.
        index_path: Optional path to save/load the BM25 index.

    Returns:
        A BM25Retriever instance.
    """
    # Load snippets from the preprocessed data
    if data_path.suffix == '.jsonl':
        snippets = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                snippets.append(CodeSnippet(
                    id=data.get('id', ''),
                    text=data.get('text', ''),
                    language=data.get('language', ''),
                    repo=data.get('repo', ''),
                    ground_truth=data.get('ground_truth', [])
                ))
    elif data_path.suffix == '.csv':
        import csv
        snippets = []
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                snippets.append(CodeSnippet(
                    id=row.get('id', ''),
                    text=row.get('text', ''),
                    language=row.get('language', ''),
                    repo=row.get('repo', ''),
                    ground_truth=row.get('ground_truth', '').split(',') if row.get('ground_truth') else []
                ))
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

    logger.info(f"Loaded {len(snippets)} snippets from {data_path}")

    # Check if index exists
    if index_path and index_path.exists():
        logger.info(f"Loading existing BM25 index from {index_path}")
        return BM25Retriever.load_index(index_path)

    # Create new retriever
    logger.info("Creating new BM25 index...")
    retriever = BM25Retriever(snippets, index_path)
    return retriever


def evaluate_retrieval(
    retriever: BM25Retriever,
    queries: List[str],
    ground_truth: Dict[str, List[str]],
    k_values: List[int] = [5, 10, 20]
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate the BM25 retriever on a set of queries.

    Args:
        retriever: The BM25Retriever instance.
        queries: List of query strings.
        ground_truth: Dictionary mapping query IDs to lists of ground truth snippet IDs.
        k_values: List of k values for evaluation.

        Note: This function assumes queries have IDs that match the ground_truth keys.
        If queries are just strings, you'll need to map them to IDs first.

    Returns:
        Dictionary of metrics for each k value.
    """
    from src.models.metrics import precision_at_k, recall_at_k, ndcg_at_k

    results = {}

    for k in k_values:
        precisions = []
        recalls = []
        ndcgs = []

        for i, query in enumerate(queries):
            query_id = f"query_{i}"  # Assuming query ID is query_0, query_1, etc.
            gt_ids = set(ground_truth.get(query_id, []))

            # Retrieve results
            retrieved = retriever.retrieve(query, top_k=k)
            retrieved_ids = set(snippet.id for snippet, _ in retrieved)

            # Calculate metrics
            if gt_ids:
                precisions.append(precision_at_k(retrieved_ids, gt_ids, k))
                recalls.append(recall_at_k(retrieved_ids, gt_ids, len(gt_ids)))
                ndcgs.append(ndcg_at_k(retrieved_ids, gt_ids, k))

        results[f'P@{k}'] = sum(precisions) / len(precisions) if precisions else 0.0
        results[f'R@{k}'] = sum(recalls) / len(recalls) if recalls else 0.0
        results[f'nDCG@{k}'] = sum(ndcgs) / len(ndcgs) if ndcgs else 0.0

    return results


def main():
    """
    Main function to demonstrate BM25 retrieval.

    This function:
    1. Loads preprocessed data
    2. Builds/loads BM25 index
    3. Runs retrieval on sample queries
    4. Outputs results
    """
    set_random_seed(42)

    # Configuration
    data_path = Path("data/processed/code_searchnet_processed.jsonl")
    index_path = Path("data/processed/bm25_index.pkl")

    # Load retriever
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return

    retriever = load_bm25_retriever(data_path, index_path)

    # Sample queries
    sample_queries = [
        "function to sort a list",
        "read a file in python",
        "calculate fibonacci number"
    ]

    # Retrieve and display results
    logger.info("Running sample retrieval...")
    for query in sample_queries:
        logger.info(f"\nQuery: {query}")
        results = retriever.retrieve(query, top_k=5)
        for i, (snippet, score) in enumerate(results):
            logger.info(f"  {i+1}. Score: {score:.4f} | ID: {snippet.id} | Lang: {snippet.language}")
            logger.info(f"     Text preview: {snippet.text[:100]}...")

    logger.info("BM25 retrieval demonstration complete.")


if __name__ == "__main__":
    main()

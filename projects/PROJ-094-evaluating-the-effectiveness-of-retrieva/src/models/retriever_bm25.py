"""
BM25 Retriever Implementation for Code Search.

This module implements the BM25 retrieval algorithm using the `rank_bm25` library
on preprocessed code snippets. It provides functionality to index a corpus of code,
retrieve relevant snippets for a given query, and evaluate retrieval performance.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

from src.data.models import CodeSnippet, RetrievalMethod
from src.data.preprocess import tokenize_and_truncate
from src.lib.utils import set_seed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BM25Retriever:
    """
    BM25 Retriever for code search.

    Attributes:
        bm25: The BM25 index object.
        tokenized_corpus: The tokenized corpus used for indexing.
        snippet_ids: List of snippet IDs corresponding to the tokenized corpus.
    """

    def __init__(self, tokenized_corpus: List[List[str]], snippet_ids: List[str]):
        """
        Initialize the BM25 retriever.

        Args:
            tokenized_corpus: A list of tokenized documents (lists of tokens).
            snippet_ids: A list of unique identifiers for each document.
        """
        if len(tokenized_corpus) != len(snippet_ids):
            raise ValueError("tokenized_corpus and snippet_ids must have the same length.")

        self.tokenized_corpus = tokenized_corpus
        self.snippet_ids = snippet_ids
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"BM25 index created with {len(tokenized_corpus)} documents.")

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Retrieve the top-k most relevant snippets for a given query.

        Args:
            query: The search query string.
            top_k: The number of results to return.

        Returns:
            A list of tuples (snippet_id, score) sorted by score descending.
        """
        query_tokens = tokenize_and_truncate(query)
        scores = self.bm25.get_scores(query_tokens)

        # Get indices of top_k scores
        # Handle case where there are fewer documents than top_k
        actual_k = min(top_k, len(scores))
        top_indices = np.argsort(scores)[::-1][:actual_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include positive scores
                results.append((self.snippet_ids[idx], float(scores[idx])))

        return results

    def save(self, path: Path) -> None:
        """
        Save the retriever state to disk.

        Args:
            path: The directory path where the retriever will be saved.
        """
        path.mkdir(parents=True, exist_ok=True)
        index_path = path / "bm25_index.pkl"
        with open(index_path, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "tokenized_corpus": self.tokenized_corpus,
                "snippet_ids": self.snippet_ids
            }, f)
        logger.info(f"BM25 retriever saved to {index_path}")

    @classmethod
    def load(cls, path: Path) -> "BM25Retriever":
        """
        Load a retriever from disk.

        Args:
            path: The directory path where the retriever is saved.

        Returns:
            An instance of BM25Retriever.
        """
        index_path = path / "bm25_index.pkl"
        if not index_path.exists():
            raise FileNotFoundError(f"BM25 index not found at {index_path}")

        with open(index_path, "rb") as f:
            data = pickle.load(f)

        logger.info(f"BM25 retriever loaded from {index_path}")
        return cls(data["tokenized_corpus"], data["snippet_ids"])


def load_bm25_retriever(
    data_dir: Path,
    split: str = "train",
    cache_dir: Optional[Path] = None
) -> BM25Retriever:
    """
    Load or create a BM25 retriever from preprocessed data.

    Args:
        data_dir: The directory containing preprocessed data (JSONL files).
        split: The data split to use ('train' or 'test').
        cache_dir: Optional directory to cache the index. If None, index is built in memory.

    Returns:
        A BM25Retriever instance.
    """
    # Determine the path to the processed data
    if split not in ["train", "test"]:
        raise ValueError(f"Invalid split: {split}. Must be 'train' or 'test'.")

    processed_data_path = data_dir / f"{split}.jsonl"
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_data_path}")

    # Load snippets from JSONL
    snippets = []
    with open(processed_data_path, "r", encoding="utf-8") as f:
        for line in f:
            snippet_data = json.loads(line)
            # Expected fields: id, code, tokens (precomputed by preprocess.py)
            snippets.append(snippet_data)

    if not snippets:
        raise ValueError(f"No snippets found in {processed_data_path}")

    snippet_ids = [s["id"] for s in snippets]
    tokenized_corpus = [s["tokens"] for s in snippets]

    # Check for cached index
    if cache_dir:
        cache_dir = Path(cache_dir)
        cached_retriever_path = cache_dir / split
        if cached_retriever_path.exists():
            logger.info(f"Loading cached BM25 index from {cached_retriever_path}")
            return BM25Retriever.load(cached_retriever_path)

    # Create retriever
    retriever = BM25Retriever(tokenized_corpus, snippet_ids)

    # Save to cache if cache_dir is provided
    if cache_dir:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached_retriever_path = cache_dir / split
        retriever.save(cached_retriever_path)

    return retriever


def evaluate_retrieval(
    retriever: BM25Retriever,
    queries: List[Dict[str, Any]],
    k_values: List[int] = [1, 5, 10, 20]
) -> Dict[str, Any]:
    """
    Evaluate the retriever on a set of queries with ground truth.

    Args:
        retriever: The BM25Retriever instance.
        queries: A list of query dictionaries with 'id', 'query', and 'ground_truth_ids'.
        k_values: List of K values for evaluation metrics.

    Returns:
        A dictionary containing evaluation metrics for each K value.
    """
    from src.models.metrics import precision_at_k, recall_at_k, ndcg_at_k

    results = {f"p@{k}": [] for k in k_values}
    results.update({f"r@{k}": [] for k in k_values})
    results.update({f"ndcg@{k}": [] for k in k_values})

    for q in queries:
        query_id = q["id"]
        query_text = q["query"]
        ground_truth_ids = set(q["ground_truth_ids"])

        retrieved = retriever.retrieve(query_text, top_k=max(k_values))
        retrieved_ids = [r[0] for r in retrieved]

        for k in k_values:
            retrieved_k = retrieved_ids[:k]
            if not retrieved_k:
                results[f"p@{k}"].append(0.0)
                results[f"r@{k}"].append(0.0)
                results[f"ndcg@{k}"].append(0.0)
                continue

            p = precision_at_k(retrieved_k, ground_truth_ids)
            r = recall_at_k(retrieved_k, ground_truth_ids)
            ndcg = ndcg_at_k(retrieved_k, ground_truth_ids)

            results[f"p@{k}"].append(p)
            results[f"r@{k}"].append(r)
            results[f"ndcg@{k}"].append(ndcg)

    # Compute averages
    summary = {}
    for k in k_values:
        summary[f"p@{k}"] = np.mean(results[f"p@{k}"])
        summary[f"r@{k}"] = np.mean(results[f"r@{k}"])
        summary[f"ndcg@{k}"] = np.mean(results[f"ndcg@{k}"])

    return summary


def main():
    """
    Main function to demonstrate BM25 retrieval and evaluation.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="BM25 Retriever for Code Search")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to preprocessed data directory")
    parser.add_argument("--split", type=str, default="train", choices=["train", "test"], help="Data split to use")
    parser.add_argument("--cache_dir", type=str, default=None, help="Directory to cache the index")
    parser.add_argument("--eval_queries", type=str, default=None, help="Path to JSON file with evaluation queries")
    parser.add_argument("--top_k", type=int, default=10, help="Number of results to retrieve")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()
    set_seed(args.seed)

    data_dir = Path(args.data_dir)
    cache_dir = Path(args.cache_dir) if args.cache_dir else None

    try:
        retriever = load_bm25_retriever(data_dir, args.split, cache_dir)
        logger.info(f"Successfully loaded BM25 retriever for split '{args.split}'")
    except Exception as e:
        logger.error(f"Failed to load BM25 retriever: {e}")
        sys.exit(1)

    # Example retrieval
    example_queries = [
        "function to calculate fibonacci number",
        "class for handling HTTP requests",
        "algorithm to sort a list of integers"
    ]

    logger.info("\n--- Example Retrievals ---")
    for i, query in enumerate(example_queries):
        results = retriever.retrieve(query, top_k=args.top_k)
        logger.info(f"\nQuery {i+1}: {query}")
        for rank, (snippet_id, score) in enumerate(results, 1):
            logger.info(f"  {rank}. {snippet_id} (score: {score:.4f})")

    # Evaluation if queries provided
    if args.eval_queries:
        eval_path = Path(args.eval_queries)
        if not eval_path.exists():
            logger.error(f"Evaluation queries file not found: {eval_path}")
            sys.exit(1)

        with open(eval_path, "r", encoding="utf-8") as f:
            queries = json.load(f)

        logger.info(f"\n--- Evaluation on {len(queries)} queries ---")
        metrics = evaluate_retrieval(retriever, queries)
        for metric, value in metrics.items():
            logger.info(f"{metric}: {value:.4f}")


if __name__ == "__main__":
    main()

"""
Retriever module for CiteVQA text retrieval pipeline.

Encodes text chunks using all-MiniLM-L6-v2 and retrieves top-k
relevant chunks for a given query.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path

from config import get_config_dict


class TextRetriever:
    """
    Encodes text chunks and performs similarity-based retrieval.

    Uses all-MiniLM-L6-v2 model for encoding.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", config: Optional[Dict] = None):
        """
        Initialize the retriever with the specified model.

        Args:
            model_name: Name of the sentence-transformers model to use.
            config: Configuration dictionary. If None, loads from config.py.
        """
        self.config = config or get_config_dict()
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)
        self.chunk_embeddings: Optional[np.ndarray] = None
        self.chunk_ids: List[str] = []
        self.chunk_texts: List[str] = []

    def load_chunks(self, chunks: List[Dict[str, str]]) -> None:
        """
        Load and encode text chunks for retrieval.

        Args:
            chunks: List of dictionaries with 'id' and 'text' keys.
        """
        self.chunk_ids = [chunk['id'] for chunk in chunks]
        self.chunk_texts = [chunk['text'] for chunk in chunks]

        # Encode all chunks
        self.chunk_embeddings = self.model.encode(
            self.chunk_texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(self.chunk_embeddings, axis=1, keepdims=True)
        self.chunk_embeddings = self.chunk_embeddings / norms

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        """
        Retrieve top-k most relevant chunks for a given query.

        Args:
            query: The query string.
            top_k: Number of chunks to retrieve.

        Returns:
            List of dictionaries containing chunk_id, text, and similarity score.
        """
        if self.chunk_embeddings is None:
            raise ValueError("No chunks loaded. Call load_chunks() first.")

        # Encode query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        )
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Compute cosine similarity (dot product of normalized vectors)
        similarities = np.dot(self.chunk_embeddings, query_embedding.T).flatten()

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                'chunk_id': self.chunk_ids[idx],
                'text': self.chunk_texts[idx],
                'similarity': float(similarities[idx])
            })

        return results

    def retrieve_batch(self, queries: List[str], top_k: int = 5) -> List[List[Dict[str, any]]]:
        """
        Retrieve top-k chunks for multiple queries.

        Args:
            queries: List of query strings.
            top_k: Number of chunks to retrieve per query.

        Returns:
            List of lists, where each inner list contains retrieval results for one query.
        """
        return [self.retrieve(query, top_k) for query in queries]


def load_processed_data(data_path: str) -> List[Dict[str, str]]:
    """
    Load processed text chunks from a JSON file.

    Args:
        data_path: Path to the JSON file containing chunks.

    Returns:
        List of dictionaries with 'id' and 'text' keys.
    """
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list format and dict with 'chunks' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'chunks' in data:
        return data['chunks']
    else:
        raise ValueError(f"Unexpected data format in {data_path}")


def main():
    """
    Main function to demonstrate retriever functionality.
    Loads processed data and performs retrieval on sample queries.
    """
    config = get_config_dict()
    data_dir = Path(config['data_dir'])
    processed_dir = data_dir / 'processed'

    # Load processed chunks
    chunks_file = processed_dir / 'citevqa_chunks.json'
    if not chunks_file.exists():
        print(f"Error: Chunks file not found at {chunks_file}")
        print("Please run T006 to fetch and process the dataset first.")
        return

    print(f"Loading chunks from {chunks_file}...")
    chunks = load_processed_data(str(chunks_file))
    print(f"Loaded {len(chunks)} chunks.")

    # Initialize retriever
    retriever = TextRetriever()
    retriever.load_chunks(chunks)

    # Sample queries for demonstration
    sample_queries = [
        "What is the role of transcription factors in gene regulation?",
        "How does chromatin accessibility affect gene expression?",
        "Describe the mechanism of RNA polymerase binding."
    ]

    print("\nPerforming retrieval on sample queries...")
    for i, query in enumerate(sample_queries, 1):
        print(f"\nQuery {i}: {query}")
        results = retriever.retrieve(query, top_k=3)
        for j, result in enumerate(results, 1):
            print(f"  {j}. Chunk ID: {result['chunk_id']}")
            print(f"     Similarity: {result['similarity']:.4f}")
            print(f"     Text (truncated): {result['text'][:100]}...")

    # Save retrieval results for testing
    results_output = processed_dir / 'retrieval_sample_results.json'
    all_results = []
    for query in sample_queries:
        all_results.append({
            'query': query,
            'retrieved_chunks': retriever.retrieve(query, top_k=3)
        })

    with open(results_output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    print(f"\nSample retrieval results saved to {results_output}")


if __name__ == "__main__":
    main()
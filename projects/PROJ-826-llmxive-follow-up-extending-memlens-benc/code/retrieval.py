import os
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from code.utils.logger import get_logger, log_retrieval_results

logger = get_logger(__name__)

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    Handles zero vectors by returning 0.0.
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    dot_product = np.dot(vec_a, vec_b)
    return float(dot_product / (norm_a * norm_b))

def retrieve_top_k(
    query_vector: np.ndarray,
    store_vectors: List[np.ndarray],
    store_metadata: List[Dict[str, Any]],
    k: int = 5
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Retrieve top-k items based on cosine similarity.
    
    Args:
        query_vector: The query embedding.
        store_vectors: List of stored embeddings.
        store_metadata: List of metadata dictionaries corresponding to store_vectors.
        k: Number of top results to return.
        
    Returns:
        List of tuples (metadata, similarity_score) sorted by score descending.
    """
    if not store_vectors:
        return []
    
    similarities = []
    for i, vec in enumerate(store_vectors):
        sim = cosine_similarity(query_vector, vec)
        similarities.append((i, sim))
    
    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Get top k
    top_k_indices = similarities[:k]
    
    results = []
    for idx, score in top_k_indices:
        results.append((store_metadata[idx], score))
        
    return results

def run_coarse_retrieval(
    query: str,
    coarse_store_path: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Run retrieval on the Coarse store using text summaries.
    
    Args:
        query: The natural language query.
        coarse_store_path: Path to the coarse store JSON file.
        k: Number of top results.
        
    Returns:
        List of retrieved items with metadata and scores.
    """
    from code.preprocessing import get_text_embedding, load_sentence_transformer_model
    
    logger.info(f"Running Coarse retrieval for query: {query[:50]}...")
    
    # Load store
    with open(coarse_store_path, 'r') as f:
        store_data = json.load(f)
    
    # Extract vectors and metadata
    store_vectors = [np.array(item['embedding']) for item in store_data]
    store_metadata = [item for item in store_data]
    
    # Get query embedding
    model = load_sentence_transformer_model()
    query_vector = get_text_embedding(model, query)
    
    # Retrieve
    results = retrieve_top_k(query_vector, store_vectors, store_metadata, k)
    
    # Format results
    formatted_results = []
    for metadata, score in results:
        formatted_results.append({
            'metadata': metadata,
            'similarity_score': score
        })
        
    log_retrieval_results("coarse", len(formatted_results), query)
    return formatted_results

def run_medium_retrieval(
    query: str,
    medium_store_path: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Run retrieval on the Medium store using global CLIP embeddings.
    
    Args:
        query: The natural language query.
        medium_store_path: Path to the medium store JSON file.
        k: Number of top results.
        
    Returns:
        List of retrieved items with metadata and scores.
    """
    from code.preprocessing import get_text_embedding, load_sentence_transformer_model
    
    logger.info(f"Running Medium retrieval for query: {query[:50]}...")
    
    # Load store
    with open(medium_store_path, 'r') as f:
        store_data = json.load(f)
    
    # Extract vectors and metadata
    store_vectors = [np.array(item['embedding']) for item in store_data]
    store_metadata = [item for item in store_data]
    
    # Get query embedding
    model = load_sentence_transformer_model()
    query_vector = get_text_embedding(model, query)
    
    # Retrieve
    results = retrieve_top_k(query_vector, store_vectors, store_metadata, k)
    
    # Format results
    formatted_results = []
    for metadata, score in results:
        formatted_results.append({
            'metadata': metadata,
            'similarity_score': score
        })
        
    log_retrieval_results("medium", len(formatted_results), query)
    return formatted_results

def run_fine_retrieval(
    query: str,
    fine_store_path: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Run retrieval on the Fine store using text-only object captions.
    
    This implementation strictly adheres to the requirement that coordinates
    are stored as metadata but EXCLUDED from the similarity vector.
    The similarity vector is constructed ONLY from the concatenated object
    captions (text) using sentence-transformer embeddings.
    
    Args:
        query: The natural language query.
        fine_store_path: Path to the fine store JSON file.
        k: Number of top results.
        
    Returns:
        List of retrieved items with metadata (including coordinates) and scores.
    """
    from code.preprocessing import get_text_embedding, load_sentence_transformer_model
    
    logger.info(f"Running Fine retrieval for query: {query[:50]}...")
    
    # Load store
    with open(fine_store_path, 'r') as f:
        store_data = json.load(f)
    
    if not store_data:
        logger.warning("Fine store is empty.")
        return []
    
    store_vectors = []
    store_metadata = []
    
    # Construct embeddings from text-only object captions
    model = load_sentence_transformer_model()
    
    for item in store_data:
        # Extract object captions, ignoring coordinates for embedding
        # The item structure is expected to have 'objects' which is a list of dicts
        # Each dict has 'caption' (text) and 'bbox' (coordinates)
        objects = item.get('objects', [])
        captions = []
        
        for obj in objects:
            caption = obj.get('caption', '')
            if caption:
                captions.append(caption)
        
        # Concatenate all captions into a single text block for this item
        # This ensures the retrieval is based on the semantic content of all detected objects
        combined_text = " ".join(captions)
        
        if not combined_text.strip():
            # If no captions, use a fallback or skip
            # For robustness, we'll use a generic placeholder if no text exists
            combined_text = "no objects detected"
        
        # Generate embedding from text ONLY
        embedding = get_text_embedding(model, combined_text)
        
        store_vectors.append(embedding)
        
        # Store the full metadata (including bboxes) for the result
        store_metadata.append(item)
    
    # Get query embedding
    query_vector = get_text_embedding(model, query)
    
    # Retrieve
    results = retrieve_top_k(query_vector, store_vectors, store_metadata, k)
    
    # Format results
    formatted_results = []
    for metadata, score in results:
        formatted_results.append({
            'metadata': metadata,
            'similarity_score': score
        })
        
    log_retrieval_results("fine", len(formatted_results), query)
    return formatted_results

def save_retrieval_results(
    results: List[Dict[str, Any]],
    output_path: str,
    strategy: str
) -> None:
    """
    Save retrieval results to a JSON file.
    
    Args:
        results: List of retrieval results.
        output_path: Path to save the results.
        strategy: Strategy name (coarse, medium, fine).
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'strategy': strategy,
        'results': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """
    Main entry point for testing retrieval logic.
    This function demonstrates the retrieval process for all three stores.
    """
    # Example usage (paths would be configured via CLI or config in real usage)
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    
    coarse_store = data_dir / "stores" / "coarse_store.json"
    medium_store = data_dir / "stores" / "medium_store.json"
    fine_store = data_dir / "stores" / "fine_store.json"
    
    query = "What is happening in the image?"
    k = 5
    
    if coarse_store.exists():
        logger.info("Testing Coarse Retrieval...")
        coarse_results = run_coarse_retrieval(query, str(coarse_store), k)
        save_retrieval_results(coarse_results, str(data_dir / "retrieval_coarse.json"), "coarse")
    
    if medium_store.exists():
        logger.info("Testing Medium Retrieval...")
        medium_results = run_medium_retrieval(query, str(medium_store), k)
        save_retrieval_results(medium_results, str(data_dir / "retrieval_medium.json"), "medium")
        
    if fine_store.exists():
        logger.info("Testing Fine Retrieval...")
        fine_results = run_fine_retrieval(query, str(fine_store), k)
        save_retrieval_results(fine_results, str(data_dir / "retrieval_fine.json"), "fine")
        
    logger.info("Retrieval test completed.")

if __name__ == "__main__":
    main()
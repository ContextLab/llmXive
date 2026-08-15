"""
Query module for skill vector retrieval.

Handles generation of query vectors using sentence-transformers and
retrieval from the skill index with Out-of-Distribution (OOD) detection.
"""
import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from src.utils.config import get_project_root, get_results_path, set_seed
from src.retrieval.strategies import load_skill_index, single_nearest_neighbor

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_OOD_THRESHOLD = 0.8
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 5

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml or use defaults."""
    project_root = get_project_root()
    config_path = project_root / "config.yaml"
    
    if config_path.exists():
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('retrieval', {})
    return {}

def get_ood_threshold(config: Dict[str, Any]) -> float:
    """Get OOD threshold from config or use default."""
    return config.get('ood_threshold', DEFAULT_OOD_THRESHOLD)

def generate_query_vector(text: str, model_name: str = DEFAULT_MODEL_NAME) -> np.ndarray:
    """
    Generate a query vector from text using a sentence-transformer model.
    
    Args:
        text: The query text.
        model_name: Name of the sentence-transformer model to use.
        
    Returns:
        numpy array of shape (embedding_dim,)
    """
    logger.info(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    logger.info(f"Encoding text: '{text[:50]}...'")
    start_time = time.time()
    embedding = model.encode(text, convert_to_numpy=True)
    end_time = time.time()
    
    latency_ms = (end_time - start_time) * 1000
    logger.info(f"Embedding generated in {latency_ms:.2f}ms. Shape: {embedding.shape}")
    
    return embedding

def check_ood(query_vector: np.ndarray, index_vectors: np.ndarray, threshold: float) -> Tuple[bool, float]:
    """
    Check if a query is out-of-distribution based on distance to nearest neighbor.
    
    Args:
        query_vector: The query embedding vector.
        index_vectors: The skill index vectors (N, D).
        threshold: Maximum allowed cosine distance (default 0.8).
        
    Returns:
        Tuple of (is_ood, min_distance)
        
    Raises:
        ValueError: If the query is determined to be OOD.
    """
    # Normalize vectors for cosine similarity
    query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
    index_norms = index_vectors / (np.linalg.norm(index_vectors, axis=1, keepdims=True) + 1e-8)
    
    # Compute cosine similarities
    similarities = np.dot(index_norms, query_norm)
    
    # Compute cosine distances (1 - similarity)
    distances = 1.0 - similarities
    
    min_distance = np.min(distances)
    nearest_idx = np.argmin(distances)
    
    logger.info(f"Nearest neighbor distance: {min_distance:.4f} (threshold: {threshold})")
    
    if min_distance > threshold:
        raise ValueError(
            f"Query is Out-of-Distribution (OOD). "
            f"Distance to nearest skill: {min_distance:.4f} > threshold: {threshold}. "
            f"Nearest skill index: {nearest_idx}. "
            f"Consider adding this skill to the database or refining the query."
        )
    
    return False, min_distance

def retrieve_skills(
    query_vector: np.ndarray,
    index_vectors: np.ndarray,
    index_metadata: List[Dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
    threshold: Optional[float] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Retrieve top-k skills from the index, with OOD checking.
    
    Args:
        query_vector: The query embedding.
        index_vectors: The skill index vectors.
        index_metadata: Metadata for each skill in the index.
        top_k: Number of top skills to retrieve.
        threshold: OOD threshold (overrides config).
        config: Configuration dictionary.
        
    Returns:
        Dictionary containing retrieved skills and metrics.
        
    Raises:
        ValueError: If query is OOD.
    """
    if config is None:
        config = load_config()
    
    if threshold is None:
        threshold = get_ood_threshold(config)
    
    # Check for OOD
    logger.info("Performing OOD check...")
    is_ood, min_distance = check_ood(query_vector, index_vectors, threshold)
    
    # Perform retrieval
    logger.info(f"Retrieving top-{top_k} skills...")
    start_time = time.time()
    
    # Normalize for cosine similarity
    query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
    index_norms = index_vectors / (np.linalg.norm(index_vectors, axis=1, keepdims=True) + 1e-8)
    
    similarities = np.dot(index_norms, query_norm)
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    retrieval_time = (time.time() - start_time) * 1000
    
    retrieved_skills = []
    for idx in top_indices:
        skill_data = {
            'index': int(idx),
            'metadata': index_metadata[int(idx)],
            'similarity': float(similarities[idx]),
            'distance': float(1.0 - similarities[idx])
        }
        retrieved_skills.append(skill_data)
    
    result = {
        'query_vector': query_vector,
        'retrieved_skills': retrieved_skills,
        'metrics': {
            'embedding_latency_ms': 0.0,  # Should be set by caller
            'retrieval_latency_ms': retrieval_time,
            'is_ood': is_ood,
            'min_distance': min_distance,
            'threshold': threshold
        }
    }
    
    logger.info(f"Retrieved {len(retrieved_skills)} skills in {retrieval_time:.2f}ms")
    return result

def log_latency_metrics(
    embedding_latency: float,
    retrieval_latency: float,
    interpolation_latency: float = 0.0
) -> None:
    """
    Log latency metrics to data/results/latency_metrics.json.
    
    Args:
        embedding_latency: Time to generate query vector (ms).
        retrieval_latency: Time for index lookup (ms).
        interpolation_latency: Time to compute weighted average (ms).
    """
    results_path = get_results_path()
    metrics_file = results_path / "latency_metrics.json"
    
    metrics = {
        'embedding_latency_ms': embedding_latency,
        'retrieval_latency_ms': retrieval_latency,
        'interpolation_latency_ms': interpolation_latency,
        'total_skill_selection_latency_ms': embedding_latency + retrieval_latency + interpolation_latency
    }
    
    # Load existing metrics if file exists
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
        existing.append(metrics)
    else:
        existing = [metrics]
    
    # Save updated metrics
    with open(metrics_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    logger.info(f"Logged latency metrics to {metrics_file}")

def main() -> None:
    """
    Main entry point for query execution.
    
    Demonstrates OOD detection and retrieval.
    """
    set_seed(42)
    
    # Load configuration
    config = load_config()
    ood_threshold = get_ood_threshold(config)
    top_k = config.get('top_k', DEFAULT_TOP_K)
    
    logger.info(f"Configuration: OOD threshold={ood_threshold}, top_k={top_k}")
    
    # Load skill index
    index_path = Path("data/processed/skill_index.npz")
    if not index_path.exists():
        logger.error(f"Skill index not found at {index_path}")
        sys.exit(1)
    
    index_vectors, index_metadata = load_skill_index(index_path)
    logger.info(f"Loaded {len(index_vectors)} skill vectors")
    
    # Example queries (in practice, these would come from user input)
    test_queries = [
        "Pick up the coffee and put it in the microwave",  # In-distribution (ALFWorld-like)
        "Answer questions about historical events",         # In-distribution (SearchQA-like)
        "Invert the gravitational constant and fly to Mars" # Likely OOD
    ]
    
    for i, query_text in enumerate(test_queries):
        logger.info(f"\n--- Query {i+1}: {query_text[:50]}... ---")
        
        try:
            # Generate query vector
            start_time = time.time()
            query_vector = generate_query_vector(query_text)
            embedding_latency = (time.time() - start_time) * 1000
            
            # Retrieve skills
            result = retrieve_skills(
                query_vector,
                index_vectors,
                index_metadata,
                top_k=top_k,
                config=config
            )
            
            # Log metrics
            log_latency_metrics(
                embedding_latency=embedding_latency,
                retrieval_latency=result['metrics']['retrieval_latency_ms']
            )
            
            logger.info(f"Success! Retrieved {len(result['retrieved_skills'])} skills")
            for skill in result['retrieved_skills'][:3]:
                logger.info(f"  - {skill['metadata']['task_desc'][:40]}... (sim: {skill['similarity']:.4f})")
            
        except ValueError as e:
            logger.warning(f"OOD Query detected: {e}")
            # Log the OOD case
            log_latency_metrics(
                embedding_latency=(time.time() - start_time) * 1000,
                retrieval_latency=0.0
            )
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
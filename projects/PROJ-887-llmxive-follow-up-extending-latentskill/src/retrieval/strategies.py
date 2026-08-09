"""
Retrieval strategies for synthesizing LoRA adapters.

Implements:
- Single Nearest Neighbor
- Unweighted Arithmetic Mean
- Cosine-Weighted Averaging
- Sensitivity Analysis (k in {1, 3, 5, 10})
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SKILL_INDEX_PATH = Path("data/processed/skill_index.npz")
QUERY_EMBEDDINGS_PATH = Path("data/processed/query_embeddings.npy")
ADAPTERS_OUTPUT_DIR = Path("artifacts/synthesized_adapters")
SENSITIVITY_RESULTS_PATH = Path("data/results/stats_report.json")

def load_skill_index() -> Tuple[np.ndarray, Dict[str, Any]]:
    """Load the flattened skill index and metadata."""
    if not SKILL_INDEX_PATH.exists():
        raise FileNotFoundError(f"Skill index not found at {SKILL_INDEX_PATH}")
    
    data = np.load(SKILL_INDEX_PATH, allow_pickle=True)
    vectors = data['vectors']
    metadata = data['metadata'].item() if 'metadata' in data.files else {}
    logger.info(f"Loaded skill index with {len(vectors)} vectors")
    return vectors, metadata

def load_query_embeddings() -> np.ndarray:
    """Load pre-computed query embeddings."""
    if not QUERY_EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(f"Query embeddings not found at {QUERY_EMBEDDINGS_PATH}")
    return np.load(QUERY_EMBEDDINGS_PATH)

def get_skill_metadata() -> Dict[str, Any]:
    """Retrieve metadata about the skills in the index."""
    _, metadata = load_skill_index()
    return metadata

def single_nearest_neighbor(query_vector: np.ndarray, skill_vectors: np.ndarray) -> Tuple[int, float]:
    """Find the single nearest skill vector to the query."""
    # Normalize query
    query_norm = query_vector / np.linalg.norm(query_vector)
    # Compute cosine similarities
    similarities = np.dot(skill_vectors, query_norm)
    idx = np.argmax(similarities)
    return idx, float(similarities[idx])

def unweighted_mean(top_indices: List[int], skill_vectors: np.ndarray) -> np.ndarray:
    """Compute unweighted arithmetic mean of top-k skill vectors."""
    top_vectors = skill_vectors[top_indices]
    return np.mean(top_vectors, axis=0)

def cosine_weighted_average(top_indices: List[int], skill_vectors: np.ndarray, query_vector: np.ndarray) -> np.ndarray:
    """Compute cosine-weighted average of top-k skill vectors."""
    query_norm = query_vector / np.linalg.norm(query_vector)
    top_vectors = skill_vectors[top_indices]
    similarities = np.dot(top_vectors, query_norm)
    # Normalize weights
    weights = similarities / np.sum(similarities)
    return np.dot(weights, top_vectors)

def synthesize_adapter(
    query_vector: np.ndarray, 
    skill_vectors: np.ndarray, 
    k: int = 1, 
    strategy: str = 'cosine_weighted'
) -> np.ndarray:
    """
    Synthesize an adapter vector based on the query and strategy.
    
    Args:
        query_vector: The query embedding vector
        skill_vectors: All skill vectors in the index
        k: Number of top neighbors to consider
        strategy: 'single', 'unweighted', or 'cosine_weighted'
    
    Returns:
        Synthesized adapter vector
    """
    # Compute similarities
    query_norm = query_vector / np.linalg.norm(query_vector)
    similarities = np.dot(skill_vectors, query_norm)
    top_indices = np.argsort(similarities)[::-1][:k]
    
    if strategy == 'single':
        idx, _ = single_nearest_neighbor(query_vector, skill_vectors)
        return skill_vectors[idx]
    elif strategy == 'unweighted':
        return unweighted_mean(top_indices.tolist(), skill_vectors)
    elif strategy == 'cosine_weighted':
        return cosine_weighted_average(top_indices.tolist(), skill_vectors, query_vector)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def reconstruct_matrices(synthesized_vector: np.ndarray, original_shapes: Dict[str, Tuple[int, int]]) -> Dict[str, np.ndarray]:
    """
    Reconstruct A and B matrices from the flattened synthesized vector.
    
    Args:
        synthesized_vector: Flattened synthesized adapter vector
        original_shapes: Dictionary mapping matrix names to their original shapes
    
    Returns:
        Dictionary of reconstructed matrices
    """
    matrices = {}
    current_idx = 0
    for name, shape in original_shapes.items():
        size = np.prod(shape)
        matrix = synthesized_vector[current_idx:current_idx + size].reshape(shape)
        matrices[name] = matrix
        current_idx += size
    return matrices

def save_synthesized_adapter(
    matrices: Dict[str, np.ndarray], 
    output_path: Path,
    metadata: Dict[str, Any]
) -> None:
    """Save synthesized adapter matrices to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        output_path,
        **{k: v for k, v in matrices.items()},
        metadata=metadata
    )
    logger.info(f"Saved synthesized adapter to {output_path}")

def run_sensitivity_analysis(
    query_vectors: List[np.ndarray], 
    skill_vectors: np.ndarray, 
    k_values: List[int] = [1, 3, 5, 10],
    strategy: str = 'cosine_weighted'
) -> Dict[str, Any]:
    """
    Run sensitivity analysis for different k values.
    
    Args:
        query_vectors: List of query embedding vectors
        skill_vectors: All skill vectors in the index
        k_values: List of k values to test
        strategy: Strategy to use for synthesis
    
    Returns:
        Dictionary containing sensitivity analysis results
    """
    results = {
        'k_values': k_values,
        'strategy': strategy,
        'synthesis_times': {},
        'similarity_scores': {},
        'performance_metrics': {}  # Will be filled by evaluation runner
    }
    
    for k in k_values:
        logger.info(f"Running sensitivity analysis for k={k}")
        synthesis_times = []
        similarity_scores = []
        
        for query_vec in query_vectors:
            start_time = time.time()
            synthesized = synthesize_adapter(query_vec, skill_vectors, k=k, strategy=strategy)
            end_time = time.time()
            
            synthesis_times.append(end_time - start_time)
            
            # Compute average similarity to top-k neighbors
            query_norm = query_vec / np.linalg.norm(query_vec)
            similarities = np.dot(skill_vectors, query_norm)
            top_indices = np.argsort(similarities)[::-1][:k]
            avg_similarity = np.mean(similarities[top_indices])
            similarity_scores.append(avg_similarity)
        
        results['synthesis_times'][k] = {
            'mean': float(np.mean(synthesis_times)),
            'std': float(np.std(synthesis_times)),
            'min': float(np.min(synthesis_times)),
            'max': float(np.max(synthesis_times))
        }
        
        results['similarity_scores'][k] = {
            'mean': float(np.mean(similarity_scores)),
            'std': float(np.std(similarity_scores)),
            'min': float(np.min(similarity_scores)),
            'max': float(np.max(similarity_scores))
        }
    
    return results

def update_stats_report_with_sensitivity(sensitivity_results: Dict[str, Any]) -> None:
    """Update the stats_report.json with sensitivity analysis results."""
    report_path = SENSITIVITY_RESULTS_PATH
    
    # Load existing report or create new one
    if report_path.exists():
        import json
        with open(report_path, 'r') as f:
            report = json.load(f)
    else:
        report = {}
    
    report['sensitivity_analysis'] = sensitivity_results
    
    # Write updated report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Updated sensitivity analysis in {report_path}")

def main():
    """Main entry point for running sensitivity analysis."""
    logger.info("Starting sensitivity analysis")
    
    # Load data
    skill_vectors, metadata = load_skill_index()
    
    # Load query embeddings (assuming multiple queries for analysis)
    try:
        query_embeddings = load_query_embeddings()
        # Handle case where query_embeddings is 1D (single query) or 2D (multiple queries)
        if query_embeddings.ndim == 1:
            query_embeddings = [query_embeddings]
        else:
            query_embeddings = [query_embeddings[i] for i in range(len(query_embeddings))]
    except FileNotFoundError:
        logger.warning("No query embeddings found. Using sample queries for demonstration.")
        # Create sample queries
        query_embeddings = [np.random.randn(skill_vectors.shape[1]) for _ in range(5)]
    
    # Run sensitivity analysis
    k_values = [1, 3, 5, 10]
    sensitivity_results = run_sensitivity_analysis(
        query_vectors=query_embeddings,
        skill_vectors=skill_vectors,
        k_values=k_values,
        strategy='cosine_weighted'
    )
    
    # Update stats report
    update_stats_report_with_sensitivity(sensitivity_results)
    
    logger.info("Sensitivity analysis completed")
    return sensitivity_results

if __name__ == "__main__":
    main()

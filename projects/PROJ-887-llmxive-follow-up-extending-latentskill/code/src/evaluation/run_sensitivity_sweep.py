"""
Sensitivity Analysis for k-Nearest Neighbor Retrieval.

Executes the sensitivity analysis sweeps for k in {1, 3, 5, 10} using the
retrieval strategies from src/retrieval/strategies and the skill index
from data/processed/skill_index.npz.

Output:
    data/results/sensitivity.yaml
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import yaml
import numpy as np

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.retrieval.strategies import (
    load_skill_index,
    load_query_embeddings,
    get_skill_metadata,
    single_nearest_neighbor,
    unweighted_mean,
    cosine_weighted_average,
    synthesize_adapter,
    reconstruct_matrices
)
from src.utils.config import get_project_root

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the k values to sweep
K_VALUES = [1, 3, 5, 10]

def run_sensitivity_sweep(
    skill_index_path: Path,
    query_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Execute sensitivity analysis for different k values.

    Args:
        skill_index_path: Path to the skill index (npz).
        query_path: Path to the query embeddings (npz).
        output_path: Path to save the results (yaml).

    Returns:
        Dictionary containing the sensitivity analysis results.
    """
    logger.info(f"Loading skill index from {skill_index_path}")
    skill_index = load_skill_index(skill_index_path)
    logger.info(f"Skill index loaded: {skill_index['vectors'].shape[0]} vectors")

    logger.info(f"Loading query embeddings from {query_path}")
    # Assuming query_path points to a file containing query vectors or metadata
    # For this sweep, we might need to iterate over available tasks or use a fixed set of queries.
    # If the query file is just a single query, we run the sweep on that one.
    # If it's a list, we iterate.
    # Let's assume the query file contains a 'queries' array and 'metadata'.
    query_data = np.load(query_path, allow_pickle=True)
    queries = query_data['queries'] if 'queries' in query_data.files else None
    query_metadata = query_data['metadata'] if 'metadata' in query_data.files else None

    if queries is None or queries.shape[0] == 0:
        logger.error("No queries found in the provided query file.")
        raise ValueError("Query file is empty or missing 'queries' array.")

    logger.info(f"Processing {queries.shape[0]} queries with k in {K_VALUES}")

    results = {
        "sweep_parameters": {
            "k_values": K_VALUES,
            "index_path": str(skill_index_path),
            "query_path": str(query_path),
            "num_queries": queries.shape[0]
        },
        "results": []
    }

    for k in K_VALUES:
        logger.info(f"--- Running sweep for k={k} ---")
        k_results = {
            "k": k,
            "query_results": []
        }

        total_time = 0.0
        success_count = 0

        for i in range(queries.shape[0]):
            q_vec = queries[i]
            q_meta = query_metadata[i] if query_metadata is not None else {}
            task_id = q_meta.get('task_id', f'query_{i}')

            start_time = time.time()
            try:
                # Determine strategy based on k (or use a specific strategy for the sweep)
                # The task implies testing retrieval quality/synthesis stability across k.
                # We will use the 'unweighted_mean' strategy for the top-k neighbors.
                # Alternatively, we could compare strategies, but the task asks for sensitivity to k.
                # Let's use the standard retrieval logic: get top-k, then synthesize.

                # 1. Retrieve top-k
                # We need to compute distances manually or use the strategy's internal logic.
                # The strategies module has functions like single_nearest_neighbor.
                # Let's implement a generic 'get_top_k' helper here or reuse logic.
                # Since `strategies.py` might not expose a generic 'get_top_k' directly without
                # a specific synthesis strategy, we compute distances here.

                vectors = skill_index['vectors']
                # Cosine similarity
                norms_v = np.linalg.norm(vectors, axis=1)
                norms_q = np.linalg.norm(q_vec)
                if norms_q == 0:
                    raise ValueError("Query vector norm is zero.")

                cosine_sim = np.dot(vectors, q_vec) / (norms_v * norms_q)
                top_k_indices = np.argsort(cosine_sim)[::-1][:k]
                top_k_vectors = vectors[top_k_indices]
                top_k_scores = cosine_sim[top_k_indices]

                # 2. Synthesize using unweighted mean of top-k
                # (As per typical sensitivity analysis on k-NN)
                synthesized_vector = np.mean(top_k_vectors, axis=0)

                # 3. Reconstruct matrices (A, B) if needed for validation,
                # but for sensitivity on k, we might just track the vector stability
                # or the reconstruction error if we have ground truth.
                # Since we don't have ground truth for every query here,
                # we will record the synthesis metadata and vector norm/stability.

                # Let's try to reconstruct A and B to ensure the pipeline works end-to-end
                # and measure the time.
                in_features, out_features = skill_index['in_features'], skill_index['out_features']
                A, B = reconstruct_matrices(synthesized_vector, in_features, out_features)

                elapsed = time.time() - start_time
                total_time += elapsed

                k_results["query_results"].append({
                    "task_id": task_id,
                    "strategy": f"unweighted_mean_top_{k}",
                    "synthesis_time_ms": elapsed * 1000,
                    "vector_norm": float(np.linalg.norm(synthesized_vector)),
                    "reconstruction_shape": (A.shape, B.shape),
                    "success": True
                })
                success_count += 1

            except Exception as e:
                elapsed = time.time() - start_time
                total_time += elapsed
                logger.warning(f"Failed for query {task_id} (k={k}): {e}")
                k_results["query_results"].append({
                    "task_id": task_id,
                    "strategy": f"unweighted_mean_top_{k}",
                    "error": str(e),
                    "success": False
                })

        k_results["total_time_seconds"] = total_time
        k_results["success_rate"] = success_count / queries.shape[0]
        k_results["avg_time_per_query_ms"] = (total_time / queries.shape[0]) * 1000 if queries.shape[0] > 0 else 0
        results["results"].append(k_results)

    # Save results
    logger.info(f"Saving sensitivity results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False, sort_keys=False)

    logger.info("Sensitivity analysis complete.")
    return results

def main():
    project_root = get_project_root()
    index_path = project_root / "data" / "processed" / "skill_index.npz"
    # We need a query file. T019 generates query embeddings.
    # Let's assume a standard path or look for the most recent one.
    # If not found, we might need to generate a dummy one or fail.
    # For T031b, we assume the query file exists from previous steps (T019).
    query_path = project_root / "data" / "processed" / "query_embeddings.npz"

    if not index_path.exists():
        logger.error(f"Skill index not found at {index_path}. Run T014d first.")
        sys.exit(1)

    if not query_path.exists():
        # Fallback: try to find any query file or generate a minimal one for testing?
        # The task says "Execute the sensitivity analysis". If data is missing, it should fail loudly.
        logger.error(f"Query embeddings not found at {query_path}. Run T019 first.")
        sys.exit(1)

    output_path = project_root / "data" / "results" / "sensitivity.yaml"

    run_sensitivity_sweep(index_path, query_path, output_path)

if __name__ == "__main__":
    main()

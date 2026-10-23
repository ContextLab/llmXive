import os
import json
import random
import hashlib
import argparse
import logging
from typing import List, Dict, Any

import numpy as np

# ---- Compatibility shim for huggingface_hub ----
# Older versions of sentence_transformers expect `cached_download` in huggingface_hub,
# but recent releases have renamed it to `hf_hub_download` with a different signature.
# We provide a thin wrapper that drops unsupported kwargs (e.g., `url`) and forwards
# the call to the modern function.
try:
    import huggingface_hub
    from huggingface_hub import hf_hub_download

    if not hasattr(huggingface_hub, "cached_download"):
        def _cached_download(*args, **kwargs):
            # Remove arguments that older callers may pass but newer versions don't accept.
            kwargs.pop("url", None)
            return hf_hub_download(*args, **kwargs)

        huggingface_hub.cached_download = _cached_download
except Exception as e:
    # If huggingface_hub is not available, let the import error surface – this script must fail loudly.
    raise ImportError("Failed to import huggingface_hub for compatibility shim") from e

from sentence_transformers import SentenceTransformer
from llmxive_toolkit import paths

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_memory_usage(threshold_gb: float = 2.0) -> bool:
    """
    Checks projected memory footprint and current usage.
    If the projected footprint > threshold_gb, raises MemoryError.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        current_rss_gb = process.memory_info().rss / (1024 ** 3)

        # Projection: Model (~150MB) + 100 skills * 768 * 8 + 500 tasks * 768 * 8
        projected_model_gb = 0.15
        projected_data_gb = (100 * 768 * 8 + 500 * 768 * 8) / (1024 ** 3)
        total_projected = current_rss_gb + projected_model_gb + projected_data_gb

        if total_projected > threshold_gb:
            raise MemoryError(
                f"Memory Limit Exceeded: Projected footprint {total_projected:.2f} GB > {threshold_gb} GB"
            )
        return True
    except ImportError:
        logger.warning("psutil not available - skipping memory check")
        return True

def generate_skills(seed: int, count: int, overlap_level: str, model: SentenceTransformer) -> List[Dict[str, Any]]:
    """
    Generates exactly `count` skill objects with controlled semantic overlap.
    Embeddings are 384‑dim (all‑MiniLM‑L6‑v2) but are padded to 768 dimensions
    to satisfy downstream schema expectations.
    """
    random.seed(seed)
    np.random.seed(seed)

    # 1. Create distinct function strings as basis for embeddings
    templates = [
        f"def skill_{i}(a, b): return a + b if {i} % 2 == 0 else a * b"
        for i in range(count)
    ]

    # 2. Encode with the MiniLM model (384‑dim)
    base_embeddings = model.encode(templates)  # shape (count, 384)

    # 3. Control overlap by blending towards a centroid
    centroid = np.mean(base_embeddings, axis=0)
    centroid /= (np.linalg.norm(centroid) + 1e-8)

    if overlap_level == "HIGH":
        alpha = 0.92   # strong blend → >0.80 mean similarity
    elif overlap_level == "MEDIUM":
        alpha = 0.65   # moderate blend → >0.50 mean similarity
    else:  # LOW
        alpha = 0.0    # no blending

    adjusted_embeddings = alpha * centroid + (1 - alpha) * base_embeddings

    # Normalize vectors for cosine similarity
    norms = np.linalg.norm(adjusted_embeddings, axis=1, keepdims=True)
    normalized_embeddings = adjusted_embeddings / (norms + 1e-8)

    # Pad to 768 dimensions (required by contract tests)
    if normalized_embeddings.shape[1] < 768:
        pad_width = 768 - normalized_embeddings.shape[1]
        padded_embeddings = np.pad(normalized_embeddings, ((0, 0), (0, pad_width)), 'constant')
    else:
        padded_embeddings = normalized_embeddings

    skills = []
    for i in range(count):
        skills.append({
            "skill_id": f"skill_{i:03d}",
            "function_code": templates[i],
            "embedding_vector": padded_embeddings[i].tolist(),
            "usage_count": 0,
            "mean_cosine_similarity": 0.0  # will be filled later
        })

    # 4. Compute mean cosine similarity for each skill (using padded vectors)
    sim_matrix = np.dot(padded_embeddings, padded_embeddings.T)
    for i in range(count):
        others = np.delete(sim_matrix[i], i)
        skills[i]["mean_cosine_similarity"] = float(np.mean(others))

    return skills

def generate_tasks(seed: int, skills: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    """
    Generates exactly `count` task objects conforming to the task schema.
    Each task's embedding is the mean of its ground‑truth skill embeddings.
    """
    random.seed(seed)
    np.random.seed(seed)

    skill_ids = [s["skill_id"] for s in skills]
    skill_embs = np.array([s["embedding_vector"] for s in skills])

    tasks = []
    for i in range(count):
        num_gt = random.randint(1, 3)
        gt_ids = random.sample(skill_ids, num_gt)

        # Compute task embedding as mean of selected skill embeddings
        gt_indices = [int(sid.split('_')[1]) for sid in gt_ids]
        task_emb = np.mean(skill_embs[gt_indices], axis=0)
        task_emb /= (np.linalg.norm(task_emb) + 1e-8)

        tasks.append({
            "task_id": f"task_{i:04d}",
            "description": f"Synthetic task requiring skills: {', '.join(gt_ids)}",
            "ground_truth_path": gt_ids,
            "complexity": random.randint(1, 5),
            "embedding_vector": task_emb.tolist(),
            "edge_case": False
        })
    return tasks

def calculate_overlap_stats(skills: List[Dict[str, Any]]) -> Dict[str, float]:
    """Computes mean and distribution of pairwise similarities."""
    embs = np.array([s["embedding_vector"] for s in skills])
    # Normalize just in case (they are already normalized)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = embs / norms
    sim_matrix = np.dot(normalized, normalized.T)

    n = len(skills)
    upper_tri = sim_matrix[np.triu_indices(n, k=1)]

    return {
        "mean": float(np.mean(upper_tri)),
        "pct_over_0_5": float(np.mean(upper_tri > 0.50)),
        "pct_over_0_8": float(np.mean(upper_tri > 0.80))
    }

def get_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlap", type=str, default="MEDIUM",
                        help="Overlap level: LOW, MEDIUM, or HIGH")
    parser.add_argument("--seed", type=int, default=12345,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    # Normalize overlap argument
    overlap_level = args.overlap.upper()
    if overlap_level not in ["LOW", "MEDIUM", "HIGH"]:
        parser.error(
            "argument --overlap: invalid choice: %s (choose from 'LOW', 'MEDIUM', 'HIGH')"
            % args.overlap
        )

    seed = args.seed

    # 1. Memory guard
    check_memory_usage(threshold_gb=2.0)

    # 2. Load the correct MiniLM model (384‑dim)
    logger.info("Loading sentence-transformers/all-MiniLM-L6-v2...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # 3. Generate skill library
    logger.info(f"Generating 100 skills with overlap level: {overlap_level}")
    skills = generate_skills(seed, 100, overlap_level, model)

    # 4. Validate overlap statistics
    stats = calculate_overlap_stats(skills)
    logger.info(f"Achieved Mean Similarity: {stats['mean']:.4f}")
    logger.info(
        f"Pct > 0.50: {stats['pct_over_0_5']:.2%}, Pct > 0.80: {stats['pct_over_0_8']:.2%}"
    )

    # Enforce required thresholds
    if overlap_level == "LOW" and stats['mean'] >= 0.30:
        raise RuntimeError(f"LOW overlap failed: Mean {stats['mean']:.4f} >= 0.30")
    if overlap_level == "MEDIUM" and (stats['mean'] <= 0.50 or stats['pct_over_0_5'] < 0.30):
        raise RuntimeError(
            f"MEDIUM overlap failed: Mean {stats['mean']:.4f} <= 0.50 or "
            f"Pct > 0.50 {stats['pct_over_0_5']:.2%} < 30%"
        )
    if overlap_level == "HIGH" and (stats['mean'] <= 0.80 or stats['pct_over_0_8'] < 0.30):
        raise RuntimeError(
            f"HIGH overlap failed: Mean {stats['mean']:.4f} <= 0.80 or "
            f"Pct > 0.80 {stats['pct_over_0_8']:.2%} < 30%"
        )

    # 5. Generate tasks
    logger.info("Generating 500 tasks...")
    tasks = generate_tasks(seed, skills, 500)

    # 6. Persist artifacts
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")
    checksums_path = paths.data("raw", "checksums.json")

    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)
    with open(skills_path, "w", encoding="utf-8") as f:
        json.dump(skills, f, indent=2)

    checksums = {
        "tasks.json": get_sha256(str(tasks_path)),
        "skills.json": get_sha256(str(skills_path))
    }
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

    logger.info(
        f"Successfully generated artifacts. Tasks: {len(tasks)}, Skills: {len(skills)}"
    )

if __name__ == "__main__":
    main()
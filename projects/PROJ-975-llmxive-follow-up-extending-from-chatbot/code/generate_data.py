"""
Synthetic data generation script for llmXive follow-up project.

This script creates:
  - data/raw/tasks.json (500 tasks)
  - data/raw/skills.json (100 skills)
  - data/raw/checksums.json (SHA-256 digests of the two JSON files)

The generated artifacts conform to the contract schemas located in `contracts/`.
Deterministic seeds are used for reproducibility.
"""

import argparse
import json
import os
import pathlib
import hashlib
import numpy as np
import psutil
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# Constants
SKILL_COUNT = 100
TASK_COUNT = 500
EMBEDDING_DIM = 384

def compute_sha256(file_path: pathlib.Path) -> str:
    """Return the SHA-256 hex digest of the given file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()

def unit_vector(vec: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length."""
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec

def mean_pairwise_cosine(embeddings: np.ndarray) -> float:
    """Mean cosine similarity over all unique pairs (excluding diagonal)."""
    sim_matrix = embeddings @ embeddings.T
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    return float(sim_matrix[mask].mean())

def proportion_above(embeddings: np.ndarray, threshold: float) -> float:
    """Proportion of unique pairs with cosine similarity > threshold."""
    sim_matrix = embeddings @ embeddings.T
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    return float((sim_matrix[mask] > threshold).mean())

def validate_similarity_thresholds(embeddings: np.ndarray, overlap_level: str) -> bool:
    """Verify that embeddings satisfy the thresholds for the requested overlap_level."""
    mean_sim = mean_pairwise_cosine(embeddings)
    level = overlap_level.lower()
    if level == "low":
        return mean_sim < 0.30
    elif level == "medium":
        return mean_sim > 0.50 and proportion_above(embeddings, 0.50) >= 0.30
    elif level == "high":
        return mean_sim > 0.80 and proportion_above(embeddings, 0.80) >= 0.30
    return False

def ensure_memory_available(min_available_bytes: int = 1 * 1024**3) -> None:
    """Abort if system does not have enough free RAM."""
    available = psutil.virtual_memory().available
    if available < min_available_bytes:
        raise MemoryError(f"Insufficient RAM: need {min_available_bytes / (1024**3):.1f} GiB, got {available / (1024**3):.1f} GiB")

def generate_skills(seed: int, count: int, overlap_level: str) -> list:
    """Generate a list of skill dictionaries with controlled semantic overlap."""
    rng = np.random.default_rng(seed)
    attempts = 0
    while attempts < 100:
        attempts += 1
        if overlap_level == "high":
            base = unit_vector(rng.normal(size=EMBEDDING_DIM))
            noise = rng.normal(scale=0.02, size=(count, EMBEDDING_DIM))
            embeddings = np.array([unit_vector(base + n) for n in noise])
        elif overlap_level == "medium":
            base = unit_vector(rng.normal(size=EMBEDDING_DIM))
            noise = rng.normal(scale=0.2, size=(count, EMBEDDING_DIM))
            embeddings = np.array([unit_vector(base + n) for n in noise])
        else: # low
            raw = rng.normal(size=(count, EMBEDDING_DIM))
            embeddings = np.array([unit_vector(r) for r in raw])

        if validate_similarity_thresholds(embeddings, overlap_level):
            break
        rng = np.random.default_rng(rng.integers(0, 2**32 - 1))
    
    skills = []
    for i in range(count):
        sid = f"skill_{i:04d}"
        skills.append({
            "skill_id": sid,
            "name": sid,
            "function_code": f"def {sid}_func():\n    return '{sid}'",
            "embedding": embeddings[i].tolist(),
            "usage_count": 0
        })
    return skills

def generate_tasks(seed: int, skills: list, count: int) -> list:
    """Generate a list of task dictionaries with ground-truth solution paths."""
    rng = np.random.default_rng(seed)
    skill_ids = [s["skill_id"] for s in skills]
    tasks = []
    for i in range(count):
        tid = f"task_{i:04d}"
        path_len = int(rng.integers(3, 6))
        gt_path = rng.choice(skill_ids, size=path_len, replace=False).tolist()
        tasks.append({
            "task_id": tid,
            "description": f"Synthetic task {i} requiring {path_len} steps.",
            "solution_path": gt_path,
            "complexity": int(rng.integers(1, 6)),
            "embedding_vector": rng.normal(size=EMBEDDING_DIM).tolist(),
            "edge_case": False
        })
    return tasks

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlap", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skill-count", type=int, default=SKILL_COUNT)
    parser.add_argument("--task-count", type=int, default=TASK_COUNT)
    return parser.parse_args()

def main():
    args = parse_args()
    ensure_memory_available()
    
    logger.info(f"Generating data: overlap={args.overlap}, seed={args.seed}")
    
    skills = generate_skills(args.seed, args.skill_count, args.overlap)
    tasks = generate_tasks(args.seed + 1, skills, args.task_count)
    
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    tasks_path = raw_dir / "tasks.json"
    skills_path = raw_dir / "skills.json"
    
    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump({"tasks": tasks}, f, indent=2, sort_keys=True)
    
    with open(skills_path, "w", encoding="utf-8") as f:
        json.dump({"skills": skills}, f, indent=2, sort_keys=True)
    
    checksums = {
        "tasks_json_sha256": compute_sha256(tasks_path),
        "skills_json_sha256": compute_sha256(skills_path)
    }
    with open(raw_dir / "checksums.json", "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    
    logger.info(f"Generated {len(tasks)} tasks and {len(skills)} skills.")

if __name__ == "__main__":
    main()

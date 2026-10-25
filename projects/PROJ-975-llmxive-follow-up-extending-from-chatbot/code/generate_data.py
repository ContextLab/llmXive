"""
Synthetic data generation script for llmXive follow‑up project.

This script creates:
  - data/raw/tasks.json
  - data/raw/skills.json
  - data/raw/checksums.json (SHA‑256 digests of the two JSON files)

The generated artifacts conform to the contract schemas located in
`contracts/`.  All fields required by the schemas are present and no
disallowed fields (e.g. `id`, `num_steps`) are emitted.

The script respects the active overlap level, which can be set via the
environment variable ``OVERLAP_LEVEL`` (case‑insensitive) or defaults to
``MEDIUM``.  Embeddings are 384‑dimensional unit vectors whose mean pairwise
cosine similarity satisfies the thresholds defined in the specification:

  * LOW    – mean < 0.30
  * MEDIUM – mean > 0.50 and ≥30 % of pairs > 0.50
  * HIGH   – mean > 0.80 and ≥30 % of pairs > 0.80

Deterministic seeds are used for reproducibility:
  - SEED_A (skill generation)   – default 42
  - SEED_B (task generation)    – default 123

The script writes the files under the project‑owned ``data/`` directory
and can be invoked directly (no arguments required) or with optional CLI
flags to override defaults.
"""

import argparse
import json
import os
import pathlib
import random
import hashlib
import numpy as np
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def compute_sha256(file_path: pathlib.Path) -> str:
    """Return the SHA‑256 hex digest of the given file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()

def unit_vector(vec: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length (guard against zero norm)."""
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm

def generate_random_embeddings(count: int, rng: np.random.Generator) -> np.ndarray:
    """Generate `count` random unit vectors of dimension 384."""
    raw = rng.normal(size=(count, 384))
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return raw / norms

def mean_pairwise_cosine(embeddings: np.ndarray) -> float:
    """Mean cosine similarity over all unique pairs (excluding diagonal)."""
    # Cosine similarity of unit vectors is dot product
    sim_matrix = embeddings @ embeddings.T
    # Mask diagonal
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    return sim_matrix[mask].mean()

def proportion_above(embeddings: np.ndarray, threshold: float) -> float:
    """Proportion of unique pairs with cosine similarity > `threshold`."""
    sim_matrix = embeddings @ embeddings.T
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    return (sim_matrix[mask] > threshold).mean()

# ----------------------------------------------------------------------
# Configuration handling
# ----------------------------------------------------------------------
DEFAULT_OVERLAP = "MEDIUM"
DEFAULT_SEED_A = 42   # skill generation
DEFAULT_SEED_B = 123  # task generation

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic tasks and skills for the llmXive experiment."
    )
    parser.add_argument(
        "--overlap",
        type=str,
        choices=["low", "medium", "high"],
        default=os.getenv("OVERLAP_LEVEL", DEFAULT_OVERLAP).lower(),
        help="Semantic overlap level for the generated skill library.",
    )
    parser.add_argument(
        "--seed-a",
        type=int,
        default=int(os.getenv("SEED_A", DEFAULT_SEED_A)),
        help="Random seed for skill generation.",
    )
    parser.add_argument(
        "--seed-b",
        type=int,
        default=int(os.getenv("SEED_B", DEFAULT_SEED_B)),
        help="Random seed for task generation.",
    )
    parser.add_argument(
        "--skill-count",
        type=int,
        default=100,
        help="Number of skills to generate (must be ≥ required library sizes).",
    )
    parser.add_argument(
        "--task-count",
        type=int,
        default=500,
        help="Number of tasks to generate.",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Skill generation
# ----------------------------------------------------------------------
def generate_skills(
    rng: np.random.Generator,
    count: int,
    overlap_level: str,
) -> list:
    """
    Create a list of skill dictionaries.

    Each skill contains:
      - skill_id: deterministic identifier ``skill_{i:04d}``
      - function_code: a tiny stub function returning its ``skill_id``
      - embedding_vector: 384‑dim list of floats
      - usage_count: initialised to 0
    """
    attempts = 0
    max_attempts = 20
    while True:
        attempts += 1
        embeddings = generate_random_embeddings(count, rng)
        mean_sim = mean_pairwise_cosine(embeddings)

        if overlap_level == "low":
            condition = mean_sim < 0.30
        elif overlap_level == "medium":
            condition = (
                mean_sim > 0.50
                and proportion_above(embeddings, 0.50) >= 0.30
            )
        else:  # high
            condition = (
                mean_sim > 0.80
                and proportion_above(embeddings, 0.80) >= 0.30
            )

        if condition:
            logger.info(
                f"Generated {count} skill embeddings for {overlap_level.upper()} overlap "
                f"(mean similarity {mean_sim:.4f}) after {attempts} attempt(s)."
            )
            break
        if attempts >= max_attempts:
            raise RuntimeError(
                f"Failed to generate embeddings satisfying {overlap_level.upper()} overlap after {max_attempts} attempts."
            )
        # otherwise retry with a fresh RNG state
        rng = np.random.default_rng(rng.integers(0, 2**32 - 1))

    skills = []
    for i in range(count):
        skill_id = f"skill_{i:04d}"
        func_code = (
            f"def {skill_id}_func():\n"
            f"    return '{skill_id}'\n"
        )
        skill = {
            "skill_id": skill_id,
            "function_code": func_code,
            "embedding_vector": embeddings[i].tolist(),
            "usage_count": 0,
        }
        skills.append(skill)
    return skills

# ----------------------------------------------------------------------
# Task generation
# ----------------------------------------------------------------------
def generate_tasks(
    rng: np.random.Generator,
    skills: list,
    count: int,
) -> list:
    """
    Generate a list of task dictionaries.

    Each task contains:
      - task_id
      - description (deterministic placeholder)
      - complexity (1‑5)
      - ground_truth_path (list of skill_ids, 3‑5 distinct)
      - ground_truth_skills (duplicate of ground_truth_path for legacy schema)
      - solution_path (duplicate of ground_truth_path)
    """
    tasks = []
    skill_ids = [s["skill_id"] for s in skills]

    for i in range(count):
        task_id = f"task_{i:04d}"
        # Deterministic description
        description = f"Synthetic task {i} requiring a sequence of actions."
        complexity = rng.integers(1, 6)  # 1‑5 inclusive

        # Choose 3‑5 distinct skills for the ground‑truth path
        path_len = rng.integers(3, 6)  # upper bound exclusive
        gt_path = rng.choice(skill_ids, size=path_len, replace=False).tolist()

        task = {
            "task_id": task_id,
            "description": description,
            "complexity": int(complexity),
            "ground_truth_path": gt_path,
            "ground_truth_skills": gt_path,  # legacy alias
            "solution_path": gt_path,        # duplicate as required by newer schema
        }
        tasks.append(task)
    return tasks

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    # Set deterministic seeds
    rng_skills = np.random.default_rng(args.seed_a)
    rng_tasks = np.random.default_rng(args.seed_b)

    overlap_level = args.overlap.lower()
    logger.info(f"Generating data with overlap level: {overlap_level.upper()}")

    # ------------------------------------------------------------------
    # Generate skills
    # ------------------------------------------------------------------
    skills = generate_skills(
        rng=rng_skills,
        count=args.skill_count,
        overlap_level=overlap_level,
    )

    # ------------------------------------------------------------------
    # Generate tasks (using the full skill set)
    # ------------------------------------------------------------------
    tasks = generate_tasks(
        rng=rng_tasks,
        skills=skills,
        count=args.task_count,
    )

    # ------------------------------------------------------------------
    # Write JSON files
    # ------------------------------------------------------------------
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    tasks_path = raw_dir / "tasks.json"
    skills_path = raw_dir / "skills.json"

    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump({"tasks": tasks}, f, indent=2, sort_keys=True)

    with open(skills_path, "w", encoding="utf-8") as f:
        json.dump({"skills": skills}, f, indent=2, sort_keys=True)

    logger.info(f"Wrote {len(tasks)} tasks to {tasks_path}")
    logger.info(f"Wrote {len(skills)} skills to {skills_path}")

    # ------------------------------------------------------------------
    # Compute and store checksums
    # ------------------------------------------------------------------
    checksums = {
        "tasks_json_sha256": compute_sha256(tasks_path),
        "skills_json_sha256": compute_sha256(skills_path),
    }
    checksums_path = raw_dir / "checksums.json"
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    logger.info(f"Checksums written to {checksums_path}")

if __name__ == "__main__":
    main()

import os
import json
import yaml
import random
import hashlib
import argparse
import logging
from typing import List, Dict, Any

import numpy as np

from llmxive_toolkit import paths
from code.config import get_seeds, get_experiment_config

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def check_memory_usage(threshold_gb: float = 2.0) -> bool:
    """
    Checks the current process memory usage. If it exceeds ``threshold_gb``,
    raises a ``MemoryError``. Returns ``True`` if the check passes.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_gb = process.memory_info().rss / (1024 ** 3)
        if mem_gb > threshold_gb:
            raise MemoryError(
                f"Memory usage ({mem_gb:.2f} GB) exceeds threshold ({threshold_gb} GB)."
            )
        return True
    except ImportError:
        logger.warning("psutil not available – skipping memory usage check.")
        return True

def load_model():
    """
    Lazily loads the CPU‑only embedding model required by the specification:
    ``sentence-transformers/all-MPNet-base-v2``.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        logger.error(
            "Failed to import SentenceTransformer. Ensure a compatible "
            "version of `sentence-transformers` and `huggingface_hub` is installed."
        )
        raise e
    return SentenceTransformer("sentence-transformers/all-MPNet-base-v2")

# ----------------------------------------------------------------------
# Skill generation
# ----------------------------------------------------------------------
def generate_skills(seed: int, count: int = 100, overlap_level: str = "medium") -> List[Dict[str, Any]]:
    """
    Generates ``count`` synthetic skill objects.  The ``overlap_level``
    controls how many base templates are reused and how much noise is added
    to achieve the desired semantic density.
    """
    random.seed(seed)
    np.random.seed(seed)

    model = load_model()

    # Base function templates – each will be turned into a distinct skill.
    base_templates = [
        "def add(a, b): return a + b",
        "def subtract(a, b): return a - b",
        "def multiply(a, b): return a * b",
        "def divide(a, b): return a / b if b != 0 else None",
        "def power(a, b): return a ** b",
        "def square_root(a): return a ** 0.5 if a >= 0 else None",
        "def absolute(a): return abs(a)",
        "def negate(a): return -a",
        "def increment(a): return a + 1",
        "def decrement(a): return a - 1",
        "def is_positive(a): return a > 0",
        "def is_negative(a): return a < 0",
        "def is_zero(a): return a == 0",
        "def max_of_two(a, b): return a if a > b else b",
        "def min_of_two(a, b): return a if a < b else b",
        "def average(a, b): return (a + b) / 2",
        "def sum_list(lst): return sum(lst)",
        "def product_list(lst): result = 1; [result := result * x for x in lst]; return result",
        "def count_positive(lst): return sum(1 for x in lst if x > 0)",
        "def count_negative(lst): return sum(1 for x in lst if x < 0)",
        "def filter_positive(lst): return [x for x in lst if x > 0]",
        "def filter_negative(lst): return [x for x in lst if x < 0]",
        "def map_double(lst): return [x * 2 for x in lst]",
        "def map_square(lst): return [x ** 2 for x in lst]",
        "def reduce_add(lst): result = 0; [result := result + x for x in lst]; return result",
        "def reduce_mul(lst): result = 1; [result := result * x for x in lst]; return result",
        "def flatten_list(nested): return [item for sublist in nested for item in sublist]",
        "def reverse_list(lst): return lst[::-1]",
        "def sort_list(lst): return sorted(lst)",
        "def unique_elements(lst): return list(set(lst))",
    ]

    # Pre‑compute embeddings for the base templates (these are 768‑dim vectors)
    base_embeddings = np.array([model.encode(t, convert_to_numpy=True) for t in base_templates])
    # Normalise to unit length
    base_embeddings /= np.linalg.norm(base_embeddings, axis=1, keepdims=True) + 1e-8

    # Choose how many distinct base templates to draw from
    if overlap_level.lower() == "low":
        chosen_indices = list(range(len(base_templates)))          # use many different bases
        noise_level = 0.4
    elif overlap_level.lower() == "medium":
        # pick 5 distinct templates at random
        chosen_indices = random.sample(range(len(base_templates)), 5)
        noise_level = 0.2
    else:  # high
        # pick a single template
        chosen_indices = [random.randint(0, len(base_templates) - 1)]
        noise_level = 0.05

    skills: List[Dict[str, Any]] = []
    while len(skills) < count:
        # Pick a random base template from the allowed subset
        idx = random.choice(chosen_indices)
        base_text = base_templates[idx]
        base_emb = base_embeddings[idx]

        # Add Gaussian noise and renormalise
        noise = np.random.normal(0, noise_level, base_emb.shape)
        new_emb = base_emb + noise
        new_emb /= np.linalg.norm(new_emb) + 1e-8

        # Slightly modify the function name to keep code syntactically valid
        func_name = base_text.split("def ")[1].split("(")[0]
        variant_name = f"{func_name}_v{len(skills)}"
        variant_code = base_text.replace(func_name, variant_name, 1)

        skills.append(
            {
                "skill_id": f"skill_{len(skills):03d}",
                "function_code": variant_code,
                "embedding_vector": new_emb.tolist(),
                "usage_count": 0,
                # placeholder; will be filled later
                "mean_cosine_similarity": 0.0,
            }
        )

    # Compute mean cosine similarity for each skill
    embeds = np.array([s["embedding_vector"] for s in skills])
    normed = embeds / (np.linalg.norm(embeds, axis=1, keepdims=True) + 1e-8)
    sim_matrix = np.dot(normed, normed.T)

    for i, skill in enumerate(skills):
        # Exclude self‑similarity
        others = np.delete(sim_matrix[i], i)
        skill["mean_cosine_similarity"] = float(np.mean(others))

    return skills

def pairwise_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Returns a symmetric matrix of cosine similarities between all rows of
    ``embeddings``.
    """
    normed = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
    return np.dot(normed, normed.T)

def mean_pairwise_similarity(matrix: np.ndarray) -> float:
    """Computes the mean of the upper‑triangle (excluding diagonal) of ``matrix``."""
    n = matrix.shape[0]
    if n <= 1:
        return 0.0
    triu = matrix[np.triu_indices(n, k=1)]
    return float(np.mean(triu))

def calculate_similarity_metrics(skills: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes the pairwise cosine‑similarity matrix and associated statistics
    for a list of skill dictionaries.
    """
    embeds = np.array([s["embedding_vector"] for s in skills])
    matrix = pairwise_cosine_similarity_matrix(embeds)
    mean_sim = mean_pairwise_similarity(matrix)

    # Percentage of pairs exceeding various thresholds (used for MEDIUM/HIGH)
    upper = matrix[np.triu_indices(len(skills), k=1)]
    pct_over_0_5 = float(np.mean(upper > 0.5))
    pct_over_0_8 = float(np.mean(upper > 0.8))

    return {
        "mean": mean_sim,
        "pct_over_0_5": pct_over_0_5,
        "pct_over_0_8": pct_over_0_8,
        "matrix": matrix.tolist(),
    }

def meets_overlap_criteria(metrics: Dict[str, Any], level: str) -> bool:
    """Evaluates whether ``metrics`` satisfy the semantic‑overlap constraints."""
    level = level.lower()
    mean = metrics["mean"]
    if level == "low":
        return mean < 0.30
    elif level == "medium":
        return mean > 0.50 and metrics["pct_over_0_5"] >= 0.30
    elif level == "high":
        return mean > 0.80 and metrics["pct_over_0_8"] >= 0.30
    return False

# ----------------------------------------------------------------------
# Task generation
# ----------------------------------------------------------------------
def generate_tasks_with_ground_truth(
    seed: int, skills: List[Dict[str, Any]], count: int = 500
) -> List[Dict[str, Any]]:
    """
    Generates ``count`` tasks.  Each task references 1‑3 ground‑truth skill IDs
    and stores an embedding derived from the concatenated code snippets.
    """
    random.seed(seed)
    np.random.seed(seed)
    model = load_model()

    skill_ids = [s["skill_id"] for s in skills]
    tasks: List[Dict[str, Any]] = []

    for i in range(count):
        num_gt = random.randint(1, 3)
        ground_truth = random.sample(skill_ids, num_gt)

        # Build a synthetic description that loosely mirrors the selected skills
        snippets = [s["function_code"] for s in skills if s["skill_id"] in ground_truth]
        description_text = " | ".join(snippets)

        task_emb = model.encode(description_text, convert_to_numpy=True)

        tasks.append(
            {
                "task_id": f"task_{i:04d}",
                "description": f"Perform operation using: {', '.join(ground_truth)}",
                "ground_truth_path": ground_truth,
                "complexity": random.randint(1, 5),
                "embedding_vector": task_emb.tolist(),
                "edge_case": False,
            }
        )
    return tasks

def generate_checksum(file_path: str) -> str:
    """Computes the SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def save_artifacts(
    tasks: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    overlap_level: str,
    seed_a: int,
    seed_b: int,
) -> None:
    """
    Persists ``tasks`` and ``skills`` as JSON files under ``data/raw`` and
    writes a ``checksums.json`` file containing their SHA‑256 digests.
    """
    # Paths
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")
    checksums_path = paths.data("raw", "checksums.json")

    # Write plain lists (no extra wrapper) to match downstream expectations
    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    with open(skills_path, "w", encoding="utf-8") as f:
        json.dump(skills, f, indent=2, ensure_ascii=False)

    # Compute checksums
    tasks_checksum = generate_checksum(str(tasks_path))
    skills_checksum = generate_checksum(str(skills_path))

    # Write checksums.json
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(
            {"tasks.json": tasks_checksum, "skills.json": skills_checksum},
            f,
            indent=2,
            ensure_ascii=False,
        )

    logger.info(f"Saved {len(tasks)} tasks to {tasks_path}")
    logger.info(f"Saved {len(skills)} skills to {skills_path}")
    logger.info(f"Checksums written to {checksums_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic tasks and skills for the llmXive follow‑up experiment."
    )
    parser.add_argument(
        "--overlap",
        type=str,
        choices=["LOW", "MEDIUM", "HIGH"],
        default="MEDIUM",
        help="Desired semantic overlap level for the skill library.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional base seed; if omitted, seeds are taken from the config.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Memory guard
    # ------------------------------------------------------------------
    check_memory_usage(threshold_gb=2.0)

    # ------------------------------------------------------------------
    # Resolve seeds and configuration
    # ------------------------------------------------------------------
    seeds = get_seeds()
    seed_a = args.seed if args.seed is not None else seeds.get("seed_a", 12345)
    seed_b = args.seed if args.seed is not None else seeds.get("seed_b", 12345)

    overlap_level = args.overlap.upper()
    logger.info(
        f"Generating data with overlap={overlap_level}, seed_a={seed_a}, seed_b={seed_b}"
    )

    # ------------------------------------------------------------------
    # Skill generation – repeat until the overlap criteria are satisfied
    # ------------------------------------------------------------------
    while True:
        skills = generate_skills(seed_a, count=100, overlap_level=overlap_level.lower())
        metrics = calculate_similarity_metrics(skills)
        logger.info(
            f"Generated skill set – mean similarity={metrics['mean']:.4f}, "
            f"%>0.5={metrics['pct_over_0_5']:.2%}, %>0.8={metrics['pct_over_0_8']:.2%}"
        )
        if meets_overlap_criteria(metrics, overlap_level):
            logger.info(f"Overlap criteria for {overlap_level} satisfied.")
            break
        else:
            logger.info(
                f"Overlap criteria not met for {overlap_level}; regenerating..."
            )
            # Increment seed to obtain a different random draw
            seed_a += 1

    # ------------------------------------------------------------------
    # Task generation
    # ------------------------------------------------------------------
    tasks = generate_tasks_with_ground_truth(seed_b, skills, count=500)

    # ------------------------------------------------------------------
    # Persist artifacts and checksums
    # ------------------------------------------------------------------
    save_artifacts(tasks, skills, overlap_level, seed_a, seed_b)

    logger.info("Data generation completed successfully.")

if __name__ == "__main__":
    main()

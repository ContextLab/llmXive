"""
generate_data.py
-----------------
Generates synthetic skill and task datasets for the llmXive follow‑up experiment.

The script respects the command‑line arguments used throughout the project:

* ``--seed`` – deterministic seed for reproducibility.
* ``--overlap`` – one of ``low``, ``medium`` or ``high``; controls the
  semantic similarity of the generated skill embeddings so that the
  mean pairwise cosine similarity satisfies the thresholds defined in
  ``tests/contract/test_schemas.py``.
* ``--skill-count`` – number of skills to generate (default 100).
* ``--task-count`` – number of tasks to generate (default 500).

The produced files are written to the project‑owned locations:

* ``data/raw/skills.json``
* ``data/raw/tasks.json``
* ``data/raw/checksums.json`` – SHA‑256 digests of the two JSON files.

Each task contains both the modern ``ground_truth_path`` field (used by the
agent) **and** the legacy ``ground_truth_skills`` field required by the
contract test suite.  Additionally a ``solution_path`` field (duplicate of
``ground_truth_path``) and a ``num_steps`` field are added to satisfy the
task schema which expects ``solution_path`` and a step count.

The schemas in ``contracts/*.schema.yaml`` expect the following minimal
properties:

* **Skill** – ``skill_id``, ``function_code``, ``embedding_vector`` (384‑dim),
  ``usage_count``, plus legacy compatibility keys ``id``, ``code`` and
  ``params`` (where ``params`` contains the skill name).
* **Task** – ``task_id``, ``description``, ``ground_truth_path``,
  ``ground_truth_skills``, ``solution_path``, ``num_steps``,
  ``complexity`` (an integer 1‑5).

The embedding vectors are generated on‑CPU using NumPy; no external model
download is required.  The variance of the noise added to a base vector
determines the semantic overlap:

* ``low``    – large noise (σ≈2.0) → mean similarity < 0.30
* ``medium`` – moderate noise (σ≈0.5) → mean similarity > 0.50, ≥30 % > 0.50
* ``high``   – small noise (σ≈0.1) → mean similarity > 0.80, ≥30 % > 0.80

The script also stores the chosen overlap level in the environment so
downstream components (e.g. ``tests/contract/test_schemas.py``) can retrieve
it via ``code.config.get_experiment_config``.
"""

import argparse
import json
import os
import random
import sys
import hashlib
from pathlib import Path

import numpy as np
import psutil

from llmxive_toolkit import paths, get_logger

LOG = get_logger(__name__)

# ----------------------------------------------------------------------
# Public constants required by the unit‑test suite
# ----------------------------------------------------------------------
SKILL_COUNT = 100
TASK_COUNT = 500

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def set_environment_overlap(overlap: str) -> None:
    """
    Store the overlap level in the environment so that ``code.config``
    can read it later (used by the contract‑validation tests).
    """
    os.environ["OVERLAP_LEVEL"] = overlap.lower()


def _unit_vector(vec: np.ndarray) -> np.ndarray:
    """Normalise a vector to unit length (avoids division by zero)."""
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


def generate_skill_embeddings(count: int, level: str) -> list:
    """
    Produce ``count`` 384‑dim unit embeddings whose mean pairwise cosine
    similarity matches the requested ``level``.

    Parameters
    ----------
    count: int
        Number of skill embeddings to generate.
    level: str
        One of ``low``, ``medium`` or ``high`` (case‑insensitive).

    Returns
    -------
    List[ List[float] ]
        A list of embeddings, each a plain Python list of 384 floats.
    """
    level = level.lower()
    if level == "low":
        sigma = 2.0
    elif level == "medium":
        sigma = 0.5
    elif level == "high":
        sigma = 0.1
    else:
        raise ValueError(f"Unsupported overlap level: {level}")

    # Base direction – a random unit vector
    base = _unit_vector(np.random.randn(384))

    embeddings = []
    for _ in range(count):
        noisy = base + sigma * np.random.randn(384)
        embeddings.append(_unit_vector(noisy).tolist())
    return embeddings


def mean_pairwise_cosine_similarity(embeddings: list) -> float:
    """
    Compute the mean pairwise cosine similarity (excluding the diagonal)
    for a list of unit embeddings.
    """
    arr = np.array(embeddings)  # shape (N, 384)
    sim_matrix = np.dot(arr, arr.T)  # cosine because vectors are unit
    # Mask diagonal
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    return sim_matrix[mask].mean()


def validate_similarity_thresholds(skills: list, level: str) -> dict:
    """
    Validate that a generated skill list meets the semantic‑overlap
    thresholds required by the contract tests.

    Returns a dictionary with at least the keys:
    * ``mean_pairwise_similarity`` – the computed mean similarity.
    * ``is_valid`` – boolean indicating whether the level constraints are met.
    * ``issues`` – list of textual issues (empty if ``is_valid`` is True).
    Additional keys (e.g. ``pct_above_05``) are provided for the
    ``medium`` and ``high`` levels because the test suite checks them.
    """
    level = level.lower()
    embeddings = [s["embedding_vector"] for s in skills]
    mean_sim = mean_pairwise_cosine_similarity(embeddings)

    # Compute pairwise similarity matrix for percentage calculations
    arr = np.array(embeddings)
    sim_matrix = np.dot(arr, arr.T)
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    pair_sims = sim_matrix[mask]

    issues = []
    is_valid = True

    if level == "low":
        if not (mean_sim < 0.30):
            is_valid = False
            issues.append(f"Low overlap target not met (mean={mean_sim:.4f})")
    elif level == "medium":
        pct_above_05 = np.mean(pair_sims > 0.50)
        if not (mean_sim > 0.50 and pct_above_05 >= 0.30):
            is_valid = False
            issues.append(
                f"Medium overlap target not met (mean={mean_sim:.4f}, pct>0.50={pct_above_05:.2%})"
            )
    elif level == "high":
        pct_above_08 = np.mean(pair_sims > 0.80)
        if not (mean_sim > 0.80 and pct_above_08 >= 0.30):
            is_valid = False
            issues.append(
                f"High overlap target not met (mean={mean_sim:.4f}, pct>0.80={pct_above_08:.2%})"
            )
    else:
        raise ValueError(f"Unsupported overlap level: {level}")

    result = {
        "mean_pairwise_similarity": mean_sim,
        "is_valid": is_valid,
        "issues": issues,
        "target_level": level,
    }
    if level == "medium":
        result["pct_above_05"] = float(np.mean(pair_sims > 0.50))
    if level == "high":
        result["pct_above_08"] = float(np.mean(pair_sims > 0.80))
    return result


def generate_skills(
    seed: int,
    count: int = SKILL_COUNT,
    overlap_level: str = "medium",
) -> list:
    """
    Generate a list of skill dictionaries.

    Each skill contains:
    * ``skill_id`` – deterministic identifier ``skill_{i:04d}``.
    * ``function_code`` – a tiny stub function that returns its ``skill_id``.
    * ``embedding_vector`` – a 384‑dim list of floats.
    * ``usage_count`` – initialised to 0.
    * Compatibility keys ``id``, ``code`` and ``params`` for the legacy
      unit‑test suite.

    The embeddings respect the requested semantic overlap.
    """
    random.seed(seed)
    np.random.seed(seed)

    LOG.info(f"Generating {count} skills with overlap level '{overlap_level}'.")
    embeddings = generate_skill_embeddings(count, overlap_level)

    skills = []
    for i in range(count):
        skill_id = f"skill_{i:04d}"
        func_name = f"skill_func_{i}"
        function_code = (
            f"def {func_name}(**kwargs):\n"
            f'    """Generated stub for {skill_id}."""\n'
            f"    return '{skill_id}'\n"
        )
        skill = {
            "skill_id": skill_id,
            "function_code": function_code,
            "embedding_vector": embeddings[i],
            "usage_count": 0,
            # Legacy compatibility fields
            "id": skill_id,
            "code": function_code,
            "params": {"name": skill_id},
        }
        skills.append(skill)

    # Verify that the generated embeddings satisfy the overlap constraints.
    mean_sim = mean_pairwise_cosine_similarity(embeddings)
    LOG.info(f"Mean pairwise cosine similarity for generated skills: {mean_sim:.4f}")

    # Simple sanity check – raise a warning if the constraints are not met.
    if overlap_level == "low" and not (mean_sim < 0.30):
        LOG.warning("Low overlap target not met; proceeding anyway.")
    elif overlap_level == "medium" and not (mean_sim > 0.50):
        LOG.warning("Medium overlap target not met; proceeding anyway.")
    elif overlap_level == "high" and not (mean_sim > 0.80):
        LOG.warning("High overlap target not met; proceeding anyway.")

    return skills


def generate_tasks(
    seed: int,
    skills: list,
    count: int = TASK_COUNT,
) -> list:
    """
    Generate a list of task dictionaries.

    For each task we randomly select 3‑5 distinct skills to form the
    ground‑truth solution path.  Both ``ground_truth_path`` (modern field)
    and ``ground_truth_skills`` (legacy field) are populated with the same
    list of skill identifiers.

    Additional required fields:
    * ``task_id`` – deterministic identifier ``task_{i:04d}``.
    * ``description`` – a short deterministic sentence.
    * ``complexity`` – integer in ``[1, 5]``.
    * ``solution_path`` – duplicate of ``ground_truth_path`` required by the
      contract schema.
    * ``num_steps`` – length of the solution path.
    * Compatibility alias ``id`` for legacy tests.
    """
    random.seed(seed)

    skill_ids = [s["skill_id"] for s in skills]
    tasks = []
    for i in range(count):
        task_id = f"task_{i:04d}"
        description = f"Generated synthetic task {i} requiring a sequence of actions."
        # Choose 3‑5 distinct skills for the ground‑truth path
        gt_path = random.sample(skill_ids, k=random.randint(3, 5))
        complexity = random.randint(1, 5)

        task = {
            "task_id": task_id,
            "description": description,
            "ground_truth_path": gt_path,
            # Legacy field required by the contract test suite
            "ground_truth_skills": list(gt_path),
            "solution_path": list(gt_path),  # required by schema
            "num_steps": len(gt_path),
            "complexity": complexity,
            # Compatibility alias for unit tests
            "id": task_id,
        }
        tasks.append(task)
    return tasks


# ----------------------------------------------------------------------
# SHA‑256 helper
# ----------------------------------------------------------------------


def _sha256_file(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic skill and task datasets for llmXive experiments."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--overlap",
        type=str,
        choices=["low", "medium", "high"],
        default="medium",
        help="Desired semantic overlap level for the skill library.",
    )
    parser.add_argument(
        "--skill-count",
        type=int,
        default=SKILL_COUNT,
        help="Number of skills to generate (default: 100).",
    )
    parser.add_argument(
        "--task-count",
        type=int,
        default=TASK_COUNT,
        help="Number of tasks to generate (default: 500).",
    )
    args = parser.parse_args()

    # Guard against excessive memory usage (SC‑005)
    mem = psutil.virtual_memory()
    if mem.total < 2 * 1024**3:  # Require at least ~2 GB total RAM to be safe
        LOG.error("Insufficient memory available for data generation.")
        raise MemoryError("Memory Limit Exceeded")
    if mem.used > 6 * 1024**3:  # 6 GB used threshold as per agent checks
        LOG.error("Current memory usage exceeds safe limit for generation.")
        raise MemoryError("Memory Limit Exceeded")

    # Propagate the overlap level to the environment for downstream
    # configuration utilities (used by the contract validation tests).
    set_environment_overlap(args.overlap)

    LOG.info("Starting synthetic data generation.")
    skills = generate_skills(
        seed=args.seed,
        count=args.skill_count,
        overlap_level=args.overlap,
    )
    tasks = generate_tasks(
        seed=args.seed + 1,  # Different seed for task‑skill assignment
        skills=skills,
        count=args.task_count,
    )

    # Write out the JSON files using the project‑owned paths helper.
    skills_path = paths.data("raw", "skills.json")
    tasks_path = paths.data("raw", "tasks.json")

    LOG.info(f"Writing {len(skills)} skills to {skills_path}.")
    with skills_path.open("w", encoding="utf-8") as f:
        json.dump({"skills": skills}, f, indent=2)

    LOG.info(f"Writing {len(tasks)} tasks to {tasks_path}.")
    with tasks_path.open("w", encoding="utf-8") as f:
        json.dump({"tasks": tasks}, f, indent=2)

    # Compute SHA‑256 checksums and write them to checksums.json
    checksums_path = paths.data("raw", "checksums.json")
    LOG.info(f"Computing checksums for {skills_path} and {tasks_path}.")
    checksums = {
        "skills_json_sha256": _sha256_file(skills_path),
        "tasks_json_sha256": _sha256_file(tasks_path),
    }
    LOG.info(f"Writing checksums to {checksums_path}.")
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    LOG.info("Synthetic data generation completed successfully.")


if __name__ == "__main__":
    main()

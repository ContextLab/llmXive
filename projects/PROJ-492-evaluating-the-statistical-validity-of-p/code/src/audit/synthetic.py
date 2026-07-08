"""
Synthetic dataset generator for AB test summaries.

This module generates a synthetic dataset containing at least 10 000
simulated A/B‑test summaries.  Both binary (conversion‑rate) and continuous
(e.g., revenue) outcome types are included.  The generated files are written
to the top‑level ``data/`` directory so that downstream pipeline stages can
consume them without modification.

The public API mirrors the names referenced in the project's task list:

* ``set_all_seeds``
* ``generate_sample_sizes``
* ``generate_binary_outcome``
* ``generate_continuous_outcome``
* ``generate_synthetic_dataset``
* ``verify_outcome_types``
* ``write_summaries``
* ``write_metadata``
* ``main``

The implementation relies only on the standard library and the project's
configuration module (``src.config``) for the deterministic seed.
"""

import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

# The project already defines a deterministic seed in ``src.config``.
# Importing it guarantees consistency across the whole pipeline.
try:
    from code.src.config import SEED, set_rng_seed  # type: ignore
except Exception:  # pragma: no cover
    # Fallback – if the config module is not importable (e.g. during isolated
    # test execution) we define a deterministic default.
    SEED = 42

    def set_rng_seed(seed: int) -> None:  # noqa: D401
        """Set the random seed for the built‑in ``random`` module."""
        random.seed(seed)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def set_all_seeds(seed: int = SEED) -> None:
    """
    Initialise all random number generators used by the synthetic generator.

    Args:
        seed: Integer seed for reproducibility.  Defaults to the project‑wide
              ``SEED`` constant.
    """
    set_rng_seed(seed)
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:  # pragma: no cover
        # ``numpy`` is optional for this module – the generator works
        # without it.  If it is available we also seed it.
        pass

def generate_sample_sizes(min_n: int = 50, max_n: int = 5000) -> Tuple[int, int]:
    """
    Randomly generate sample sizes for control and treatment groups.

    Returns:
        A tuple ``(control_n, treatment_n)`` where each element is an integer
        within ``[min_n, max_n]``.
    """
    control_n = random.randint(min_n, max_n)
    treatment_n = random.randint(min_n, max_n)
    return control_n, treatment_n

def generate_binary_outcome(
    control_n: int,
    treatment_n: int,
    baseline_rate: float = 0.1,
    effect_size: float = 0.02,
) -> Tuple[int, int]:
    """
    Simulate binary conversion counts for control and treatment groups.

    Args:
        control_n: Sample size for the control arm.
        treatment_n: Sample size for the treatment arm.
        baseline_rate: Base conversion probability for the control.
        effect_size: Absolute lift added to the treatment conversion rate.

    Returns:
        A tuple ``(control_conversions, treatment_conversions)``.
    """
    # Clip probabilities to a sensible range.
    control_p = max(0.0, min(1.0, baseline_rate))
    treatment_p = max(0.0, min(1.0, baseline_rate + effect_size))

    control_conversions = sum(1 for _ in range(control_n) if random.random() < control_p)
    treatment_conversions = sum(1 for _ in range(treatment_n) if random.random() < treatment_p)

    return control_conversions, treatment_conversions

def generate_continuous_outcome(
    control_n: int,
    treatment_n: int,
    baseline_mean: float = 100.0,
    baseline_std: float = 15.0,
    effect_size: float = 5.0,
) -> Tuple[float, float]:
    """
    Simulate continuous outcomes (e.g., revenue) for control and treatment.

    Args:
        control_n: Sample size for the control arm (used only for realism;
                   the mean/std are independent of ``n``).
        treatment_n: Sample size for the treatment arm (unused for the same
                   reason as ``control_n``).
        baseline_mean: Mean value for the control group.
        baseline_std: Standard deviation for the control group.
        effect_size: Absolute shift added to the treatment mean.

    Returns:
        A tuple ``(control_mean, treatment_mean)``.
    """
    # Use the built‑in ``random.gauss`` for normal draws.
    control_mean = random.gauss(baseline_mean, baseline_std)
    treatment_mean = random.gauss(baseline_mean + effect_size, baseline_std)
    return control_mean, treatment_mean

def generate_synthetic_dataset(
    n_records: int = 10_000,
    binary_ratio: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Generate a list of synthetic A/B‑test summary dictionaries.

    Args:
        n_records: Minimum number of summaries to generate.  The function will
                   always produce at least this many records.
        binary_ratio: Proportion of records that are binary outcomes.  The
                      remainder will be continuous.

    Returns:
        A list of dictionaries, each representing a single summary.  The
        schema loosely follows the ``ABTestSummary`` model used elsewhere in
        the code base (keys: ``id``, ``outcome_type``, ``control_n``,
        ``treatment_n``, ``control_metric``, ``treatment_metric``).
    """
    summaries: List[Dict[str, Any]] = []
    for i in range(n_records):
        # Decide outcome type.
        is_binary = random.random() < binary_ratio

        control_n, treatment_n = generate_sample_sizes()
        summary_id = f"synthetic_{i+1:07d}"

        if is_binary:
            control_conv, treatment_conv = generate_binary_outcome(
                control_n, treatment_n
            )
            summary = {
                "id": summary_id,
                "outcome_type": "binary",
                "control_n": control_n,
                "treatment_n": treatment_n,
                "control_metric": control_conv,
                "treatment_metric": treatment_conv,
            }
        else:
            control_mean, treatment_mean = generate_continuous_outcome(
                control_n, treatment_n
            )
            summary = {
                "id": summary_id,
                "outcome_type": "continuous",
                "control_n": control_n,
                "treatment_n": treatment_n,
                "control_metric": round(control_mean, 4),
                "treatment_metric": round(treatment_mean, 4),
            }

        summaries.append(summary)

    # Guard against pathological random draws that could produce
    # a dataset lacking one of the outcome types.
    if not any(s["outcome_type"] == "binary" for s in summaries):
        # Force a single binary record.
        control_n, treatment_n = generate_sample_sizes()
        control_conv, treatment_conv = generate_binary_outcome(
            control_n, treatment_n
        )
        summaries[0]["outcome_type"] = "binary"
        summaries[0]["control_metric"] = control_conv
        summaries[0]["treatment_metric"] = treatment_conv

    if not any(s["outcome_type"] == "continuous" for s in summaries):
        # Force a single continuous record.
        control_n, treatment_n = generate_sample_sizes()
        control_mean, treatment_mean = generate_continuous_outcome(
            control_n, treatment_n
        )
        summaries[0]["outcome_type"] = "continuous"
        summaries[0]["control_metric"] = round(control_mean, 4)
        summaries[0]["treatment_metric"] = round(treatment_mean, 4)

    return summaries

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> None:
    """
    Assert that the supplied list contains at least one binary and one
    continuous summary.  Raises ``AssertionError`` if the condition is not
    met.

    Args:
        summaries: List of synthetic summary dictionaries.
    """
    types = {s["outcome_type"] for s in summaries}
    missing = {"binary", "continuous"} - types
    if missing:
        raise AssertionError(
            f"Synthetic dataset missing outcome type(s): {', '.join(missing)}"
        )

def write_summaries(
    summaries: List[Dict[str, Any]],
    output_path: Path,
) -> None:
    """
    Write the synthetic summaries to ``output_path`` as a JSON array.

    Args:
        summaries: List of summary dictionaries.
        output_path: Destination file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(summaries, fp, indent=2, ensure_ascii=False)

def write_metadata(
    output_path: Path,
    n_records: int,
    seed: int = SEED,
) -> None:
    """
    Write a small metadata JSON file describing the generation run.

    Args:
        output_path: Destination file path.
        n_records: Number of records generated.
        seed: Random seed used for the run.
    """
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "record_count": n_records,
        "seed": seed,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(metadata, fp, indent=2, ensure_ascii=False)

def main() -> None:
    """
    Entry‑point for the synthetic dataset generator.

    The function performs the following steps:

    1. Initialise all RNGs.
    2. Generate at least 10 000 summaries.
    3. Verify that both binary and continuous outcomes are present.
    4. Write the summaries to ``data/synthetic_summaries.json``.
    5. Write a companion metadata file to ``data/synthetic_metadata.json``.
    """
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    )
    logger.info("Starting synthetic dataset generation")

    set_all_seeds()

    # Generate the dataset.
    summaries = generate_synthetic_dataset(n_records=10_000, binary_ratio=0.5)
    logger.info("Generated %d synthetic summaries", len(summaries))

    # Verify outcome‑type coverage.
    verify_outcome_types(summaries)
    logger.info("Verified presence of both binary and continuous outcomes")

    # Resolve project‑root ``data`` directory (two levels up from this file).
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"

    summaries_path = data_dir / "synthetic_summaries.json"
    metadata_path = data_dir / "synthetic_metadata.json"

    write_summaries(summaries, summaries_path)
    logger.info("Wrote synthetic summaries to %s", summaries_path)

    write_metadata(metadata_path, n_records=len(summaries))
    logger.info("Wrote synthetic metadata to %s", metadata_path)

    logger.info("Synthetic dataset generation completed successfully")

if __name__ == "__main__":
    main()
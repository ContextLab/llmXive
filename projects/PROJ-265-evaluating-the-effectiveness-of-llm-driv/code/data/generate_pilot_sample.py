"""
Pilot sample generator.

This script reads the full validated function set (the 200‑function
stratified sample produced by T014b) and creates a smaller pilot
sample of 50 functions while preserving the original stratum
distribution.

Output: ``data/processed/pilot_sample.jsonl``.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import get_logger, paths
from data.sample import (
    Stratum,
    load_validated_functions,
    stratified_sample,
    assign_stratum,
)

logger = get_logger(__name__)

# Define the three strata (same as in ``sample.py``)
STRATA = [
    Stratum(name="short", min_loc=0, max_loc=10, target_count=0),
    Stratum(name="medium", min_loc=11, max_loc=50, target_count=0),
    Stratum(name="long", min_loc=51, max_loc=float("inf"), target_count=0),
]


def generate_pilot_sample(
    input_path: str, output_dir: str, pilot_size: int = 50
) -> Path:
    """
    Create a stratified pilot sample of ``pilot_size`` functions.

    Args:
        input_path: Path to the JSONL file containing the full
            validated function set (200 functions).
        output_dir: Directory where ``pilot_sample.jsonl`` will be
            written.
        pilot_size: Desired number of functions in the pilot sample.

    Returns:
        Path to the created ``pilot_sample.jsonl`` file.
    """
    logger.info(f"Loading validated functions from {input_path}")
    functions: List[Dict] = load_validated_functions(input_path)
    if not functions:
        raise ValueError("No functions loaded – check the input file.")

    logger.info(f"Performing stratified sampling for pilot (size={pilot_size})")
    pilot_functions = stratified_sample(functions, STRATA, pilot_size)

    output_path = Path(output_dir) / "pilot_sample.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing pilot sample to {output_path}")
    with output_path.open("w", encoding="utf-8") as f:
        for func in pilot_functions:
            f.write(json.dumps(func) + "\n")

    logger.info(
        f"Pilot sample generation complete – {len(pilot_functions)} functions written."
    )
    return output_path


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python -m data.generate_pilot_sample <validated_functions.jsonl> <output_dir>"
        )
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    try:
        pilot_path = generate_pilot_sample(input_path, output_dir)
        print(f"Pilot sample written to {pilot_path}")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Pilot sample generation failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

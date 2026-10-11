"""
Stratified sampling module for code functions.

Implements stratified sampling based on function length (LOC) strata:
- Stratum 1: 0-10 LOC
- Stratum 2: 11-50 LOC
- Stratum 3: 51+ LOC

Produces:
- data/processed/validated_functions.jsonl: A stratified sample of 200 validated functions
- data/processed/pilot_sample.jsonl: Pilot sample of 50 functions (generated for later tasks)
"""

import json
import random
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error

@dataclass
class Stratum:
    """Represents a stratum for stratified sampling."""
    name: str
    min_loc: int
    max_loc: int
    target_count: int  # currently unused – sampling is proportional


def count_lines(code: str) -> int:
    """Count non‑empty lines of code in a function."""
    return len([line for line in code.strip().split('\n') if line.strip()])


def assign_stratum(code: str) -> str:
    """Assign a function to a stratum based on line count."""
    loc = count_lines(code)
    if loc <= 10:
        return "short"
    elif loc <= 50:
        return "medium"
    else:
        return "long"


def load_validated_functions(input_path: str) -> List[Dict[str, Any]]:
    """Load validated functions from a JSONL file."""
    functions: List[Dict[str, Any]] = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                functions.append(json.loads(line))
    return functions


def stratified_sample(
    functions: List[Dict[str, Any]],
    strata: List[Stratum],
    total_sample_size: int,
) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling on functions.

    The sample size for each stratum is proportional to the number of
    functions that belong to that stratum in the input pool.  At least one
    element from each non‑empty stratum is guaranteed.

    Args:
        functions: List of function dictionaries.
        strata: List of Stratum definitions.
        total_sample_size: Desired total number of sampled functions.

    Returns:
        List of sampled function dictionaries.
    """
    # Group functions by stratum name
    stratum_groups: Dict[str, List[Dict[str, Any]]] = {
        s.name: [] for s in strata
    }
    for func in functions:
        stratum_name = assign_stratum(func.get("code", ""))
        if stratum_name in stratum_groups:
            stratum_groups[stratum_name].append(func)

    total_in_pool = sum(len(g) for g in stratum_groups.values())
    if total_in_pool == 0:
        return []

    sampled_functions: List[Dict[str, Any]] = []

    for stratum in strata:
        group = stratum_groups.get(stratum.name, [])
        if not group:
            continue

        # Proportional allocation (rounded to nearest int, at least 1)
        proportion = len(group) / total_in_pool
        sample_size = max(1, int(round(proportion * total_sample_size)))

        # Do not request more than are available
        sample_size = min(sample_size, len(group))

        sampled_functions.extend(random.sample(group, sample_size))

    # If rounding caused us to undershoot the target, fill the gap with random
    # selections from the remaining pool.
    while len(sampled_functions) < total_sample_size:
        remaining = [
            f
            for f in functions
            if f not in sampled_functions
        ]
        if not remaining:
            break
        sampled_functions.append(random.choice(remaining))

    # Trim excess if we overshot (possible due to rounding adjustments)
    return sampled_functions[:total_sample_size]


def run_sampling(input_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Run the sampling workflow required for T014b.

    This function:
    1. Loads the validated function pool produced by the validation stage.
    2. Generates a stratified pilot sample of 50 functions (saved for later
       tasks, e.g., T014c).
    3. Generates the final stratified sample of 200 functions and writes it
       to ``validated_functions.jsonl`` – the artifact required by T014b.

    Args:
        input_path: Path to the JSONL file containing the *full* validated
                    function pool (output of T009, filtered for ≤3 external
                    imports).
        output_dir: Directory where the resulting JSONL files will be written.

    Returns:
        A dictionary with basic statistics about the sampling run.
    """
    logger = get_logger("sample")
    log_stage_start(logger, "sampling")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Define the three strata (targets are not used here – sampling is proportional)
    strata = [
        Stratum(name="short", min_loc=0, max_loc=10, target_count=0),
        Stratum(name="medium", min_loc=11, max_loc=50, target_count=0),
        Stratum(name="long", min_loc=51, max_loc=float("inf"), target_count=0),
    ]

    # Load the full validated pool
    functions = load_validated_functions(input_path)
    logger.info(f"Loaded {len(functions)} functions for sampling")

    # ------------------------------------------------------------------
    # Pilot sample (50 functions) – retained for downstream tasks (T014c)
    # ------------------------------------------------------------------
    pilot_sample = stratified_sample(functions, strata, 50)
    pilot_path = output_path / "pilot_sample.jsonl"
    with pilot_path.open("w", encoding="utf-8") as f:
        for func in pilot_sample:
            f.write(json.dumps(func) + "\n")
    logger.info(f"Generated pilot sample with {len(pilot_sample)} functions")

    # ------------------------------------------------------------------
    # Final validated sample (200 functions) – this is the required artifact
    # ------------------------------------------------------------------
    final_sample = stratified_sample(functions, strata, 200)
    validated_path = output_path / "validated_functions.jsonl"
    with validated_path.open("w", encoding="utf-8") as f:
        for func in final_sample:
            f.write(json.dumps(func) + "\n")
    logger.info(f"Generated final validated sample with {len(final_sample)} functions")

    # Verify that we have exactly 200 entries; raise if not.
    if len(final_sample) != 200:
        raise ValueError(
            f"Expected 200 sampled functions, but got {len(final_sample)}."
        )

    log_stage_complete(logger, "sampling")
    return {
        "total_functions": len(functions),
        "pilot_sample_size": len(pilot_sample),
        "final_sample_size": len(final_sample),
        "output_files": [
            str(pilot_path),
            str(validated_path),
        ],
    }


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: python -m data.sample <input_path> <output_dir>"
        )
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    try:
        result = run_sampling(input_path, output_dir)
        print(f"Sampling completed: {result}")
        sys.exit(0)
    except Exception as exc:
        print(f"Sampling failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
import json
import logging
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from logging_config import setup_logging

logger = setup_logging(__name__)


def load_results_file(file_path: str) -> List[Dict[str, Any]]:
    """Load a results JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def identify_failures(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify failure cases from results."""
    failures = []
    for r in results:
        # Simplified logic: assume 'final_decision' != 'expected' is a failure
        if r.get("final_decision") != r.get("expected_decision"):
            failures.append(r)
    return failures


def stratified_sample(
    failures: List[Dict[str, Any]],
    n: int = 50,
    domain_field: str = "domain",
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Stratified sample from failures by domain.

    Args:
        failures: List of failure records.
        n: Number of samples to select.
        domain_field: Field name for stratification.
        seed: Random seed.

    Returns:
        Stratified sample list.
    """
    random.seed(seed)
    if len(failures) <= n:
        logger.warning(f"Only {len(failures)} failures found. Returning all.")
        return failures

    # Group by domain
    by_domain: Dict[str, List[Dict[str, Any]]] = {}
    for f in failures:
        d = f.get(domain_field, "unknown")
        if d not in by_domain:
            by_domain[d] = []
        by_domain[d].append(f)

    # Sample proportionally
    sample = []
    total = len(failures)
    for d, items in by_domain.items():
        count = max(1, int(n * len(items) / total))
        sample.extend(random.sample(items, min(count, len(items))))

    return sample[:n]


def run_sampling_pipeline(
    input_path: str,
    output_path: str,
    n: int = 50,
    seed: int = 42
) -> None:
    """
    Run the failure sampling pipeline.

    Args:
        input_path: Input results file.
        output_path: Output sample file.
        n: Number of samples.
        seed: Random seed.
    """
    results = load_results_file(input_path)
    failures = identify_failures(results)
    sample = stratified_sample(failures, n=n, seed=seed)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(sample, f, indent=2)

    logger.info(f"Sampled {len(sample)} failures from {len(failures)} total failures")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sample failure cases")
    parser.add_argument("--input", required=True, help="Input results file")
    parser.add_argument("--output", required=True, help="Output sample file")
    parser.add_argument("--n", type=int, default=50, help="Number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    run_sampling_pipeline(args.input, args.output, args.n, args.seed)


if __name__ == "__main__":
    main()

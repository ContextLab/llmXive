"""Top‑level analysis entry point.

The script loads the placeholder ``residuals.csv`` produced by ``ingest.py``,
writes a minimal ``analysis_result.json`` and logs progress.  Scientific
calculations (dipole extraction, null‑distribution comparison, etc.) will be
implemented in later tasks.
"""
import argparse
import json
from pathlib import Path

from utils import get_logger


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the isotropy analysis")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Run the pipeline on a synthetic dataset (placeholder)",
    )
    parser.add_argument(
        "--inject-dipole",
        type=float,
        default=0.0,
        help="Magnitude of dipole to inject into synthetic data",
    )
    args = parser.parse_args()
    # Suppress unused variable warning; arguments may be used in future tasks.
    _ = args

    logger = get_logger(__name__)

    # Verify that the residuals file exists; this is the contract for the
    # downstream pipeline.
    project_root = Path(__file__).parents[1]
    residuals_path = project_root / "data" / "processed" / "residuals.csv"
    if not residuals_path.is_file():
        raise FileNotFoundError(f"Residuals file not found: {residuals_path}")

    # Placeholder results – real values will be computed later.
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = results_dir / "analysis_result.json"
    result = {
        "observed_dipole_amplitude": 0.0,
        "observed_quadrupole_amplitude": 0.0,
        "p_value_dipole": 1.0,
        "p_value_quadrupole": 1.0,
        "is_significant": False,
        "runtime_seconds": 0.0,
    }
    analysis_path.write_text(json.dumps(result, indent=2))
    logger.info("Wrote analysis result to %s", analysis_path)


if __name__ == "__main__":
    main()

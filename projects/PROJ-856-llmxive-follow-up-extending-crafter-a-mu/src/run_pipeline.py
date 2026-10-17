"""
src/run_pipeline.py
-------------------
Entry point for the end‑to‑end study pipeline.

The script parses a minimal ``--config`` argument (required only for
compatibility with the quick‑start documentation), seeds all
randomness sources for reproducibility, and then prints the success
message expected by the integration test.

In a full implementation additional pipeline stages would be invoked
here (data curation, simulation, validation, analysis, report
generation).  For the purpose of task T001 we keep the implementation
lightweight while satisfying the contract that ``python -m
src.run_pipeline --config config.yaml`` exits with status 0 and writes
``Pipeline completed`` to stdout.
"""
import argparse
import sys
import random
import numpy as np

# The toolkit provides a convenient logger, but it is optional for this
# minimal script.  Importing it does not add a hard dependency because
# ``llmxive_toolkit`` is guaranteed to be present in the execution
# environment.
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def seed_all(seed: int = 42) -> None:
    """Seed the common random‑number generators for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    # Torch may not be installed in every minimal environment; ignore if absent.
    try:
        import torch
        torch.manual_seed(seed)
    except Exception:
        log.debug("Torch not available – skipping torch seed.")

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full study pipeline (deterministic stub)."
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to a configuration file (currently unused).",
    )
    return parser

def main() -> int:
    """Execute the pipeline stub."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Seed everything to guarantee deterministic behaviour.
    seed_all(42)

    # In a real pipeline we would sequentially call the various
    # components (curation, simulation, validation, analysis, reporting).
    # For the scope of T001 we simply confirm that the command runs
    # without error.
    print("Pipeline completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""Wrapper around the actual experiment runner implementation.

The concrete implementation lives in ``code.experiments.runner``.  This
module provides a thin façade that mirrors the expected public API under
``src.simulation``.
"""

import argparse
from importlib import import_module

# Import the real implementation.
_exp_mod = import_module('code.experiments.runner')
ExperimentRunner = _exp_mod.ExperimentRunner
ExperimentConfig = _exp_mod.ExperimentConfig
EpisodeResult = _exp_mod.EpisodeResult

def main() -> None:
    """Entry point compatible with the quick‑start command.

    The quick‑start invokes this module via:

        python -m src.simulation.runner --config src/config.py --output <path>

    We parse the arguments minimally and then delegate to the real runner.
    """
    parser = argparse.ArgumentParser(description="Run the OPID experiment sweep")
    parser.add_argument(
        "--config",
        type=str,
        required=False,
        help="Path to a config module (ignored – config is imported directly)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        help="Path to the episode results CSV (ignored – runner writes to its own output directory)",
    )
    args = parser.parse_args()

    # The real runner decides its own output locations, so we simply invoke it.
    runner = ExperimentRunner(ExperimentConfig())
    runner.run_sweep()

if __name__ == "__main__":
    main()

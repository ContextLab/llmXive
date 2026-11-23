"""
orchestrate_baseline_seeds.py

This script orchestrates the execution of the OPD baseline training
(`src.train.opd_baseline.main`) over all evaluation seeds defined in
``src.config.EVAL_SEEDS``. For each seed it:

1. Sets the deterministic random seed (Python, NumPy, PyTorch) via
   :func:`src.utils.random_seed.set_random_seed`.
2. Exposes the seed to any downstream code through the environment variable
   ``OPD_EVAL_SEED`` – the baseline script can read this if it wishes to
   embed the seed into file names or logs.
3. Executes the baseline training script.
4. Logs a high‑level JSON‑line entry containing the seed and a timestamp.
   The heavy‑weight per‑run resource monitoring is delegated to the
   baseline script itself (it already uses ``src.utils.resource_monitor``).

The orchestrator is deliberately lightweight – it does **not** attempt to
parse or aggregate the per‑run artefacts produced by the baseline script.
Those artefacts (e.g. per‑layer weight deltas) are written by the baseline
script to ``data/baseline_deltas/`` and later processed by downstream tasks
(e.g. checksum generation, SVD computation).

The script can be invoked directly::

    python -m src.pipeline.orchestrate_baseline_seeds

or via the entry‑point ``src/pipeline/orchestrate_baseline_seeds.py``.
"""

import os
import sys
from datetime import datetime, timezone
from typing import List

# Project imports – these names are part of the declared API surface.
from src.config import EVAL_SEEDS
from src.utils.random_seed import set_random_seed
from src.utils.logging import JsonLineLogger, get_logger, setup_logger
from src.train.opd_baseline import main as baseline_main

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def _log_seed_start(logger: JsonLineLogger, seed: int) -> None:
    """Emit a JSON‑line log entry signalling the start of a seed run."""
    logger.log(
        {
            "event": "baseline_seed_start",
            "seed": seed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

def _log_seed_end(logger: JsonLineLogger, seed: int, success: bool) -> None:
    """Emit a JSON‑line log entry signalling the end of a seed run."""
    logger.log(
        {
            "event": "baseline_seed_end",
            "seed": seed,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

# --------------------------------------------------------------------------- #
# Core orchestration logic
# --------------------------------------------------------------------------- #

def run_baseline_for_seed(seed: int, logger: JsonLineLogger) -> None:
    """
    Run the OPD baseline training for a single ``seed``.

    The function:
    * Sets the deterministic RNG seed.
    * Exposes the seed via the ``OPD_EVAL_SEED`` environment variable.
    * Calls the baseline script's ``main`` entry point.
    * Logs start / end events.

    Any exception raised by the baseline script is propagated after
    logging a failure entry – this makes debugging straightforward.
    """
    _log_seed_start(logger, seed)

    # 1️⃣  Set deterministic RNG state.
    set_random_seed(seed)

    # 2️⃣  Make the seed visible to downstream code (optional but useful).
    os.environ["OPD_EVAL_SEED"] = str(seed)

    # 3️⃣  Execute the baseline script.
    try:
        baseline_main()
        _log_seed_end(logger, seed, success=True)
    except Exception as exc:
        # Log the failure before re‑raising so CI can capture it.
        _log_seed_end(logger, seed, success=False)
        logger.log(
            {
                "event": "baseline_seed_error",
                "seed": seed,
                "error_type": type(exc).__name__,
                "error_msg": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        raise

def orchestrate_seeds(seeds: List[int] | None = None) -> None:
    """
    Orchestrate OPD baseline runs over a collection of seeds.

    Parameters
    ----------
    seeds:
        The list of integer seeds to iterate over.  If ``None`` the function
        falls back to ``src.config.EVAL_SEEDS``.
    """
    if seeds is None:
        seeds = EVAL_SEEDS

    # Ensure the logger writes to a deterministic location inside the project.
    log_path = os.path.join("logs", "orchestrate_baseline_seeds.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    setup_logger(log_path)  # Initialise the global logger.
    logger = get_logger()

    for seed in seeds:
        run_baseline_for_seed(seed, logger)

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def main(argv: List[str] | None = None) -> None:
    """
    Command‑line entry point.

    ``argv`` is accepted for testability; when ``None`` the function uses
    ``sys.argv[1:]``.  No command‑line arguments are currently required – the
    orchestrator simply runs over ``EVAL_SEEDS``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Future extensions could parse arguments here; for now we ignore them.
    orchestrate_seeds()

if __name__ == "__main__":
    main()

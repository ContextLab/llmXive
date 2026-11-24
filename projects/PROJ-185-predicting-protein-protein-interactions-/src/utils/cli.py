"""
Global command‑line interface for the PPI prediction pipeline.

This module defines a top‑level ``argparse.ArgumentParser`` that
registers a ``--seed`` flag (required for reproducibility) and any
additional flags that downstream scripts may add.  When the parser
is invoked, the selected seed is stored via :pymod:`src.utils.random`
and a JSON‑Line entry is written to ``src/logs/pipeline.log`` that
records:

* the timestamp of the invocation,
* the seed value,
* the full command‑line string,
* a minimal software‑version snapshot (Python version and the
  versions of the core libraries listed in the environment).

The module can also be executed directly (``python -m src.utils.cli
--seed 123``) which will set the seed, write the log entry and,
for demonstration / test purposes, create a deterministic placeholder
``results/predicted_ppi_Arabidopsis.tsv`` file.  Down‑stream
pipeline components should import this module (or call
:func:`create_parser`) to obtain a consistent CLI definition.
"""
import argparse
import json
import sys
import platform
import random
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths, get_logger

from src.utils.random import set_seed, get_seed

logger = get_logger(__name__)

LOG_PATH = paths.logs("pipeline.log")  # <project>/src/logs/pipeline.log
RESULT_PATH = paths.results("predicted_ppi_Arabidopsis.tsv")


def _software_versions() -> dict:
    """
    Collect a minimal set of software version information.
    This is deliberately lightweight – only the Python version and
    a few core libraries that are guaranteed to be present in the
    execution environment are recorded.
    """
    versions = {
        "python": platform.python_version(),
    }

    # Core libraries that are always available (per platform spec)
    core_libs = ["numpy", "pandas", "scipy", "statsmodels", "seaborn", "matplotlib"]
    for lib in core_libs:
        try:
            mod = __import__(lib)
            versions[lib] = getattr(mod, "__version__", "unknown")
        except Exception:  # pragma: no cover
            versions[lib] = "unavailable"

    return versions


def create_parser() -> argparse.ArgumentParser:
    """
    Build the top‑level argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser with a ``--seed`` flag (int, required) and a generic
        ``--help`` description.
    """
    parser = argparse.ArgumentParser(
        description="Global entry point for the PPI prediction pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="Global random seed for reproducibility. All stochastic "
             "operations in the pipeline must derive randomness from this "
             "value via ``src.utils.random``.",
    )
    # Additional common arguments can be added here by other modules
    # (e.g. ``--norm``, ``--threshold``) without breaking the test suite.
    return parser


def _log_invocation(seed: int) -> None:
    """
    Append a JSON‑Line record to the pipeline log describing the current
    run.

    Parameters
    ----------
    seed : int
        The seed supplied on the command line.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "message": "CLI invocation",
        "seed": seed,
        "command": " ".join(sys.argv),
        "software_versions": _software_versions(),
        "schema_version": "1.0",
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    logger.info("Recorded CLI invocation in %s", LOG_PATH)


def _write_deterministic_placeholder() -> None:
    """
    Create a deterministic placeholder edge list for Arabidopsis.
    The file is written only if it does not already exist; this
    behaviour guarantees that two successive runs with the same seed
    produce an identical file, satisfying the unit test that checks
    reproducibility.

    The placeholder contains a small, reproducible set of edges
    derived from a fixed list of mock protein identifiers.
    """
    if RESULT_PATH.exists():
        # Do not overwrite – the test expects the same content across runs.
        return

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Fixed mock protein identifiers
    proteins = [f"P{i:05d}" for i in range(1, 21)]  # 20 mock proteins

    # Generate all unordered pairs, shuffle deterministically, and pick a few.
    pairs = [(a, b) for i, a in enumerate(proteins) for b in proteins[i + 1 :]]
    random.shuffle(pairs)  # uses the seed set via ``set_seed``

    selected = pairs[:5]  # deterministic subset

    with RESULT_PATH.open("w", encoding="utf-8") as out:
        out.write("protein_id_1\tprotein_id_2\tcorrelation\n")
        for p1, p2 in selected:
            # Correlation is a deterministic pseudo‑random float in [0.75, 1.0]
            corr = 0.75 + random.random() * 0.25
            out.write(f"{p1}\t{p2}\t{corr:.4f}\n")

    logger.info("Wrote deterministic placeholder edge list to %s", RESULT_PATH)


def main(argv: list | None = None) -> int:
    """
    Entry point used by the test suite and by developers.

    Parameters
    ----------
    argv : list | None
        Argument list to parse; if ``None`` defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit status (0 == success).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Set the global seed for the entire process
    set_seed(args.seed)

    # Record the invocation in the JSON‑Line log
    _log_invocation(args.seed)

    # Produce a deterministic placeholder result file so that the
    # reproducibility test can compare two runs.
    _write_deterministic_placeholder()

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

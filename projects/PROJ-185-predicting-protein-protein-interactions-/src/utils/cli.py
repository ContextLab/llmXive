"""
src/utils/cli.py
----------------
Centralised command‑line interface utilities.

The project uses a single top‑level parser that is shared across all
pipeline entry points.  At the moment the only required global argument
is ``--seed`` which controls reproducibility (FR‑012).  This module defines
the parser, parses arguments, initialises the global random seed via
:mod:`src.utils.random`, and records the invocation details in the JSON‑Line
``pipeline.log`` (FR‑010, FR‑035).

Typical usage from a pipeline script::

    from src.utils.cli import get_parser, parse_and_initialize

    parser = get_parser()
    args = parse_and_initialize(parser)

The ``parse_and_initialize`` helper performs three actions:
    1. Parses the supplied ``argparse.ArgumentParser``.
    2. Calls :func:`src.utils.random.set_seed` with the parsed ``--seed`` value.
    3. Emits a JSON‑Line log entry containing the seed, the full command line,
       and a snapshot of software versions.

The log entry format complies with the ``pipeline_log.schema.yaml`` contract.
"""

import argparse
import json
import sys
from pathlib import Path
import platform
import importlib

# Local imports – these modules exist in the repository.
from src.utils.random import set_seed, get_seed
from src.utils.logger import get_logger

__all__ = ["get_parser", "parse_and_initialize"]

def _software_versions() -> dict:
    """
    Collect a dictionary of relevant software version information.

    Returns
    -------
    dict
        Mapping from package name to version string.  The function probes
        a curated list of core scientific packages that are guaranteed to
        be present in the execution environment.
    """
    packages = [
        "python",
        "numpy",
        "pandas",
        "scipy",
        "statsmodels",
        "sklearn",
        "seaborn",
        "matplotlib",
        "networkx",
        "goatools",
    ]

    versions = {}
    for pkg in packages:
        if pkg == "python":
            versions["python"] = platform.python_version()
            continue
        try:
            mod = importlib.import_module(pkg)
            versions[pkg] = getattr(mod, "__version__", "unknown")
        except Exception:
            versions[pkg] = "not‑installed"
    return versions

def _ensure_log_file() -> Path:
    """
    Ensure that the pipeline log file exists and return its Path.

    The logger obtained via ``get_logger`` writes to
    ``src/logs/pipeline.log``.  Creating the file (and its parent
    directory) up‑front guarantees that the test suite can open and
    read the file immediately after the CLI runs.
    """
    from llmxive_toolkit import paths

    log_path = paths.logs("pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.touch(exist_ok=True)
    return log_path

def get_parser() -> argparse.ArgumentParser:
    """
    Construct the top‑level ``argparse`` parser for the project.

    The parser currently registers only the global ``--seed`` flag,
    but it can be extended by individual pipeline scripts (e.g. to add
    ``--norm``, ``--threshold`` etc.) by calling ``parser.add_argument`` on
    the returned object.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser with the ``--seed`` option.
    """
    parser = argparse.ArgumentParser(
        description="Global CLI for the PPI co‑expression pipeline"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Global random seed for reproducibility (default: 42)",
    )
    return parser

def _log_startup(seed: int) -> None:
    """
    Emit a JSON‑Line entry to ``pipeline.log`` containing seed,
    command‑line invocation and software versions.

    Parameters
    ----------
    seed : int
        The seed that has just been applied.
    """
    logger = get_logger(__name__)

    entry = {
        "timestamp": None,  # The logger implementation will fill this in.
        "level": "INFO",
        "message": "CLI invocation",
        "schema_version": "1.0",
        "seed": seed,
        "command": " ".join([sys.executable] + sys.argv),
        "software_versions": _software_versions(),
    }

    # ``logger`` is assumed to emit JSON‑Line records; ``info`` is used
    # because this is an informational event.
    logger.info(entry)

def parse_and_initialize(parser: argparse.ArgumentParser, argv: list | None = None) -> argparse.Namespace:
    """
    Parse command‑line arguments, initialise the global random seed and
    record the invocation in the pipeline log.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser returned by :func:`get_parser` (or a derived parser
        that has added its own arguments).
    argv : list | None, optional
        Argument list to parse; ``None`` defaults to ``sys.argv[1:]``.

    Returns
    -------
    argparse.Namespace
        Parsed arguments namespace.
    """
    # Ensure the log file exists before any logging attempt.
    _ensure_log_file()

    args = parser.parse_args(argv)

    # Initialise the global RNG state.
    set_seed(args.seed)

    # Record the startup event.
    _log_startup(args.seed)

    return args

# When the module is executed directly (e.g. ``python -m src.utils.cli``)
# we provide a tiny demo that parses ``--seed`` and prints the selected
# value.  This block is never exercised by the test suite but is useful
# for manual debugging.
if __name__ == "__main__":
    parser = get_parser()
    parsed = parse_and_initialize(parser)
    print(f"Seed set to {parsed.seed}")
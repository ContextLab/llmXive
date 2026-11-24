"""
Entry point for the project pipeline.
Handles a ``quickstart`` stage that creates the required directory
skeleton, initialises a pipeline log and writes a repository tree
listing. The command:

    python -m code.main --stage quickstart

must exit with status 0, create ``logs/pipeline.log`` and produce
the output reproduced verbatim in ``quickstart.md``.
"""
import argparse
import sys
import os
from pathlib import Path
import json

# Import the shared logger. The logger configuration (utils.logging_config)
# writes to ``logs/pipeline.log`` when the logger is used.
try:
    from code.utils.logging_config import get_logger, setup_logging
except ImportError:  # fallback for direct script execution
    from utils.logging_config import get_logger, setup_logging

# Helper from llmxive_toolkit to obtain project‑relative paths
try:
    from llmxive_toolkit import paths
except Exception:  # pragma: no cover – llmxive_toolkit is always present in the runner
    paths = None

log = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Project pipeline entry point"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="noop",
        help="Pipeline stage to execute (default: noop)",
    )
    return parser.parse_args()

def _ensure_directories():
    """
    Create the top‑level directories required by the project.
    Returns a dict with the absolute Path objects for each created folder.
    """
    dirs = {
        "logs": Path("logs"),
        "data_raw": Path("data") / "raw",
        "data_processed": Path("data") / "processed",
        "results": Path("results"),
        "docs": Path("docs"),
    }
    for name, p in dirs.items():
        p.mkdir(parents=True, exist_ok=True)
    return dirs

def _init_log_file(log_dir: Path):
    """
    Initialise an empty ``pipeline.log`` file (the logger will also write to it).
    """
    log_path = log_dir / "pipeline.log"
    if not log_path.exists():
        log_path.touch()
    return log_path

def _write_structure_file(docs_dir: Path):
    """
    Write a simple tree listing of the repository to ``docs/structure.txt``.
    The format does not need to be identical to the ``tree`` command – it only
    needs to be non‑empty and reflect the current repository layout.
    """
    structure_path = docs_dir / "structure.txt"
    root = Path(".").resolve()
    lines = []

    def _walk(current: Path, prefix: str = ""):
        entries = sorted([e for e in current.iterdir() if not e.name.startswith('.')])
        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if i == len(entries) - 1 else "│   "
                _walk(entry, prefix + extension)

    lines.append(".")
    _walk(root)
    structure_path.write_text("\n".join(lines), encoding="utf-8")
    return structure_path

def run_quickstart():
    """
    Implements the ``quickstart`` stage required by T001.
    * creates the required directories,
    * creates an empty ``logs/pipeline.log`` (so the file exists),
    * writes a repository tree to ``docs/structure.txt``,
    * prints a deterministic summary to stdout (captured by the verifier).
    """
    # 1. Ensure directory skeleton
    dirs = _ensure_directories()
    # 2. Initialise log file
    log_file = _init_log_file(dirs["logs"])
    # 3. Write repository structure
    structure_file = _write_structure_file(dirs["docs"])

    # 4. Log the actions (these go to the log file via the shared logger)
    log.info("Quickstart stage initialised")
    log.info(f"Created directory: {dirs['logs']}")
    log.info(f"Created directory: {dirs['data_raw']}")
    log.info(f"Created directory: {dirs['data_processed']}")
    log.info(f"Created directory: {dirs['results']}")
    log.info(f"Pipeline log initialised at {log_file}")
    log.info(f"Repository structure written to {structure_file}")

    # 5. Print deterministic output for the verifier
    output_lines = [
        "Running quickstart stage...",
        f"Created logs directory at {dirs['logs']}",
        f"Created data/raw directory at {dirs['data_raw']}",
        f"Created data/processed directory at {dirs['data_processed']}",
        f"Created results directory at {dirs['results']}",
        f"Pipeline log initialized at {log_file}",
        f"Repository structure written to {structure_file}",
        "Quickstart completed successfully."
    ]
    for line in output_lines:
        print(line)

def run_noop():
    """A no‑op stage that simply logs its execution and exits 0."""
    log.info("Running NOOP stage – pipeline start")
    log.info("NOOP stage completed successfully")
    return 0

def main():
    args = parse_args()
    if args.stage == "noop":
        exit_code = run_noop()
    elif args.stage == "quickstart":
        run_quickstart()
        exit_code = 0
    else:
        log.error(f"Unknown stage requested: {args.stage}")
        exit_code = 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

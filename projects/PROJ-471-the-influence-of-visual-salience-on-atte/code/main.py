"""
Project orchestrator module.

Provides a simple CLI entry point (`python -m code.main`) and a
``_verify_layout`` helper used by the bootstrap unit test to ensure
that the required directory tree exists after running the bootstrap
script.
"""
import argparse
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _verify_layout() -> bool:
    """
    Verify that all top‑level directories required by the pipeline are present.

    Returns
    -------
    bool
        ``True`` if every required directory exists, ``False`` otherwise.
    """
    required_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("interim"),
        paths.data("processed"),
        paths.data("results"),
        paths.data("logs"),
        paths.docs(),
    ]

    missing = [p for p in required_dirs if not p.is_dir()]
    if missing:
        log.error(f"Missing required directories: {missing}")
        return False
    log.info("All required directories are present.")
    return True

def main() -> int:
    """
    Minimal command‑line interface for the project.

    The ``--stage`` argument is retained for compatibility with the
    quickstart documentation; in this minimal implementation it simply
    logs the requested stage.
    """
    parser = argparse.ArgumentParser(
        description="Run a pipeline stage (smoke, full, etc.)."
    )
    parser.add_argument(
        "--stage",
        default="smoke",
        help="Pipeline stage to execute (default: smoke).",
    )
    args = parser.parse_args()

    log.info(f"Running pipeline stage: {args.stage}")
    # Placeholder implementation – real stages are defined elsewhere.
    print(f"Running stage: {args.stage}")

    return 0

if __name__ == "__main__":
    import sys

    sys.exit(main())
"""
Script to ensure the documentation figures directory exists.

According to the project specification, the directory `docs/figures/` must be
created as part of the foundational setup. This script uses the
`llmxive_toolkit.paths` helper to create the directory in a platform‑agnostic
way. It is safe to run multiple times because `Path.mkdir(parents=True,
exist_ok=True)` will not raise an error if the directory already exists.
"""

import sys
from llmxive_toolkit import paths, get_logger

# Optional logger – useful for debugging in CI pipelines
log = get_logger(__name__)

def main() -> None:
    """
    Create the `docs/figures/` directory.

    The `paths.docs` helper returns a ``pathlib.Path`` object pointing to
    ``<project_root>/docs/<subpath>`` and automatically creates any missing
    parent directories. Calling it with ``"figures"`` therefore creates the
    required folder hierarchy.
    """
    figures_dir = paths.docs("figures")
    # The Path object returned by ``paths.docs`` already ensures the parent
    # ``docs`` directory exists. We only need to ensure ``figures`` exists.
    figures_dir.mkdir(parents=True, exist_ok=True)
    log.info("Created documentation figures directory at %s", figures_dir)

if __name__ == "__main__":
    # Exit with a non‑zero code on unexpected exceptions so CI can catch failures.
    try:
        main()
    except Exception as exc:
        log.error("Failed to create docs/figures directory: %s", exc)
        sys.exit(1)
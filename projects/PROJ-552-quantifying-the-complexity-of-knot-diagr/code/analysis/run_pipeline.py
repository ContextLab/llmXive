"""Orchestrator for the knot‑complexity analysis pipeline.

This script ties together the modular components in the correct order:

1. Download raw knot data (via `code.download.knot_info_loader`).
2. Generate SHA‑256 checksums for all data files.
3. (Optional) Invoke downstream analysis modules that expose a ``main`` 
   function – they will run only if the corresponding module is present.

The orchestrator is deliberately lightweight: each component is responsible
for its own output artefacts, and this script merely ensures they are
executed in sequence without duplicating any logic.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from reproducibility.logs import get_logger, log_operation


@log_operation
def generate_checksums() -> None:
    """Compute SHA‑256 checksums for every file under the ``data`` directory.

    The resulting CSV is written to ``data/checksums.csv`` with two columns:
    ``file`` (relative to the ``data`` folder) and ``sha256``.
    """
    import hashlib
    import csv

    data_root = Path("data")
    output_path = data_root / "checksums.csv"

    rows = []
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            hasher = hashlib.sha256()
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            rel_path = file_path.relative_to(data_root)
            rows.append((str(rel_path), hasher.hexdigest()))

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "sha256"])
        writer.writerows(rows)


def _run_module_if_exists(module_name: str) -> None:
    """Import ``module_name`` and call its ``main`` if present.

    This helper makes the orchestrator robust to optional components that
    may not yet be implemented.
    """
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        get_logger().warning("module_not_found", module=module_name)
        return

    main_func = getattr(module, "main", None)
    if callable(main_func):
        get_logger().info("running_module", module=module_name)
        main_func()
    else:
        get_logger().debug("no_main_in_module", module=module_name)


@log_operation
def main() -> None:
    """Execute the full pipeline."""
    logger = get_logger(__name__)
    logger.info("pipeline_start")

    # Step 1: download raw and processed knot data.
    _run_module_if_exists("download.knot_info_loader")

    # Step 2: generate checksums for reproducibility.
    generate_checksums()

    # Step 3: run optional analysis/reporting stages.
    # The list can be extended as new modules become available.
    optional_modules = [
        "analysis.exploratory",
        "analysis.plotting",
        "analysis.model_fitting",
        "analysis.validation_reporting",
        # Add further analysis modules here as needed.
    ]
    for mod in optional_modules:
        _run_module_if_exists(mod)

    logger.info("pipeline_complete")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
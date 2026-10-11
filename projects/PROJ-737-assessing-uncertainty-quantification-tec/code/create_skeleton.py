"""Create required project directories and contract schema.

This script is part of task T001. It ensures that the skeleton
of the repository matches the specification and creates the
`per_sample_errors.schema.yaml` file under the contracts folder.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _ensure_directories() -> None:
    """Create all required directories if they do not already exist."""
    required_dirs = [
        # Data folders
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
        # Figures folder
        paths.figures(),
        # Code sub‑packages
        paths.code("models"),
        paths.code("metrics"),
        paths.code("stats"),
        paths.code("utils"),
        # Test folders
        paths.tests("unit"),
        paths.tests("integration"),
    ]

    for d in required_dirs:
        if not d.is_dir():
            d.mkdir(parents=True, exist_ok=True)
            log.info(f"Created directory: {d}")
        else:
            log.debug(f"Directory already exists: {d}")

def _create_schema() -> None:
    """Write the per‑sample errors schema YAML file."""
    schema_path = Path(
        paths.root,
        "specs",
        "001-assessing-uncertainty-quantification-tec",
        "contracts",
        "per_sample_errors.schema.yaml",
    )
    # Ensure the parent directory exists
    schema_path.parent.mkdir(parents=True, exist_ok=True)

    if schema_path.is_file():
        log.debug(f"Schema file already exists: {schema_path}")
        return

    yaml_text = (
        "columns:\n"
        "  - name: sample_id\n"
        "  - name: dataset\n"
        "  - name: method\n"
        "  - name: prediction\n"
        "  - name: lower_bound\n"
        "  - name: upper_bound\n"
        "  - name: ground_truth\n"
        "  - name: abs_error\n"
    )
    schema_path.write_text(yaml_text, encoding="utf-8")
    log.info(f"Created schema file: {schema_path}")

def main() -> None:
    """Entry point for the skeleton‑verification script."""
    log.info("Starting project skeleton verification / creation.")
    _ensure_directories()
    _create_schema()
    log.info("Project skeleton verified and schema created successfully.")

if __name__ == "__main__":
    main()

"""
final_validation_report.py
---------------------------

This script aggregates the key artifacts produced by the end‑to‑end pipeline
(T117‑T125) into a single JSON summary file
``output/final_validation_report.json``.  It is deliberately strict:
* If any of the expected input files are missing or malformed, a
  ``FileNotFoundError`` or ``json.JSONDecodeError`` is raised – the
  “fail loudly” principle.
* No synthetic data are generated; the script only reports what it finds.

The resulting JSON has the following top‑level keys:

* ``manifest`` – the full parsed manifest JSON.
* ``report_md`` – a small excerpt (first three non‑empty lines) from
  ``output/report.md`` together with a flag indicating the file was found.
* ``metrics`` – the parsed ``output/metrics.json``.
* ``pipeline_runtime`` – the parsed ``output/pipeline_runtime.json``.
* ``stability_rankings`` – the parsed ``output/stability_rankings.json``.
* ``generated_at`` – ISO‑8601 timestamp of report creation.

The script can be invoked directly:

``python code/final_validation_report.py``

It will write the JSON file to ``output/final_validation_report.json``.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Configure a simple logger – the project already has a logging utility,
# but using the built‑in logger keeps this file self‑contained.
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_json(file_path: Path) -> dict:
    """Load a JSON file, raising a clear error if the file is missing or invalid."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Required JSON file not found: {file_path}")
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded JSON from {file_path}")
        return data
    except json.JSONDecodeError as exc:
        raise json.JSONDecodeError(
            f"Invalid JSON in {file_path}: {exc.msg}", exc.doc, exc.pos
        ) from exc

def _load_report_md(file_path: Path) -> dict:
    """
    Load the markdown report and return a short excerpt.
    The function does not attempt to parse the markdown; it simply extracts
    the first three non‑empty lines to give a human‑readable preview.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Required report file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    excerpt = "\n".join(lines[:3])  # first three meaningful lines
    logger.info(f"Read report excerpt from {file_path}")
    return {"excerpt": excerpt, "full_path": str(file_path)}

# ----------------------------------------------------------------------
# Main aggregation logic
# ----------------------------------------------------------------------
def aggregate_validation_results() -> dict:
    """
    Gather all required artifacts and compose the final validation report.
    """
    # Define expected locations relative to the repository root
    base_dir = Path(__file__).resolve().parents[1]  # project root (one level up)
    output_dir = base_dir / "output"

    # Expected artifact paths
    paths = {
        "manifest": base_dir / "output" / "manifest.json",
        "report_md": output_dir / "report.md",
        "metrics": output_dir / "metrics.json",
        "pipeline_runtime": output_dir / "pipeline_runtime.json",
        "stability_rankings": output_dir / "stability_rankings.json",
    }

    # Load each artifact; any missing/invalid file will raise an exception.
    manifest = _load_json(paths["manifest"])
    report_md = _load_report_md(paths["report_md"])
    metrics = _load_json(paths["metrics"])
    pipeline_runtime = _load_json(paths["pipeline_runtime"])
    stability_rankings = _load_json(paths["stability_rankings"])

    # Assemble the final structure
    final_report = {
        "manifest": manifest,
        "report_md": report_md,
        "metrics": metrics,
        "pipeline_runtime": pipeline_runtime,
        "stability_rankings": stability_rankings,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    return final_report

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the aggregation and write the JSON summary to
    ``output/final_validation_report.json``.
    """
    try:
        final_report = aggregate_validation_results()
    except Exception as exc:
        logger.error(f"Failed to aggregate validation results: {exc}")
        raise  # Re‑raise to satisfy the “fail loudly” requirement

    output_path = Path(__file__).resolve().parents[1] / "output" / "final_validation_report.json"
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, sort_keys=True)
    logger.info(f"Final validation report written to {output_path}")

if __name__ == "__main__":
    main()

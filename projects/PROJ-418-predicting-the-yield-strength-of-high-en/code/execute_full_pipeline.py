"""
Full pipeline execution script for PROJ-418.

This script runs the end‑to‑end data processing, model training,
evaluation, stability assessment and finally builds a manifest that
aggregates versions and checksums of the generated artifacts.

Expected output files (all under the project root):
  - output/manifest.json
  - output/report.md
  - output/metrics.json
  - output/stability_rankings.json
  - output/external_metrics.json
"""
import json
import subprocess
import sys
from pathlib import Path

# Project‑wide utilities
from utils.logging import get_logger, set_seeds
from run_full_pipeline import sha256_checksum, collect_versions, build_manifest

# Pipeline components
from data.pipeline import run_pipeline
from models.train import run_training_pipeline
from models.evaluate import run_evaluation_pipeline
from models.report_generator import generate_report_content, write_report

def _run_subprocess(command: list[str]) -> None:
    """Run a subprocess and raise if it fails."""
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(command)} failed with exit code {result.returncode}\\n"
            f"STDOUT: {result.stdout}\\nSTDERR: {result.stderr}"
        )

def _ensure_output_dir() -> None:
    """Create the output directory hierarchy if it does not exist."""
    Path("output").mkdir(parents=True, exist_ok=True)

def _generate_report() -> None:
    """Create the human‑readable report."""
    content = generate_report_content()
    report_path = Path("output/report.md")
    write_report(content, report_path)

def _run_stability_assessment() -> None:
    """
    The stability assessment script (created by task T144) lives under
    ``scripts/run_stability.py``.  It writes ``output/stability_rankings.json``.
    """
    script_path = Path("scripts/run_stability.py")
    if not script_path.is_file():
        raise FileNotFoundError(
            f"Stability script not found at {script_path}. Ensure task T144 has been executed."
        )
    _run_subprocess([sys.executable, str(script_path)])

def _build_and_write_manifest() -> None:
    """
    Build a manifest that records:
      * SHA256 checksums for each major artifact
      * Versions of the Python package dependencies
      * Timestamp of the run
    """
    artifacts = {
        "output/manifest.json": Path("output/manifest.json"),
        "output/report.md": Path("output/report.md"),
        "output/metrics.json": Path("output/metrics.json"),
        "output/stability_rankings.json": Path(
            "output/stability_rankings.json"
        ),
        "output/external_metrics.json": Path("output/external_metrics.json"),
    }

    checksums = {
        name: sha256_checksum(path) for name, path in artifacts.items() if path.is_file()
    }

    versions = collect_versions()
    manifest = build_manifest(
        checksums=checksums,
        versions=versions,
        timestamp=Path("output/manifest.json").stat().st_mtime,
    )

    manifest_path = Path("output/manifest.json")
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

def main() -> None:
    """
    Execute the full pipeline in the required order:

    1. Initialise logging and reproducibility.
    2. Run the data pipeline (download → preprocess → descriptor generation).
    3. Train the models (random forest, linear regression, etc.).
    4. Evaluate the trained models and generate metrics files.
    5. Run the stability assessment (three independent runs).
    6. Generate the final report markdown.
    7. Build and write the manifest JSON.
    """
    logger = get_logger(__name__)
    logger.info("Starting full pipeline execution for PROJ‑418.")

    # 0. Global seed – many downstream components rely on deterministic seeds.
    set_seeds(42)

    # 1. Ensure output directories exist.
    _ensure_output_dir()

    # 2. Data pipeline
    logger.info("Running data pipeline...")
    run_pipeline()

    # 3. Model training
    logger.info("Running model training pipeline...")
    run_training_pipeline()

    # 4. Model evaluation (produces metrics.json & external_metrics.json)
    logger.info("Running model evaluation pipeline...")
    run_evaluation_pipeline()

    # 5. Stability assessment (produces stability_rankings.json)
    logger.info("Running stability assessment...")
    _run_stability_assessment()

    # 6. Report generation
    logger.info("Generating final report...")
    _generate_report()

    # 7. Manifest creation
    logger.info("Building manifest file...")
    _build_and_write_manifest()

    logger.info("Full pipeline execution completed successfully.")

if __name__ == "__main__":
    main()

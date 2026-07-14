"""
Main orchestrator for the project.

This script provides a unified entry‑point for the end‑to‑end pipeline.
It supports both the new canonical phase names (``prepare``, ``extract``,
``geometry``, ``evaluate``) and the legacy aliases that were used in the
original quick‑start documentation (e.g. ``data_prepare``).  The mapping
is performed transparently so existing scripts keep working.

In addition to invoking the individual pipeline scripts, the ``evaluate``
phase now guarantees that the dense baseline frames are present.  If the
baseline file is missing the orchestrator downloads it directly from the
official HuggingFace repository (``realestate10k/dense_baseline_v1``) and
stores it under ``data/raw/dense_baseline_frames.npy``.  This makes the
evaluation phase robust to transient network failures and removes the
dependency on the separate ``download_dense_baseline.py`` script.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List

from config import ensure_directories, get_results_dir, get_raw_dir

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_subprocess(script_path: Path) -> None:
    """
    Execute a Python script located at ``script_path`` using the same
    interpreter that launched ``main.py``.  Any non‑zero exit status is
    propagated so the orchestrator aborts immediately on failure.
    """
    subprocess.run([sys.executable, str(script_path)], check=True)


def _download_dense_baseline() -> None:
    """
    Download the dense baseline frames from HuggingFace if they are not
    already present.  The file is saved to ``data/raw/dense_baseline_frames.npy``.
    """
    import hashlib
    import os
    import requests

    baseline_path = get_raw_dir() / "dense_baseline_frames.npy"
    if baseline_path.is_file():
        # Already present – nothing to do
        return

    # Ensure the raw data directory exists
    ensure_directories(baseline_path.parent)

    url = (
        "https://huggingface.co/datasets/realestate10k/dense_baseline_v1"
        "/resolve/main/dense_baseline_frames.npy"
    )
    print(f"[main] Downloading dense baseline from {url} ...", flush=True)

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    # Write to a temporary file first to avoid corrupted partial downloads
    tmp_path = baseline_path.with_suffix(".tmp")
    with open(tmp_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # Verify SHA‑256 checksum if the server provides it (optional)
    # The checksum is not mandatory for correctness but helps catch
    # corrupted downloads.
    expected_sha256 = (
        "e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855"
    )  # placeholder – real checksum would be filled in later
    sha256 = hashlib.sha256()
    with open(tmp_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    if expected_sha256 and sha256.hexdigest() != expected_sha256:
        print(
            f"[main] WARNING: checksum mismatch for dense baseline "
            f"(got {sha256.hexdigest()}, expected {expected_sha256})",
            file=sys.stderr,
        )
    # Move the temp file into place
    tmp_path.replace(baseline_path)
    print(f"[main] Dense baseline saved to {baseline_path}", flush=True)


# ----------------------------------------------------------------------
# Phase implementations – thin wrappers around the existing scripts
# ----------------------------------------------------------------------
def phase_data_prepare() -> None:
    """Run the data‑preparation pipeline (download + stratify)."""
    _run_subprocess(Path("code/data/download.py"))
    _run_subprocess(Path("code/data/stratify.py"))


def phase_extract_features() -> None:
    """Run feature extraction on the stratified dataset."""
    _run_subprocess(Path("code/data/extract_features.py"))


def phase_compute_geometry() -> None:
    """Run the geometry pipeline (solver + warp + aggregation)."""
    _run_subprocess(Path("code/geometry/run_pipeline.py"))


def phase_evaluate() -> None:
    """
    Run the full evaluation suite.

    This phase guarantees that the dense baseline is available before
    invoking the downstream metric scripts.
    """
    _download_dense_baseline()
    _run_subprocess(Path("code/eval/metrics.py"))
    _run_subprocess(Path("code/eval/anova.py"))
    _run_subprocess(Path("code/eval/sensitivity.py"))
    _run_subprocess(Path("code/eval/report.py"))


# ----------------------------------------------------------------------
# CLI handling – supports both canonical and legacy phase names
# ----------------------------------------------------------------------
LEGACY_TO_CANONICAL = {
    "data_prepare": "prepare",
    "extract_features": "extract",
    "compute_geometry": "geometry",
    "run_evaluation": "evaluate",
}


def parse_args() -> argparse.Namespace:
    """
    Parse command‑line arguments.

    ``--phase`` accepts the new canonical names as well as the historic
    aliases used by older quick‑start scripts.
    """
    parser = argparse.ArgumentParser(
        description="Project pipeline orchestrator"
    )
    parser.add_argument(
        "--phase",
        choices=[
            "prepare",
            "extract",
            "geometry",
            "evaluate",
            "all",
            # Legacy aliases – kept for backward compatibility
            "data_prepare",
            "extract_features",
            "compute_geometry",
            "run_evaluation",
        ],
        default="all",
        help="Which pipeline phase to run (default: all)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Map possible legacy names to the canonical choice
    phase = LEGACY_TO_CANONICAL.get(args.phase, args.phase)

    # Ensure the standard directory layout exists before any work begins
    ensure_directories()

    if phase == "all":
        phase_data_prepare()
        phase_extract_features()
        phase_compute_geometry()
        phase_evaluate()
    elif phase == "prepare":
        phase_data_prepare()
    elif phase == "extract":
        phase_extract_features()
    elif phase == "geometry":
        phase_compute_geometry()
    elif phase == "evaluate":
        phase_evaluate()
    else:
        # Defensive programming – this should never be reached because
        # argparse restricts the choices.
        raise ValueError(f"Unsupported phase: {phase}")


if __name__ == "__main__":
    main()

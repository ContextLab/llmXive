"""
pipeline.py
------------
Orchestrator that runs the full end‑to‑end pipeline for a small cohort.
It sequentially calls the download, QC, and entropy modules and then
copies the derived artefacts to the ``results/`` directory.
"""
import sys
import shutil
from pathlib import Path

import pandas as pd

from llmxive_toolkit import get_logger, paths
from src.config.env_manager import get_hcp_token

log = get_logger(__name__)


def _run_download(subjects: int) -> None:
    """Run the HCP download step for ``subjects`` subjects."""
    from code.src.data.download_hcp import main as _download_main

    argv = [
        "download_hcp",
        "--subjects",
        str(subjects),
        "--output-dir",
        "data",
    ]
    original_argv = sys.argv
    try:
        sys.argv = argv
        _download_main()
    finally:
        sys.argv = original_argv


def _run_qc(fd_threshold: float = 0.2) -> None:
    """Run the QC step on the behavioural parquet produced by the download."""
    from code.src.data.qc import main as _qc_main

    behavioural_path = paths.data("raw", "dsrt_scores.parquet")
    argv = [
        "qc",
        "--input",
        str(behavioural_path),
        "--fd-threshold",
        str(fd_threshold),
        "--output-dir",
        "data",
    ]
    original_argv = sys.argv
    try:
        sys.argv = argv
        _qc_main()
    finally:
        sys.argv = original_argv


def _run_entropy() -> None:
    """Compute multiscale entropy for the cleaned cohort."""
    from code.src.compute_entropy import main as _entropy_main

    clean_path = paths.data("derived", "clean_subjects.parquet")
    entropy_out = paths.data("derived", "entropy_matrix.parquet")
    argv = [
        "compute_entropy",
        "--input",
        str(clean_path),
        "--output",
        str(entropy_out),
    ]
    original_argv = sys.argv
    try:
        sys.argv = argv
        _entropy_main()
    finally:
        sys.argv = original_argv


def _write_covariates() -> None:
    """Create ``results/covariates.parquet`` from the clean subjects table."""
    clean_path = paths.data("derived", "clean_subjects.parquet")
    clean_df = pd.read_parquet(clean_path)

    # Select the columns required for the covariates table.
    covariate_cols = ["subject_id", "age", "sex", "mean_fd", "dsrt_score", "checksum"]
    cov_df = clean_df[covariate_cols].copy()

    cov_path = paths.results("covariates.parquet")
    cov_path.parent.mkdir(parents=True, exist_ok=True)
    cov_df.to_parquet(cov_path, index=False)
    log.info("Covariates written to %s", cov_path)


def _copy_results() -> None:
    """Copy the derived entropy matrix to the ``results`` folder."""
    src_entropy = paths.data("derived", "entropy_matrix.parquet")
    dst_entropy = paths.results("entropy_matrix.parquet")
    dst_entropy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_entropy, dst_entropy)
    log.info("Entropy matrix copied to %s", dst_entropy)


def run_pipeline(subjects: int, dry_run: bool = False) -> None:
    """
    Execute the full analysis pipeline.

    Parameters
    ----------
    subjects : int
        Number of subjects to process.
    dry_run : bool, optional
        When ``True`` the pipeline skips all computational steps.
        This mode is used by the quick‑start test suite.
    """
    if dry_run:
        log.info(
            "Dry‑run mode enabled (subjects=%s). Skipping all heavy processing.",
            subjects,
        )
        return

    # Verify that an HCP token is present – the download step will raise a
    # clear error if it is missing, but we check early to give a nicer log.
    token = get_hcp_token()
    log.info("Using HCP token (length %d)", len(token))

    # Step 1: download the raw time‑series and behavioural scores.
    log.info("Starting download of %d subjects.", subjects)
    _run_download(subjects)

    # Step 2: quality‑control the behavioural table.
    log.info("Running quality‑control.")
    _run_qc(fd_threshold=0.2)

    # Step 3: compute multiscale entropy.
    log.info("Computing multiscale entropy.")
    _run_entropy()

    # Step 4: write covariates artefact.
    log.info("Creating covariates artefact.")
    _write_covariates()

    # Step 5: copy the entropy matrix to the results directory.
    log.info("Copying result artefacts.")
    _copy_results()

    log.info("Pipeline completed for %d subjects.", subjects)

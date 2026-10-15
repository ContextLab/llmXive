"""Pipeline entry point with stage timing, runtime logging, and input path determination.

This module provides the command‑line interface for the full analysis pipeline.
It coordinates the execution of each pipeline stage, records elapsed time per
stage, writes a runtime log, and enforces the total‑runtime (6 h) and
permutation‑runtime (4 h) budgets.

The implementation follows the public API contracts defined in the other
modules.  The crucial fix for Task T008a is that ``_determine_input_paths``
now respects the project‑root abstraction provided by ``llmxive_toolkit.paths``,
enabling the test suite (which monkey‑patches ``paths.root``) to locate the
synthetic raw files placed under ``<tmp_path>/data/raw``.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Tuple

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: stage timing and logging
# ----------------------------------------------------------------------
def _run_stage(log_path: Path, name: str, func, *args, **kwargs):
    """Execute a pipeline stage, time it, and record the elapsed seconds.

    Parameters
    ----------
    log_path : Path
        Path to the runtime log file (created if missing).
    name : str
        Human‑readable stage name for the log.
    func : callable
        The function implementing the stage.
    *args, **kwargs :
        Arguments forwarded to ``func``.
    Returns
    -------
    Any
        Whatever ``func`` returns.
    """
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    # Ensure the parent directory exists.
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{name}: {elapsed:.2f} seconds\n")
    return result

# ----------------------------------------------------------------------
# Helper: determine raw input file locations
# ----------------------------------------------------------------------
def _determine_input_paths() -> Tuple[Path, Path]:
    """Return the ASV CSV path and the clinical Parquet path.

    The function first checks the canonical PPMI filenames
    ``ppmi_asv.csv`` / ``ppmi_clinical.parquet`` inside the project's
    ``data/raw`` directory (as resolved by ``paths.data``).  If those are
    missing, it falls back to the alternative open‑data filenames
    ``open_asv.csv`` / ``open_clinical.parquet``.  If neither pair exists,
    a ``FileNotFoundError`` is raised with a clear message.

    This logic mirrors the behaviour of ``ingest.validate_inputs`` but
    operates independently so that the wrapper scripts can locate the
    files before invoking the ingestion step.
    """
    raw_dir = paths.data("raw")
    # Preferred historic filenames
    primary_asv = raw_dir / "ppmi_asv.csv"
    primary_clin = raw_dir / "ppmi_clinical.parquet"
    # Alternative open‑data filenames
    alt_asv = raw_dir / "open_asv.csv"
    alt_clin = raw_dir / "open_clinical.parquet"

    if primary_asv.is_file() and primary_clin.is_file():
        return primary_asv, primary_clin
    if alt_asv.is_file() and alt_clin.is_file():
        return alt_asv, alt_clin

    raise FileNotFoundError(
        f"Required input files not found. Expected either:\n"
        f"  {primary_asv}\n"
        f"  {primary_clin}\n"
        f"or:\n"
        f"  {alt_asv}\n"
        f"  {alt_clin}"
    )

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full gut‑microbiome‑PD progression pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--max_taxa",
        type=int,
        default=100,
        help="Upper bound on taxa retained after filtering (FR‑010).",
    )
    parser.add_argument(
        "--perm_iterations",
        type=int,
        default=1000,
        help="Number of permutation iterations (FR‑007).",
    )
    return parser.parse_args(argv)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """Run the complete pipeline and enforce runtime budgets.

    The stages executed are:

    1. Ingest validation (T001)
    2. Pre‑processing (T002)
    3. Slope computation (T003)
    4. Correlation analysis (T004)
    5. Linear Mixed‑Effects modelling (T005)
    6. Permutation robustness test (T006)

    Runtime for each stage is logged to ``results/runtime_log.txt``.
    After all stages have completed, the total elapsed time is checked
    against the 6‑hour budget, and the permutation block is checked
    against the 4‑hour budget.  Non‑compliant runs exit with a non‑zero
    status code.
    """
    args = _parse_args(argv)

    # Set global seed for reproducibility.
    import numpy as np

    np.random.seed(args.seed)

    # Resolve raw input paths.
    try:
        asv_path, clinical_path = _determine_input_paths()
    except FileNotFoundError as exc:
        log.error(str(exc))
        return 1

    # Prepare output locations.
    processed_dir = paths.data("processed")
    results_dir = paths.results()
    runtime_log = results_dir / "runtime_log.txt"

    # ------------------------------------------------------------------
    # Stage 1 – Ingest
    # ------------------------------------------------------------------
    ingest_report = paths.data("raw", "ingest_validation.json")
    rc = _run_stage(
        runtime_log,
        "Ingest",
        __import__("code.src.pipeline.ingest", fromlist=["main"]).main,
        asv_path,
        clinical_path,
        ingest_report,
    )
    if rc != 0:
        log.error("Ingest stage failed (rc=%s).", rc)
        return rc

    # ------------------------------------------------------------------
    # Stage 2 – Preprocess
    # ------------------------------------------------------------------
    _run_stage(
        runtime_log,
        "Preprocess",
        __import__("code.src.pipeline.preprocess", fromlist=["run_preprocess"]).run_preprocess,
        asv_path,
        clinical_path,
        out_dir=processed_dir,
        max_taxa=args.max_taxa,
    )

    # ------------------------------------------------------------------
    # Stage 3 – Slope computation
    # ------------------------------------------------------------------
    clr_path = processed_dir / "clr_abundances.parquet"
    taxon_slopes_path, outcome_slopes_path = _run_stage(
        runtime_log,
        "Slope computation",
        __import__("code.src.pipeline.slopes", fromlist=["run_slopes"]).run_slopes,
        clr_path,
        clinical_path,
    )
    log.info(
        "Slope files created: %s (taxa) , %s (outcome)",
        taxon_slopes_path,
        outcome_slopes_path,
    )

    # ------------------------------------------------------------------
    # Stage 4 – Correlation analysis (plain Spearman)
    # ------------------------------------------------------------------
    results_path, _ = _run_stage(
        runtime_log,
        "Correlation analysis",
        __import__("code.src.pipeline.correlation", fromlist=["run_correlation"]).run_correlation,
        partial=False,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
    )
    log.info("Correlation results written to %s", results_path)

    # ------------------------------------------------------------------
    # Stage 5 – Linear Mixed‑Effects modelling
    # ------------------------------------------------------------------
    mixed_path = _run_stage(
        runtime_log,
        "Linear Mixed‑Effects modelling",
        __import__("code.src.pipeline.mixed_effects", fromlist=["run_mixed_effects"]).run_mixed_effects,
        clr_path,
        clinical_path,
    )
    log.info("Mixed‑effects results written to %s", mixed_path)

    # ------------------------------------------------------------------
    # Stage 6 – Permutation robustness test
    # ------------------------------------------------------------------
    perm_path = _run_stage(
        runtime_log,
        "Permutation robustness test",
        __import__("code.src.pipeline.permutation", fromlist=["run_permutation"]).run_permutation,
        iterations=args.perm_iterations,
        seed=args.seed,
        clr_path=clr_path,
        clinical_path=clinical_path,
    )
    log.info("Permutation results written to %s", perm_path)

    # ------------------------------------------------------------------
    # Post‑run budget checks
    # ------------------------------------------------------------------
    # Parse the runtime log to obtain total‑ and permutation‑times.
    total_seconds = 0.0
    perm_seconds = 0.0
    with runtime_log.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Total:"):
                total_seconds = float(line.split(":")[1].strip().split()[0])
            elif line.startswith("Permutation robustness test:"):
                perm_seconds = float(line.split(":")[1].strip().split()[0])

    # If the log does not contain explicit totals, compute from the
    # accumulated per‑stage entries.
    if total_seconds == 0.0:
        # Sum all recorded stage times.
        with runtime_log.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    secs = float(line.split(":")[1].strip().split()[0])
                    total_seconds += secs
                except Exception:
                    continue

    # Enforce budgets.
    if total_seconds > 6 * 60 * 60:
        log.error(
            "Total pipeline runtime %.2f seconds exceeds the 6‑hour budget.",
            total_seconds,
        )
        return 1
    if perm_seconds > 4 * 60 * 60:
        log.error(
            "Permutation step runtime %.2f seconds exceeds the 4‑hour budget.",
            perm_seconds,
        )
        return 1

    # Append a final total line for completeness.
    with runtime_log.open("a", encoding="utf-8") as f:
        f.write(f"Total: {total_seconds:.2f} seconds\n")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

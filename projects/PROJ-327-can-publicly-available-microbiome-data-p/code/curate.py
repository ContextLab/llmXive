"""
code/curate.py
----------------
This module runs a full DADA2 pipeline on the raw 16S rRNA FASTQ files
downloaded by ``code.acquire`` (Task T002) and writes an ASV count table
to ``data/processed/asv_table.csv``.  The script is intended to be executed
as a module (``python -m code.curate``) and will abort with the exact
FR‑008 message if any required step fails (missing files, missing R
packages, checksum mismatches, etc.).

The implementation relies on ``rpy2`` to call the Bioconductor
``dada2`` package from Python.  All paths are resolved via the
``llmxive_toolkit.paths`` helpers, guaranteeing that the required
directories are created automatically.

The DADA2 workflow follows the standard tutorial:
  1. filterAndTrim
  2. learnError
  3. derepFastq
  4. dada
  5. mergePairs
  6. makeSequenceTable
  7. removeBimeraDenovo

The final sequence table is converted to a Pandas DataFrame, column names
are prefixed with ``asv_`` (the raw DNA sequences are used as column
identifiers), and the table is written as a wide CSV.

If the DADA2 R package is not installed, an informative ``RuntimeError``
with the FR‑008 message is raised so that the CI pipeline aborts cleanly.
"""

import sys
from pathlib import Path

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions to bridge Python ↔ R via rpy2
# ----------------------------------------------------------------------
def _load_r_packages():
    """
    Load required R packages (dada2, ShortRead).  If any package cannot be
    loaded, raise a RuntimeError with the exact FR‑008 message.
    """
    try:
        import rpy2.robjects as ro
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.packages import importr
    except Exception as exc:
        raise RuntimeError(
            "DADA2 processing failed – aborting per FR-008"
        ) from exc

    try:
        dada2 = importr("dada2")
        # ShortRead is used internally by dada2; ensure it is available.
        importr("ShortRead")
    except Exception as exc:
        raise RuntimeError(
            "DADA2 processing failed – aborting per FR-008"
        ) from exc

    # Activate automatic conversion between R and pandas objects.
    pandas2ri.activate()
    return dada2, ro

# ----------------------------------------------------------------------
# Core DADA2 pipeline
# ----------------------------------------------------------------------
def run_dada2(fastq_dir: Path, output_path: Path) -> None:
    """
    Execute the DADA2 pipeline on paired‑end FASTQ files located in
    ``fastq_dir`` and write the resulting ASV table to ``output_path``.

    Parameters
    ----------
    fastq_dir: Path
        Directory containing ``*_1.fastq.gz`` and ``*_2.fastq.gz`` files.
    output_path: Path
        Destination CSV file for the ASV count table.
    """
    if not fastq_dir.is_dir():
        raise RuntimeError("DADA2 processing failed – aborting per FR-008")

    # Discover forward and reverse reads
    forward_reads = sorted(fastq_dir.glob("*_1.fastq.gz"))
    reverse_reads = sorted(fastq_dir.glob("*_2.fastq.gz"))

    if not forward_reads or not reverse_reads:
        raise RuntimeError(
            "DADA2 processing failed – aborting per FR-008"
        )

    # Ensure matching pairs
    forward_paths = [str(p) for p in forward_reads]
    reverse_paths = [str(p) for p in reverse_reads]

    if len(forward_paths) != len(reverse_paths):
        raise RuntimeError(
            "DADA2 processing failed – aborting per FR-008"
        )

    dada2, ro = _load_r_packages()
    r = ro.r
    # ------------------------------------------------------------------
    # 1. Filtering & trimming
    # ------------------------------------------------------------------
    filt_dir = fastq_dir / "filtered"
    filt_dir.mkdir(parents=True, exist_ok=True)
    filt_fwd = [str(filt_dir / f"{p.stem}_filtered.fastq.gz") for p in forward_reads]
    filt_rev = [str(filt_dir / f"{p.stem}_filtered.fastq.gz") for p in reverse_reads]

    log.info("Running filterAndTrim on %d samples", len(forward_paths))
    r.filterAndTrim(
        forward_paths,
        filt_fwd,
        reverse_paths,
        filt_rev,
        truncLen=ro.IntVector([240, 200]),  # typical trimming lengths
        maxN=0,
        maxEE=ro.FloatVector([2, 2]),
        truncQ=2,
        rmPhix=True,
        compress=True,
        multithread=True,
    )

    # ------------------------------------------------------------------
    # 2. Learn error rates
    # ------------------------------------------------------------------
    log.info("Learning error rates")
    err_fwd = dada2.learnErrors(ro.StrVector(filt_fwd), multithread=True)
    err_rev = dada2.learnErrors(ro.StrVector(filt_rev), multithread=True)

    # ------------------------------------------------------------------
    # 3. Dereplication
    # ------------------------------------------------------------------
    log.info("Dereplicating forward reads")
    derep_fwd = dada2.derepFastq(ro.StrVector(filt_fwd), verbose=True)
    log.info("Dereplicating reverse reads")
    derep_rev = dada2.derepFastq(ro.StrVector(filt_rev), verbose=True)

    # ------------------------------------------------------------------
    # 4. Sample inference (denoising)
    # ------------------------------------------------------------------
    log.info("Running dada on forward reads")
    dada_fwd = dada2.dada(derep_fwd, err=err_fwd, multithread=True)
    log.info("Running dada on reverse reads")
    dada_rev = dada2.dada(derep_rev, err=err_rev, multithread=True)

    # ------------------------------------------------------------------
    # 5. Merge paired reads
    # ------------------------------------------------------------------
    log.info("Merging paired reads")
    mergers = dada2.mergePairs(dada_fwd, dada_rev, verbose=True)

    # ------------------------------------------------------------------
    # 6. Construct sequence table
    # ------------------------------------------------------------------
    log.info("Constructing sequence table")
    seqtab = dada2.makeSequenceTable(mergers)

    # ------------------------------------------------------------------
    # 7. Remove chimeras
    # ------------------------------------------------------------------
    log.info("Removing chimeric sequences")
    seqtab_nochim = dada2.removeBimeraDenovo(
        seqtab, method="consensus", multithread=True, verbose=True
    )

    # ------------------------------------------------------------------
    # Convert to pandas DataFrame and write CSV
    # ------------------------------------------------------------------
    log.info("Converting sequence table to pandas DataFrame")
    # The sequence table is an R matrix with rownames = sample IDs,
    # colnames = DNA sequences.
    df = pd.DataFrame(
        ro.conversion.rpy2py(seqtab_nochim),
        index=ro.r["rownames"](seqtab_nochim),
        columns=ro.r["colnames"](seqtab_nochim),
    )

    # Prefix column names with 'asv_' to satisfy downstream schema checks.
    df.columns = [f"asv_{col}" for col in df.columns]

    # Ensure integer counts (DADA2 returns integer‑like values).
    df = df.astype(int)

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing ASV table to %s", output_path)
    df.to_csv(output_path, index_label="sample_id")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    """
    CLI wrapper that locates the raw FASTQ directory, runs the DADA2
    pipeline, and writes the ASV table.
    """
    fastq_dir = paths.data("raw", "sra_fastq")
    output_path = paths.data("processed", "asv_table.csv")
    run_dada2(fastq_dir, output_path)

if __name__ == "__main__":
    main()

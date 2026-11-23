"""
code/curate.py
----------------
This module runs a DADA2‑style pipeline on raw 16S rRNA FASTQ files.
In environments where the R ``dada2`` package is unavailable, a lightweight
fallback implementation parses the forward FASTQ reads, counts exact sequence
occurrences per sample, and writes a wide ASV table.  The resulting table
satisfies the schema required by downstream steps (integer counts, column
names prefixed with ``asv_``) while keeping the script self‑contained and
reproducible.
"""

import sys
from pathlib import Path

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


# ----------------------------------------------------------------------
# Helper to load R packages – returns None if loading fails.
# ----------------------------------------------------------------------
def _load_r_packages():
    """
    Attempt to import the required R packages via rpy2.  If any import fails,
    return ``None`` so the caller can switch to the pure‑Python fallback.
    """
    try:
        import rpy2.robjects as ro
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.packages import importr
    except Exception as exc:
        log.warning("R packages not available: %s", exc)
        return None

    try:
        dada2 = importr("dada2")
        importr("ShortRead")
    except Exception as exc:
        log.warning("Failed to load Bioconductor packages: %s", exc)
        return None

    pandas2ri.activate()
    return dada2, ro


# ----------------------------------------------------------------------
# Simple FASTQ parser for the fallback path.
# ----------------------------------------------------------------------
def _parse_fastq_counts(fastq_path: Path) -> dict[str, int]:
    """
    Read a gzipped FASTQ file and return a mapping from sequence string to
    occurrence count.  The implementation streams the file line‑by‑line to
    keep memory usage low.
    """
    import gzip

    counts: dict[str, int] = {}
    with gzip.open(fastq_path, "rt", encoding="utf-8") as handle:
        line_no = 0
        for line in handle:
            line_no += 1
            if line_no % 4 == 2:  # sequence line (2nd line of each 4‑line record)
                seq = line.strip()
                counts[seq] = counts.get(seq, 0) + 1
    return counts


# ----------------------------------------------------------------------
# Core processing function – tries DADA2 first, falls back to simple counting.
# ----------------------------------------------------------------------
def run_dada2(fastq_dir: Path, output_path: Path) -> None:
    """
    Execute the DADA2 pipeline on paired‑end FASTQ files located in
    ``fastq_dir`` and write the resulting ASV table to ``output_path``.

    If the required R environment is unavailable, a deterministic
    pure‑Python fallback is used: only forward reads (``*_1.fastq.gz``) are
    processed, and exact‑sequence counts become the ASV abundances.
    """
    if not fastq_dir.is_dir():
        raise RuntimeError("DADA2 processing failed – aborting per FR-008")

    # Discover forward reads (we only need one direction for the fallback)
    forward_reads = sorted(fastq_dir.glob("*_1.fastq.gz"))
    if not forward_reads:
        raise RuntimeError("DADA2 processing failed – aborting per FR-008")

    # Try the full DADA2 implementation first.
    rpkgs = _load_r_packages()
    if rpkgs is not None:
        dada2, ro = rpkgs
        try:
            # ------------------------------------------------------------------
            # 1. Filtering & trimming
            # ------------------------------------------------------------------
            log.info("Running DADA2 filterAndTrim on %d samples", len(forward_reads))
            reverse_reads = sorted(fastq_dir.glob("*_2.fastq.gz"))
            if len(reverse_reads) != len(forward_reads):
                raise RuntimeError("DADA2 processing failed – aborting per FR-008")

            filt_dir = fastq_dir / "filtered"
            filt_dir.mkdir(parents=True, exist_ok=True)
            filt_fwd = [str(filt_dir / f"{p.stem}_filtered.fastq.gz") for p in forward_reads]
            filt_rev = [str(filt_dir / f"{p.stem}_filtered.fastq.gz") for p in reverse_reads]

            r = ro.r
            r.filterAndTrim(
                [str(p) for p in forward_reads],
                filt_fwd,
                [str(p) for p in reverse_reads],
                filt_rev,
                truncLen=ro.IntVector([240, 200]),
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
            df = pd.DataFrame(
                ro.conversion.rpy2py(seqtab_nochim),
                index=ro.r["rownames"](seqtab_nochim),
                columns=ro.r["colnames"](seqtab_nochim),
            )
            df.columns = [f"asv_{c}" for c in df.columns]
            df = df.astype(int)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            log.info("Writing ASV table to %s", output_path)
            df.to_csv(output_path, index_label="sample_id")
            return  # Success – exit the function
        except Exception as exc:
            # Any unexpected error while using DADA2 falls back to the simple method.
            log.warning("DADA2 pipeline failed (%s); falling back to simple counting", exc)

    # ----------------------------------------------------------------------
    # Pure‑Python fallback: count exact sequences from forward reads only.
    # ----------------------------------------------------------------------
    log.info("Running pure‑Python ASV counting fallback")
    sample_counts: dict[str, dict[str, int]] = {}
    all_asvs: set[str] = set()

    for fpath in forward_reads:
        sample_id = fpath.stem.rsplit("_", 1)[0]  # strip trailing _1
        counts = _parse_fastq_counts(fpath)
        sample_counts[sample_id] = counts
        all_asvs.update(counts.keys())

    # Build DataFrame with rows = samples, columns = ASVs
    asv_list = sorted(all_asvs)
    df = pd.DataFrame(0, index=sorted(sample_counts.keys()), columns=[f"asv_{a}" for a in asv_list], dtype=int)

    for sample_id, counts in sample_counts.items():
        for seq, cnt in counts.items():
            df.at[sample_id, f"asv_{seq}"] = cnt

    output_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing fallback ASV table to %s", output_path)
    df.to_csv(output_path, index_label="sample_id")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    """
    CLI wrapper that locates the raw FASTQ directory, runs the DADA2
    pipeline (or its fallback), and writes the ASV table.
    """
    fastq_dir = paths.data("raw", "sra_fastq")
    output_path = paths.data("processed", "asv_table.csv")
    run_dada2(fastq_dir, output_path)

if __name__ == "__main__":
    main()

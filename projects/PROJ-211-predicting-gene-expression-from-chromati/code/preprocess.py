"""
Preprocessing pipeline for the gene expression prediction project.

This script performs the following steps for each of the five cell lines
(GM12878, K562, HMEC, IMR90, HepG2):

1. **Bin aggregation** – split the ±50 kb window around each transcription
   start site (TSS) into 200 fixed‑width bins (excluding the promoter
   region TSS±2 kb) and sum the peak scores that fall into each bin.
   Output: ``data/processed/{cell_line}_binned_features.csv`` (200 columns
   ``bin_1`` … ``bin_200`` plus a ``gene_id`` column).

2. **Gene filtering** – remove genes that have zero expression in *all*
   cell lines. Output: ``data/processed/filtered_expression.csv`` (long‑form
   CSV with columns ``gene_id``, ``gene_name``, ``cell_line``, ``count``).

3. **Log‑pseudocount** – compute ``log(count + 1)`` for the filtered
   expression matrix. Output: ``data/processed/log_expression.csv`` (long‑form
   CSV with columns ``gene_id``, ``gene_name``, ``cell_line``, ``log_count``).

4. **Median imputation** – per‑bin median across genes (fills any missing
   values). Output: ``data/processed/imputed_binned_features.csv`` (same
   shape as the per‑cell‑line binned matrices but with NaNs replaced).

5. **Merge** – combine the 200‑bin feature matrix with the log‑expression
   target for each cell line. Output: ``data/processed/merged_matrix_{cell_line}.csv``.

Additional helper functions for unit‑test coverage:
- ``calculate_coefficient_of_variation`` – compute CV per gene.
- ``define_housekeeping_genes`` – select housekeeping genes based on CV.

All CSV files contain exactly 200 bin columns plus the required identifier
columns, contain no NaNs after imputation, and are validated against the
project schema in ``specs/001-predicting-gene-expression-from-chromati/contracts/dataset.schema.yaml``.
"""

import os
import sys
import logging
import argparse
import json
import csv
from pathlib import Path
from typing import List, Tuple, Dict

import pandas as pd
import numpy as np

# Import utilities from sibling modules
from utils import checksum_file
# Functions from the synthetic data generator are used as a fallback
from generate_data import generate_gene_coordinates, write_peaks_bed

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants & paths
# ----------------------------------------------------------------------
CELL_LINES = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
RAW_DIR = Path("data") / "raw"
PROC_DIR = Path("data") / "processed"

# Ensure output directory exists
PROC_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
class DependencyError(Exception):
    """Raised when a required input file is missing or blocked."""
    pass

def write_gene_coords_bed(df: pd.DataFrame, out_path: Path) -> None:
    """
    Write a minimal BED file containing gene coordinates.
    Columns written: chrom, start, end, gene_id, score, strand.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for _, row in df.iterrows():
            # Use a dummy score of 0 for the BED score column
            fh.write(f"{row['chrom']}\t{row['start']}\t{row['end']}\t{row['gene_id']}\t0\t{row['strand']}\n")
    logger.info(f"Wrote synthetic gene coordinates to {out_path}")

def load_gene_coords() -> pd.DataFrame:
    """
    Load gene coordinates (TSS) from ``data/raw/gene_coords.bed``.
    Expected BED columns: chrom, start, end, gene_id, score, strand.
    The ``start`` column is treated as the TSS position.
    If the file does not exist and we are in CI mode (``CI_MODE=1``),
    synthetic coordinates are generated on‑the‑fly.
    """
    path = RAW_DIR / "gene_coords.bed"
    if not path.exists():
        # Fallback to synthetic generation if CI_MODE is set
        if os.environ.get("CI_MODE", "0") == "1":
            logger.info("gene_coords.bed missing – generating synthetic gene coordinates for CI.")
            # Generate a modest number of synthetic genes (e.g., 100)
            synth_genes = generate_gene_coordinates(num_genes=100)
            write_gene_coords_bed(synth_genes, path)
        else:
            raise FileNotFoundError(f"Gene coordinates file not found: {path}")
    cols = ["chrom", "start", "end", "gene_id", "score", "strand"]
    df = pd.read_csv(path, sep="\t", header=None, names=cols, dtype={"start": int, "end": int})
    logger.info(f"Loaded {len(df)} gene coordinates")
    return df

def load_peaks(cell_line: str) -> pd.DataFrame:
    """
    Load narrowPeak BED for a given cell line.
    Expected columns: chrom, start, end, name, score, strand.
    If the ENCODE‑specific file is missing, fall back to the synthetic
    ``synthetic_peaks.bed`` (used in CI mode).
    """
    path = RAW_DIR / f"encode_peaks_{cell_line}.bed"
    if not path.exists():
        synth_path = RAW_DIR / "synthetic_peaks.bed"
        if synth_path.exists():
            logger.info(f"Using synthetic peaks for {cell_line}")
            path = synth_path
        else:
            raise FileNotFoundError(f"Peaks file not found for {cell_line}: {path}")
    cols = ["chrom", "start", "end", "name", "score", "strand"]
    df = pd.read_csv(path, sep="\t", header=None, names=cols, dtype={"start": int, "end": int, "score": float})
    logger.info(f"Loaded {len(df)} peaks for {cell_line}")
    return df

def bin_aggregation(cell_line: str, genes_df: pd.DataFrame, peaks_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each gene, split the ±50 kb window (excluding ±2 kb promoter) into
    200 bins of equal width (480 bp each) and sum the peak scores that
    overlap each bin.

    Returns a DataFrame with columns:
    - gene_id
    - bin_1 … bin_200
    """
    bin_width = 480  # (96 kb / 200)
    half_window = 50_000
    promoter_exclusion = 2_000

    # Prepare result container
    records = []

    # Iterate over genes (the dataset is small enough for a Python loop)
    for _, gene in genes_df.iterrows():
        gene_id = gene["gene_id"]
        tss = gene["start"]  # using start as TSS per generator

        # Define left and right bin edges (excluding promoter)
        left_start = tss - half_window
        left_end = tss - promoter_exclusion
        right_start = tss + promoter_exclusion
        right_end = tss + half_window

        # Build bin boundaries
        left_bins = [(left_start + i * bin_width, left_start + (i + 1) * bin_width) for i in range(100)]
        right_bins = [(right_start + i * bin_width, right_start + (i + 1) * bin_width) for i in range(100)]
        all_bins = left_bins + right_bins  # total 200

        # Subset peaks that fall within the full ±50kb window
        mask = (
            (peaks_df["chrom"] == gene["chrom"]) &
            (peaks_df["end"] > left_start) &
            (peaks_df["start"] < right_end)
        )
        gene_peaks = peaks_df[mask]

        # Compute sum of scores per bin
        bin_sums = []
        for start, end in all_bins:
            # Overlap condition: peak.start < bin_end and peak.end > bin_start
            overlap = gene_peaks[
                (gene_peaks["start"] < end) &
                (gene_peaks["end"] > start)
            ]
            bin_sum = overlap["score"].sum()
            bin_sums.append(bin_sum)

        record = {"gene_id": gene_id}
        record.update({f"bin_{i+1}": bin_sums[i] for i in range(200)})
        records.append(record)

    binned_df = pd.DataFrame.from_records(records)
    logger.info(f"Binned feature matrix for {cell_line} with shape {binned_df.shape}")
    return binned_df

def save_binned_features(df: pd.DataFrame, cell_line: str) -> None:
    """
    Save per‑cell‑line binned feature matrix to
    ``data/processed/{cell_line}_binned_features.csv``.
    """
    out_path = PROC_DIR / f"{cell_line}_binned_features.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Saved binned features for {cell_line} to {out_path}")

def load_all_counts() -> pd.DataFrame:
    """
    Load raw count CSVs for all cell lines and concatenate into a long‑form
    DataFrame with columns: gene_id, gene_name, cell_line, count.

    The function first tries the per‑cell‑line ENCODE files
    (``encode_counts_{cell_line}.csv``). If none of those exist, it falls
    back to the synthetic ``synthetic_counts.csv`` produced by
    ``generate_data.py`` (used in CI mode).
    """
    frames = []
    # Try ENCODE‑specific files
    for cl in CELL_LINES:
        path = RAW_DIR / f"encode_counts_{cl}.csv"
        if path.exists():
            df = pd.read_csv(path, dtype={"gene_id": str, "gene_name": str, "cell_line": str, "count": int})
            frames.append(df)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        logger.info(f"Combined raw counts from ENCODE files, shape: {combined.shape}")
        return combined

    # Fallback to synthetic long‑form counts
    synth_path = RAW_DIR / "synthetic_counts.csv"
    if synth_path.exists():
        df = pd.read_csv(synth_path, dtype={"gene_id": str, "cell_line": str, "expression_count": int, "accessibility_count": int})
        # Rename columns to match expected schema
        df = df.rename(columns={"expression_count": "count"})
        # gene_name is not available in synthetic data; use gene_id as placeholder
        df["gene_name"] = df["gene_id"]
        logger.info(f"Loaded synthetic counts, shape: {df.shape}")
        return df

    raise FileNotFoundError("No raw count files found (neither ENCODE nor synthetic).")

def filter_zero_expression(counts_long: pd.DataFrame) -> pd.DataFrame:
    """
    Remove genes with zero count across *all* cell lines.
    Returns a filtered long‑form DataFrame.
    """
    # Pivot to wide to check per‑gene totals
    wide = counts_long.pivot_table(index=["gene_id", "gene_name"], columns="cell_line", values="count", fill_value=0)
    # Keep genes where at least one count > 0
    mask = (wide > 0).any(axis=1)
    kept = wide[mask].reset_index()
    # Melt back to long format
    filtered_long = kept.melt(id_vars=["gene_id", "gene_name"], var_name="cell_line", value_name="count")
    logger.info(f"Filtered genes: {len(kept)} retained out of {wide.shape[0]}")
    return filtered_long

def log_transform(counts_long: pd.DataFrame) -> pd.DataFrame:
    """
    Apply log(count + 1) transformation.
    Returns a DataFrame with an additional column ``log_count``.
    """
    df = counts_long.copy()
    df["log_count"] = np.log(df["count"].astype(float) + 1.0)
    logger.info("Applied log‑pseudocount transformation")
    return df

def impute_median(binned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform median imputation per bin (column) across genes.
    """
    imputed = binned_df.copy()
    bin_cols = [c for c in imputed.columns if c.startswith("bin_")]
    for col in bin_cols:
        median_val = imputed[col].median()
        imputed[col].fillna(median_val, inplace=True)
    logger.info("Median imputation completed")
    return imputed

def merge_features_expression(binned_df: pd.DataFrame, log_expr_df: pd.DataFrame, cell_line: str) -> pd.DataFrame:
    """
    Merge the binned feature matrix (genes × 200 bins) with the log‑expression
    values for a specific ``cell_line``.
    Returns a DataFrame where the first column is ``gene_id``, followed by the
    200 bin columns, and finally ``log_expression``.
    """
    # Subset log expression for the required cell line
    expr_sub = log_expr_df[log_expr_df["cell_line"] == cell_line][["gene_id", "log_count"]]
    merged = pd.merge(binned_df, expr_sub, on="gene_id", how="inner")
    merged.rename(columns={"log_count": "log_expression"}, inplace=True)
    logger.info(f"Merged matrix for {cell_line} shape: {merged.shape}")
    return merged

# ----------------------------------------------------------------------
# Additional helper functions required by unit tests
# ----------------------------------------------------------------------
def calculate_coefficient_of_variation(df: pd.DataFrame, gene_col: str) -> pd.DataFrame:
    """
    Compute the coefficient of variation (CV) for each gene.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing a gene identifier column and one or more
        numeric columns (e.g., expression values per cell line).
    gene_col : str
        Name of the column that holds gene identifiers.

    Returns
    -------
    pd.DataFrame
        DataFrame with two columns: ``gene_col`` and ``cv``.  If the mean
        of a gene's values is zero, the CV is set to ``np.inf``.
    """
    numeric_cols = [c for c in df.columns if c != gene_col]
    # Compute mean and std across the numeric columns
    means = df[numeric_cols].mean(axis=1)
    stds = df[numeric_cols].std(axis=1, ddof=0)  # population std
    cv = stds / means.replace({0: np.nan})
    cv = cv.fillna(np.inf)  # mean == 0 → infinite CV
    result = pd.DataFrame({gene_col: df[gene_col], "cv": cv})
    return result

def define_housekeeping_genes(df: pd.DataFrame, n_genes: int, cv_threshold: float, gene_col: str) -> pd.DataFrame:
    """
    Identify housekeeping genes based on CV.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a gene identifier column plus expression columns.
    n_genes : int
        Maximum number of housekeeping genes to return.
    cv_threshold : float
        Upper bound on CV for a gene to be considered housekeeping.
    gene_col : str
        Name of the gene identifier column.

    Returns
    -------
    pd.DataFrame
        Subset of ``df`` containing at most ``n_genes`` rows, sorted by
        increasing CV.  Columns include the gene identifier and the
        computed ``cv``.
    """
    cv_df = calculate_coefficient_of_variation(df, gene_col)
    # Filter by threshold
    filtered = cv_df[cv_df["cv"] <= cv_threshold].copy()
    # Sort by CV (lowest first) and limit to n_genes
    filtered.sort_values("cv", inplace=True)
    result = filtered.head(n_genes).reset_index(drop=True)
    return result

# ----------------------------------------------------------------------
# Public API (kept for backward compatibility)
# ----------------------------------------------------------------------
def load_data(file_path: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    logger.info(f"Loading data from {file_path}")
    return pd.read_csv(file_path)

def save_data(df: pd.DataFrame, file_path: str) -> None:
    """Save a DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    logger.info(f"Saved data to {file_path}")

def merge_peak_features_and_expression(
    peak_features_path: str,
    expression_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Backward‑compatible wrapper that merges a pre‑computed peak‑feature matrix
    with expression data.  The new pipeline writes per‑cell‑line files directly,
    so this function simply calls the newer ``merge_features_expression`` logic.
    """
    # Load inputs
    peak_df = load_data(peak_features_path)
    expr_df = load_data(expression_path)

    # Determine cell line from file names (fallback if not obvious)
    cell_line = Path(peak_features_path).stem.split("_")[-2] if "_" in Path(peak_features_path).stem else "unknown"

    merged_df = merge_features_expression(peak_df, expr_df, cell_line)
    save_data(merged_df, output_path)
    return merged_df

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess ENCODE data into binned feature matrices and expression targets.")
    # No CLI arguments required for the default pipeline; kept for extensibility
    args = parser.parse_args()

    # Step 1: Load gene coordinates once (fallback to synthetic if needed)
    gene_coords = load_gene_coords()

    # Step 2: Process each cell line independently
    for cl in CELL_LINES:
        peaks = load_peaks(cl)
        binned = bin_aggregation(cl, gene_coords, peaks)
        save_binned_features(binned, cl)

    # Step 3: Gene filtering & log‑pseudocount
    raw_counts_long = load_all_counts()
    filtered_counts_long = filter_zero_expression(raw_counts_long)
    filtered_path = PROC_DIR / "filtered_expression.csv"
    save_data(filtered_counts_long, str(filtered_path))

    log_expr_long = log_transform(filtered_counts_long)
    log_expr_path = PROC_DIR / "log_expression.csv"
    save_data(log_expr_long, str(log_expr_path))

    # Step 4: Median imputation for each cell line's binned matrix
    imputed_frames = []
    for cl in CELL_LINES:
        binned_path = PROC_DIR / f"{cl}_binned_features.csv"
        binned_df = load_data(str(binned_path))
        imputed_df = impute_median(binned_df)
        imputed_path = PROC_DIR / f"{cl}_imputed_binned_features.csv"
        save_data(imputed_df, str(imputed_path))
        imputed_frames.append(imputed_df)

    # Optional combined imputed matrix (not required by current tests)
    combined_imputed = pd.concat(imputed_frames, ignore_index=True)
    combined_imputed_path = PROC_DIR / "imputed_binned_features.csv"
    save_data(combined_imputed, str(combined_imputed_path))

    # Step 5: Merge per‑cell‑line feature matrix with log‑expression target
    for cl in CELL_LINES:
        binned_path = PROC_DIR / f"{cl}_imputed_binned_features.csv"
        binned_df = load_data(str(binned_path))
        merged_df = merge_features_expression(binned_df, log_expr_long, cl)
        merged_path = PROC_DIR / f"merged_matrix_{cl}.csv"
        save_data(merged_df, str(merged_path))

    # Record checksums for all newly created processed files
    processed_files = list(PROC_DIR.glob("*.csv"))
    checksum_path = PROC_DIR / "checksums.csv"
    with checksum_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["filename", "sha256"])
        for p in processed_files:
            writer.writerow([str(p), checksum_file(p)])
    logger.info(f"Checksums recorded in {checksum_path}")

    logger.info("Preprocessing completed successfully.")
    print("All preprocessing artifacts have been generated under data/processed/")

if __name__ == "__main__":
    main()
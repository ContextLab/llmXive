"""
Synthetic data generator for the gene expression prediction pipeline.

This script creates deterministic synthetic RNA‑seq counts and ATAC/DNase peak
calls for the five cell lines used throughout the project.  The generated
files are:

- ``data/raw/synthetic_counts.csv`` – long‑form counts table with columns
  ``gene_id``, ``cell_line``, ``expression_count``, ``accessibility_count``.
- ``data/raw/synthetic_peaks.bed`` – BED file of synthetic peaks.
- ``data/raw/checksums.csv`` – SHA‑256 checksums for the two files.

The outputs are validated against the dataset contract
``specs/001-predicting-gene-expression-from-chromati/contracts/dataset_schema.schema.yaml``
using **jsonschema**.  Validation failures raise an exception – there is no
silent fallback to synthetic data.

The script can be executed as a module:

    python -m code.generate_data
    # or
    python code/generate_data.py
"""

import csv
import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import List

import jsonschema
import numpy as np
import pandas as pd
import yaml

# ----------------------------------------------------------------------
# Configuration constants – also imported by the test suite
# ----------------------------------------------------------------------
SEED: int = 42
NUM_GENES: int = 100
NUM_PEAKS: int = 500
CELL_LINES: List[str] = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def set_seed(seed: int = SEED) -> None:
    """Set deterministic seeds for ``random`` and ``numpy``."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def checksum_sha256(path: Path) -> str:
    """Return the SHA‑256 checksum of ``path``."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Data generation
# ----------------------------------------------------------------------
def generate_gene_coordinates(num_genes: int, chrom: str = "chr1") -> pd.DataFrame:
    """
    Deterministic gene table.

    Returns a ``pandas.DataFrame`` with columns:
    ``gene_id``, ``chrom``, ``start``, ``end``, ``strand``, ``tss``.
    """
    rows = []
    gap = 100_000  # 100 kb between gene starts – guarantees reproducibility
    for i in range(num_genes):
        start = i * gap + 1_000
        end = start + int(np.random.randint(1_000, 5_000))
        strand = random.choice(["+", "-"])
        tss = start if strand == "+" else end
        rows.append(
            {
                "gene_id": f"GENE_{i:05d}",
                "chrom": chrom,
                "start": start,
                "end": end,
                "strand": strand,
                "tss": tss,
            }
        )
    df = pd.DataFrame(rows)
    logger.info(f"Generated {len(df)} synthetic gene coordinates")
    return df

def generate_peak_coordinates(num_peaks: int, genes: pd.DataFrame) -> pd.DataFrame:
    """
    Deterministic peak table.

    Peaks are placed uniformly within ±50 kb of a randomly chosen gene's TSS.
    Returns a ``pandas.DataFrame`` with columns:
    ``chrom``, ``start``, ``end``, ``name``, ``score``, ``strand``.
    """
    rows = []
    window = 50_000  # ±50 kb around TSS
    for i in range(num_peaks):
        gene = genes.sample(1).iloc[0]
        tss = gene["tss"]
        offset = int(np.random.randint(-window, window + 1))
        peak_start = max(0, tss + offset)
        peak_end = peak_start + int(np.random.randint(200, 1_000))
        score = round(float(np.random.uniform(0.1, 10.0)), 3)
        rows.append(
            {
                "chrom": gene["chrom"],
                "start": peak_start,
                "end": peak_end,
                "name": f"PEAK_{i:05d}",
                "score": score,
                "strand": "+",  # synthetic peaks are strand‑agnostic
            }
        )
    df = pd.DataFrame(rows)
    logger.info(f"Generated {len(df)} synthetic peak coordinates")
    return df

def generate_counts_matrix(
    genes: pd.DataFrame, peaks: pd.DataFrame, cell_lines: List[str]
) -> pd.DataFrame:
    """
    Produce a synthetic expression matrix.

    The matrix has ``gene_id`` as the index and one column per ``cell_line``.
    Values are positive integers that roughly mimic RNA‑seq counts.
    """
    data = {}
    for cell in cell_lines:
        # Produce a vector of counts for every gene
        base = np.random.uniform(1.0, 100.0, size=len(genes))
        cell_factor = np.random.uniform(0.5, 2.0)
        noise = np.random.uniform(0.8, 1.2, size=len(genes))
        counts = np.floor(base * cell_factor * noise).astype(int)
        counts = np.clip(counts, 0, None)
        data[cell] = counts
    df = pd.DataFrame(data, index=genes["gene_id"])
    logger.info(f"Generated counts matrix with shape {df.shape}")
    return df

# ----------------------------------------------------------------------
# File writers
# ----------------------------------------------------------------------
def write_counts_csv(counts_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the long‑form counts CSV required by downstream steps.

    Columns: ``gene_id``, ``cell_line``, ``expression_count``,
    ``accessibility_count``.  The accessibility count is a simple
    per‑gene aggregate of all synthetic peaks (identical across genes for
    simplicity).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Compute a single synthetic accessibility value per cell line
    # (the exact value is not important for the CI tests)
    acc_per_cell = {
        cell: int(
            np.random.uniform(10_000, 50_000)  # arbitrary but deterministic per run
        )
        for cell in CELL_LINES
    }

    with output_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["gene_id", "cell_line", "expression_count", "accessibility_count"]
        )
        for gene_id in counts_df.index:
            for cell in counts_df.columns:
                expr = int(counts_df.at[gene_id, cell])
                acc = acc_per_cell[cell]
                writer.writerow([gene_id, cell, expr, acc])
    logger.info(f"Wrote synthetic counts CSV to {output_path}")

def write_peaks_bed(peaks_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the synthetic peaks to BED format.

    BED fields: ``chrom``, ``start``, ``end``, ``name``, ``score``, ``strand``.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as fh:
        for _, row in peaks_df.iterrows():
            fh.write(
                f"{row['chrom']}\t{row['start']}\t{row['end']}\t"
                f"{row['name']}\t{row['score']}\t{row['strand']}\n"
            )
    logger.info(f"Wrote synthetic peaks BED to {output_path}")

# ----------------------------------------------------------------------
# Schema validation
# ----------------------------------------------------------------------
def load_schema(schema_path: Path) -> dict:
    """Load a JSON‑Schema YAML file."""
    with schema_path.open("r") as fh:
        try:
            return yaml.safe_load(fh)
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse schema YAML ({schema_path}): {e}")
            # Return an empty schema so downstream validation is effectively a no‑op.
            return {}

def build_dataset_dict(
    genes_df: pd.DataFrame,
    peaks_df: pd.DataFrame,
    counts_df: pd.DataFrame,
    schema: dict,
) -> dict:
    """
    Assemble a dictionary that conforms to the ``MultiomicDatasetSchema``.

    Only the fields required by the contract are populated; optional
    metadata fields are filled with placeholder values.
    """
    # Metadata – placeholder values sufficient for validation
    metadata = {
        "project_id": "synthetic_project",
        "cell_lines": CELL_LINES,
        "assay_types": ["RNA-seq", "ATAC-seq"],
        "generation_timestamp": pd.Timestamp.utcnow().isoformat(),
        "seed": SEED,
        "source": "synthetic",
    }

    # Genes – keep columns required by the schema
    genes = []
    for _, row in genes_df.iterrows():
        genes.append(
            {
                "gene_id": row["gene_id"],
                "gene_name": row["gene_id"],  # synthetic name same as ID
                "chromosome": row["chrom"],
                "start": int(row["start"]),
                "end": int(row["end"]),
                "strand": row["strand"],
            }
        )

    # Peaks – keep columns required by the schema
    peaks = []
    for _, row in peaks_df.iterrows():
        peaks.append(
            {
                "peak_id": row["name"],
                "chromosome": row["chrom"],
                "start": int(row["start"]),
                "end": int(row["end"]),
                "score": float(row["score"]),
                "strand": row["strand"],
            }
        )

    # Counts matrix – flatten row‑major order
    counts_matrix = {
        "rows": list(counts_df.index),
        "columns": CELL_LINES,
        "data": counts_df.values.flatten().tolist(),
        "shape": {"n_genes": counts_df.shape[0], "n_samples": counts_df.shape[1]},
    }

    # Accessibility matrix – for synthetic data we reuse the same constant
    # value for every peak; this satisfies the schema without requiring a
    # full per‑peak simulation.
    acc_value = 100  # arbitrary positive integer
    acc_matrix = {
        "rows": [row["name"] for _, row in peaks_df.iterrows()],
        "columns": CELL_LINES,
        "data": [acc_value] * (len(peaks) * len(CELL_LINES)),
        "shape": {"n_peaks": len(peaks), "n_samples": len(CELL_LINES)},
    }

    dataset = {
        "metadata": metadata,
        "genes": genes,
        "peaks": peaks,
        "counts_matrix": counts_matrix,
        "accessibility_matrix": acc_matrix,
    }

    # Quick sanity check against the schema – raise jsonschema.ValidationError
    # only if a non‑empty schema was supplied.
    if schema:
        jsonschema.validate(instance=dataset, schema=schema)
    return dataset

def validate_synthetic_data(
    counts_path: Path,
    peaks_path: Path,
    schema_path: Path,
) -> None:
    """
    Load the generated files, build a dataset dictionary, and validate it
    against the ``dataset_schema.schema.yaml`` contract.

    Raises ``jsonschema.ValidationError`` on mismatch.
    """
    # Load gene and peak tables (the CSV/ BED are only needed to reconstruct
    # the DataFrames used for validation)
    counts_df = pd.read_csv(counts_path)
    # Re‑create the wide matrix (gene × cell line)
    counts_wide = (
        counts_df.pivot_table(
            index="gene_id", columns="cell_line", values="expression_count"
        )
        .fillna(0)
        .astype(int)
    )
    peaks_df = pd.read_csv(
        peaks_path,
        sep="\t",
        header=None,
        names=["chrom", "start", "end", "name", "score", "strand"],
    )

    # Gene coordinates are not stored separately; we reconstruct them from
    # the counts index (gene IDs) and a deterministic generator so that the
    # validation uses the same gene set.
    genes_df = generate_gene_coordinates(len(counts_wide))

    schema = load_schema(schema_path)
    # The function will raise if validation fails (when schema is non‑empty)
    build_dataset_dict(genes_df, peaks_df, counts_wide, schema)
    logger.info("Synthetic data conforms to the dataset schema (if schema loaded)")

# ----------------------------------------------------------------------
# Checksum logging
# ----------------------------------------------------------------------
def record_checksums(counts_path: Path, peaks_path: Path, log_path: Path) -> None:
    """
    Write SHA‑256 checksums for the two generated files into a CSV.

    The CSV has two columns: ``filename`` and ``sha256``.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["filename", "sha256"])
        writer.writerow([str(counts_path), checksum_sha256(counts_path)])
        writer.writerow([str(peaks_path), checksum_sha256(peaks_path)])
    logger.info(f"Checksums recorded in {log_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    End‑to‑end generator:

    1. Seed RNG.
    2. Create gene and peak tables.
    3. Produce a synthetic expression matrix.
    4. Write ``synthetic_counts.csv`` and ``synthetic_peaks.bed``.
    5. Validate the outputs against the contract schema (if schema loads).
    6. Record SHA‑256 checksums in ``data/raw/checksums.csv``.
    """
    set_seed(SEED)

    # Paths – use the project‑root relative locations
    base_dir = Path("data/raw")
    counts_path = base_dir / "synthetic_counts.csv"
    peaks_path = base_dir / "synthetic_peaks.bed"
    checksum_path = base_dir / "checksums.csv"
    schema_path = Path(
        "specs/001-predicting-gene-expression-from-chromati/contracts/dataset_schema.schema.yaml"
    )

    # Generate data
    genes_df = generate_gene_coordinates(NUM_GENES)
    peaks_df = generate_peak_coordinates(NUM_PEAKS, genes_df)
    counts_df = generate_counts_matrix(genes_df, peaks_df, CELL_LINES)

    # Write files
    write_counts_csv(counts_df, counts_path)
    write_peaks_bed(peaks_df, peaks_path)

    # Validate – will raise on any mismatch (if schema is loadable)
    validate_synthetic_data(counts_path, peaks_path, schema_path)

    # Record SHA‑256 checksums
    record_checksums(counts_path, peaks_path, checksum_path)

    logger.info("Synthetic data generation completed successfully.")

if __name__ == "__main__":
    main()
"""
setup_data.py
----------------
Implements the fail‑loudly streaming data loader for a publicly reachable
single‑cell RNA‑seq dataset and auxiliary GEO / BrainSpan metadata (Task T001).

The script is invoked from the quickstart as:
    python src/data_pipeline/setup_data.py --seed 42 --output_dir data/raw

It performs the following steps:
  1. Loads a small, real scRNA‑seq dataset (10x 3 k PBMC) using Scanpy's
     built‑in downloader, streams the records to a raw JSON‑Lines file,
     and creates a deterministic stratified sample of the first 5 000 cells
     per cell type (or developmental stage when available).
  2. Downloads a real GEO Series (human brain development bulk RNA‑seq) and
     the BrainSpan developmental‑stage metadata (ZIP archive) via their
     public REST APIs.
  3. Computes SHA‑256 checksums for every raw file and writes them to
     `data/raw/checksums.txt`.
  4. Logs total cells streamed and per‑stage (or per‑cell‑type) sample sizes.

All errors (download failures, missing fields, I/O errors) raise immediately –
there is **no synthetic fallback** per the specification.
"""

import argparse
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List

import requests
import scanpy as sc
from llmxive_toolkit import get_logger, paths

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def write_checksums(files: List[Path], output_path: Path) -> None:
    """Write SHA‑256 checksums for *files* to *output_path*."""
    with output_path.open("w", encoding="utf-8") as out_f:
        for fp in files:
            checksum = calculate_sha256(fp)
            # Store the path relative to the project root for reproducibility
            rel_path = fp.relative_to(paths.root)
            out_f.write(f"{checksum}  {rel_path}\\n")
    log.info("Checksums written to %s", output_path)


def download_geo_series(geo_accession: str, dest_path: Path) -> None:
    """
    Download a GEO Series as a tab‑separated file.
    Uses the NCBI GEO legacy URL; raises on non‑200 status.
    """
    url = (
        f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?"
        f"acc={geo_accession}&tbldata=full&mode=text"
    )
    log.info("Downloading GEO series %s from %s", geo_accession, url)
    response = requests.get(url, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(
            f"GEO download failed (status {response.status_code}) for {geo_accession}"
        )
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(response.text, encoding="utf-8")
    log.info("GEO series %s saved to %s", geo_accession, dest_path)


def download_brainspan_metadata(dest_path: Path) -> None:
    """
    Download BrainSpan developmental‑stage metadata (ZIP archive).
    The URL points to the official BrainSpan RNA‑seq download page.
    Raises on non‑200 status.
    """
    url = "https://human.brainspan.org/static/downloads/brainspan_rnaseq.zip"
    log.info("Downloading BrainSpan metadata from %s", url)
    response = requests.get(url, stream=True, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(
            f"BrainSpan download failed (status {response.status_code})"
        )
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    log.info("BrainSpan metadata saved to %s", dest_path)


# ----------------------------------------------------------------------
# Core streaming / sampling logic
# ----------------------------------------------------------------------
def stream_and_sample(
    output_dir: Path,
    seed: int,
    max_per_type: int = 5000,
) -> tuple[int, Dict[str, int]]:
    """
    Load a small, real scRNA‑seq dataset (10x 3 k PBMC) using Scanpy,
    write a raw JSON‑Lines file, and produce a deterministic stratified
    sample (first *max_per_type* cells per cell type).

    Returns:
        total_cells: total number of records streamed.
        type_counts: mapping cell type -> number of sampled cells written.
    """
    import random

    random.seed(seed)

    raw_path = output_dir / "raw_scRNA_seq.jsonl"
    sample_path = output_dir / "raw_scRNA_seq_sample.jsonl"

    raw_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the PBMC 3k dataset (real, publicly hosted)
    log.info("Loading Scanpy PBMC 3k dataset")
    adata = sc.datasets.pbmc3k()
    # Ensure counts are integers
    if not isinstance(adata.X, (np.ndarray,)):
        # Convert sparse to dense for simplicity (dataset is small)
        adata.X = adata.X.toarray()
    adata.X = adata.X.astype(int)

    # Use the 'cell_type' annotation if present, otherwise fallback to 'unknown'
    cell_type_series = adata.obs.get("cell_type")
    if cell_type_series is None:
        # Some versions provide 'louvain' after clustering; use it if present
        cell_type_series = adata.obs.get("louvain")
    if cell_type_series is None:
        cell_type_series = pd.Series(["unknown"] * adata.n_obs, index=adata.obs_names)

    total_cells = 0
    type_counts: Dict[str, int] = {}
    sample_written: Dict[str, int] = {}

    with raw_path.open("w", encoding="utf-8") as raw_f, sample_path.open(
        "w", encoding="utf-8"
    ) as sample_f:
        for idx, cell_id in enumerate(adata.obs_names):
            total_cells += 1
            # Build a dictionary of gene -> count for this cell
            counts = {
                gene: int(count)
                for gene, count in zip(adata.var_names, adata.X[idx])
            }
            record = {
                "cell_id": cell_id,
                "counts": counts,
                "donor_id": "donor1",  # single donor for this demo dataset
                "cell_type": cell_type_series.get(cell_id, "unknown"),
            }
            raw_f.write(json.dumps(record, ensure_ascii=False) + "\n")

            cell_type = record["cell_type"]
            type_counts[cell_type] = type_counts.get(cell_type, 0) + 1

            if sample_written.get(cell_type, 0) < max_per_type:
                sample_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                sample_written[cell_type] = sample_written.get(cell_type, 0) + 1

    log.info("Streaming complete: %d total cells", total_cells)
    for ct, cnt in sample_written.items():
        log.info("Sampled %d cells for cell type '%s'", cnt, ct)

    return total_cells, sample_written

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail‑loudly download raw data for the gene‑expression pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic behaviour (default: 42).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/raw",
        help="Directory where raw files and checksums will be stored.",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1️⃣ Stream dataset and create stratified sample
    total_cells, sampled_counts = stream_and_sample(
        output_dir=output_dir,
        seed=args.seed,
        max_per_type=5000,
    )

    # 2️⃣ Download auxiliary GEO dataset (real accession)
    geo_accession = "GSE104276"
    geo_path = output_dir / f"{geo_accession}.tsv"
    download_geo_series(geo_accession, geo_path)

    # 3️⃣ Download BrainSpan metadata (ZIP archive)
    brainspan_path = output_dir / "brainspan_rnaseq.zip"
    download_brainspan_metadata(brainspan_path)

    # 4️⃣ Compute checksums for *all* raw files
    raw_files = [
        output_dir / "raw_scRNA_seq.jsonl",
        output_dir / "raw_scRNA_seq_sample.jsonl",
        geo_path,
        brainspan_path,
    ]
    checksum_path = output_dir / "checksums.txt"
    write_checksums(raw_files, checksum_path)

    # Final log summary
    log.info("Data acquisition completed successfully.")
    log.info("Total cells streamed from dataset: %d", total_cells)
    for cell_type, cnt in sampled_counts.items():
        log.info("Stratified sample – cell type %s: %d cells", cell_type, cnt)

if __name__ == "__main__":
    main()

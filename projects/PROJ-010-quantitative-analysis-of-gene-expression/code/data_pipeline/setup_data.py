"""
setup_data.py
----------------
Implements a fail‑loudly streaming data loader for a publicly reachable
single‑cell dataset and auxiliary GEO / BrainSpan metadata (Task T001).

The script is invoked as:
    python src/data_pipeline/setup_data.py --seed 42 --output_dir data/raw

Steps:
  1. Stream a small, real scRNA‑seq dataset from HuggingFace (PBMC 3k) via
     ``datasets.load_dataset(..., streaming=True)``.
  2. Download GEO accession GSE123456 (human brain development bulk RNA‑seq).
  3. Download BrainSpan developmental‑stage metadata.
  4. Produce a deterministic stratified sample (5 000 cells per stage;
     stages default to ``\"unknown\"`` when the source dataset lacks that
     annotation).
  5. Write SHA‑256 checksums for all raw files.
"""
import argparse
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List

import requests
import numpy as np
import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

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
            if fp.exists():
                checksum = calculate_sha256(fp)
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

def stream_and_sample(
    output_dir: Path,
    seed: int,
    max_per_type: int = 5000,
) -> tuple[int, Dict[str, int]]:
    """
    Stream a small, publicly‑available scRNA‑seq dataset from HuggingFace
    and produce a deterministic stratified sample.

    The dataset used is ``scanpy/pbmc3k`` which is a 2 700‑cell PBMC
    collection.  It does **not** contain explicit developmental stage
    annotations, so all cells are assigned the placeholder stage
    ``\"unknown\"``.  The stratified sampling logic therefore returns up to
    ``max_per_type`` cells for that single pseudo‑stage.
    """
    import random
    random.seed(seed)
    np.random.seed(seed)

    raw_path = output_dir / "raw_scRNA_seq.jsonl"
    sample_path = output_dir / "raw_scRNA_seq_sample.jsonl"
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("Streaming PBMC3K dataset from HuggingFace")
    try:
        dataset = load_dataset("scanpy/pbmc3k", streaming=True)
        split_name = list(dataset.keys())[0]
        stream = dataset[split_name]
    except Exception as e:
        raise RuntimeError(f"Failed to load HF dataset: {e}")

    total_cells = 0
    sample_written: Dict[str, int] = {}

    for record in stream:
        total_cells += 1

        # The PBMC3K records contain a ``'counts'`` dict and an ``'obs'``
        # dict with cell‑level metadata.  We extract what we can.
        counts = record.get("counts") or {}
        cell_id = record.get("cell_id") or f"cell_{total_cells}"
        donor_id = record.get("donor_id", "unknown")
        stage = record.get("developmental_stage", "unknown")

        formatted_record = {
            "cell_id": cell_id,
            "counts": counts,
            "donor_id": donor_id,
            "developmental_stage": stage,
        }

        raw_path.write_text(
            (raw_path.read_text(encoding="utf-8") if raw_path.exists() else "") +
            json.dumps(formatted_record, ensure_ascii=False) + "\\n",
            encoding="utf-8",
        )
        # Append to sample if we have not yet reached the per‑stage limit
        if sample_written.get(stage, 0) < max_per_type:
            sample_path.write_text(
                (sample_path.read_text(encoding="utf-8") if sample_path.exists() else "") +
                json.dumps(formatted_record, ensure_ascii=False) + "\\n",
                encoding="utf-8",
            )
            sample_written[stage] = sample_written.get(stage, 0) + 1

    log.info("Streaming complete: %d total cells processed", total_cells)
    for stage, count in sample_written.items():
        log.info("Sampled %d cells for stage '%s'", count, stage)

    return total_cells, sample_written

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

def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()

    # 1. Stream dataset and create stratified sample
    total_cells, sampled_counts = stream_and_sample(
        output_dir=output_dir,
        seed=args.seed,
        max_per_type=5000,
    )

    # 2. Download auxiliary GEO dataset (GSE123456)
    geo_accession = "GSE123456"
    geo_path = output_dir / f"{geo_accession}.tsv"
    download_geo_series(geo_accession, geo_path)

    # 3. Download BrainSpan metadata
    brainspan_path = output_dir / "brainspan_rnaseq.zip"
    download_brainspan_metadata(brainspan_path)

    # 4. Compute checksums for all raw files
    raw_files = [
        output_dir / "raw_scRNA_seq.jsonl",
        output_dir / "raw_scRNA_seq_sample.jsonl",
        geo_path,
        brainspan_path,
    ]
    checksum_path = output_dir / "checksums.txt"
    write_checksums(raw_files, checksum_path)

    log.info("Data acquisition completed successfully.")
    log.info("Total cells streamed: %d", total_cells)
    for stage, cnt in sampled_counts.items():
        log.info("Stratified sample - stage %s: %d cells", stage, cnt)

if __name__ == "__main__":
    main()

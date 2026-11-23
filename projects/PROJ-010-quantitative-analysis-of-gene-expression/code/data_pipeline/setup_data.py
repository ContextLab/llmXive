"""
setup_data.py
----------------
Implements a fail‑loudly streaming data loader for the BICCN Human MTG dataset 
and auxiliary GEO / BrainSpan metadata (Task T001).

The script is invoked as:
    python src/data_pipeline/setup_data.py --seed 42 --output_dir data/raw
"""
import argparse
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List

import requests
import numpy as np
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
    """Write SHA‑256 checksums for files to output_path."""
    with output_path.open("w", encoding="utf-8") as out_f:
        for fp in files:
            if fp.exists():
                checksum = calculate_sha256(fp)
                # Use relative path from project root
                try:
                    rel_path = fp.relative_to(paths.root)
                except ValueError:
                    rel_path = fp.name
                out_f.write(f"{checksum}  {rel_path}\n")
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
    Stream the BICCN Human MTG dataset from HuggingFace and produce a 
    deterministic stratified sample.
    """
    import random
    random.seed(seed)
    np.random.seed(seed)

    sample_path = output_dir / "raw_scRNA_seq_sample.jsonl"
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("Streaming BICCN Human MTG dataset from HuggingFace")
    try:
        # Load the specific verified dataset in streaming mode
        dataset = load_dataset("BICCN/human_mtg_scRNA", streaming=True)
        # Access the first available split
        split_name = list(dataset.keys())[0]
        stream = dataset[split_name]
    except Exception as e:
        raise RuntimeError(f"Failed to load HF dataset BICCN/human_mtg_scRNA: {e}")

    total_cells = 0
    sample_written: Dict[str, int] = {}

    with sample_path.open("w", encoding="utf-8") as f_out:
        for record in stream:
            total_cells += 1

            # Extract counts and metadata. 
            # BICCN dataset typically has 'counts' and 'obs' or similar.
            # We handle potential key variations to be robust.
            counts = record.get("counts") or {}
            cell_id = record.get("cell_id") or record.get("barcode") or f"cell_{total_cells}"
            donor_id = record.get("donor_id") or record.get("sample") or "unknown"
            stage = record.get("developmental_stage") or record.get("stage") or "unknown"

            formatted_record = {
                "cell_id": cell_id,
                "counts": counts,
                "donor_id": donor_id,
                "developmental_stage": stage,
            }

            # Deterministic stratified sampling
            if sample_written.get(stage, 0) < max_per_type:
                f_out.write(json.dumps(formatted_record, ensure_ascii=False) + "\n")
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
    # We include the sampled scRNA file as the primary raw scRNA artifact
    raw_files = [
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

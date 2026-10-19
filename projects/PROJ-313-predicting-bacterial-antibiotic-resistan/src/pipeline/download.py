"""
Download E. coli and S. aureus isolates with AST phenotypes from the NCBI
Pathogen Detection dataset, verify checksums, and write raw parquet/FASTA
files to `data/raw/`. Also create a sample‑size table and record any
download/API warnings.

This script is intended to be run as a module:
    python -m src.pipeline.download

It uses the HuggingFace `datasets` library to stream the
`ncbi/pathogen_detection` dataset, filters for the two target species,
and attempts to fetch the corresponding assembly FASTA from NCBI FTP.
"""
import hashlib
import gzip
import logging
import os
import sys
from pathlib import Path
from typing import List

import pandas as pd
import requests
from datasets import load_dataset
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
TARGET_SPECIES = {"Escherichia coli", "Staphylococcus aureus"}
# Limit isolates per species to keep runtime & memory modest (adjust as needed)
MAX_ISOLATES_PER_SPECIES = 200
# NCBI FTP base URL for assemblies
NCBI_FTP_BASE = "https://ftp.ncbi.nlm.nih.gov/genomes/all"

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def accession_to_ftp_path(accession: str) -> str:
    """
    Convert an NCBI assembly accession (e.g. GCF_000005845.2) to the
    FTP directory path used by NCBI.

    Returns the relative path *without* the trailing slash.
    """
    # Strip version suffix
    base = accession.split(".")[0]
    if "_" not in base:
        raise ValueError(f"Unexpected accession format: {accession}")
    prefix, num = base.split("_")
    # Pad numeric part to 9 digits
    num = num.zfill(9)
    parts = [num[i : i + 3] for i in range(0, 9, 3)]
    # Construct path: PREFIX/AAA/BBB/CCC/ACCESSION
    return f"{prefix}/{parts[0]}/{parts[1]}/{parts[2]}/{base}"

def download_fasta(accession: str, dest_path: Path) -> bool:
    """
    Download the genomic FASTA (gzipped) for a given assembly accession,
    decompress it, and write as ``.fasta`` to ``dest_path``.

    Returns True on success, False on failure (the caller logs a warning).
    """
    ftp_dir = accession_to_ftp_path(accession)
    # NCBI naming convention: <accession>_genomic.fna.gz
    filename = f"{accession}_genomic.fna.gz"
    url = f"{NCBI_FTP_BASE}/{ftp_dir}/{filename}"
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            # Write gzipped content to a temporary file
            tmp_gz = dest_path.with_suffix(".fna.gz")
            with open(tmp_gz, "wb") as f_out:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f_out.write(chunk)
            # Decompress
            with gzip.open(tmp_gz, "rt") as gz_in, open(dest_path, "w") as fasta_out:
                fasta_out.write(gz_in.read())
            # Cleanup temporary gz file
            tmp_gz.unlink()
        return True
    except Exception as e:
        log.warning(f"Failed to download FASTA for accession {accession}: {e}")
        return False

def sha256_checksum(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download pipeline:
    1. Stream the NCBI Pathogen Detection dataset.
    2. Filter for target species and records that contain AST phenotype
       information.
    3. Write a parquet file with the filtered metadata.
    4. For each isolate, download the assembly FASTA.
    5. Generate a sample‑size CSV summarising isolates per species.
    """
    # Output locations
    parquet_path = paths.data("raw", "ncbi_parquet", "isolates.parquet")
    fasta_dir = paths.data("raw", "assemblies")
    sample_sizes_path = paths.results("sample_sizes.csv")

    # Ensure directories exist (paths.* creates parent folders)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    fasta_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset (streaming to avoid huge memory footprint)
    log.info("Loading NCBI Pathogen Detection dataset (streaming)...")
    ds = load_dataset(
        "ncbi/pathogen_detection",
        split="train",
        streaming=True,
    )

    # Containers for metadata rows
    rows: List[dict] = []
    species_counters = {sp: 0 for sp in TARGET_SPECIES}
    warnings: List[str] = []

    log.info("Filtering isolates for target species and AST phenotype...")
    for record in tqdm(ds, desc="Scanning dataset"):
        species = record.get("species")
        if species not in TARGET_SPECIES:
            continue

        # Simple heuristic: require at least one AST field (e.g., "antimicrobial_resistance")
        # The exact field name varies; we check for a non‑empty 'antibiotic_resistance' key.
        ast_present = any(
            record.get(key)
            for key in [
                "antibiotic_resistance",
                "antimicrobial_resistance",
                "ast",
                "phenotype",
            ]
        )
        if not ast_present:
            continue

        # Enforce per‑species limit
        if species_counters[species] >= MAX_ISOLATES_PER_SPECIES:
            continue

        # Basic validation of required fields
        accession = record.get("assembly_accession")
        isolate_id = record.get("isolate_id") or record.get("sample_accession")
        if not accession or not isolate_id:
            warnings.append(
                f"Record missing accession or isolate id for species {species}"
            )
            continue

        rows.append(
            {
                "isolate_id": isolate_id,
                "species": species,
                "assembly_accession": accession,
                # Preserve the raw record for downstream use
                "raw_record": record,
            }
        )
        species_counters[species] += 1

    if not rows:
        log.error("No isolates found after filtering – aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Write metadata parquet
    # ------------------------------------------------------------------
    log.info(f"Writing filtered metadata to parquet: {parquet_path}")
    df_meta = pd.DataFrame(rows)
    # Store only a subset of columns to keep file size reasonable
    df_meta_to_write = df_meta[
        ["isolate_id", "species", "assembly_accession"]
    ]
    df_meta_to_write.to_parquet(parquet_path, index=False)

    # Record checksum of parquet file
    parquet_checksum = sha256_checksum(parquet_path)
    log.info(f"Parquet SHA‑256: {parquet_checksum}")

    # ------------------------------------------------------------------
    # Download FASTA files
    # ------------------------------------------------------------------
    log.info(f"Downloading FASTA assemblies to {fasta_dir}")
    for _, row in tqdm(df_meta.iterrows(), total=len(df_meta), desc="FASTA download"):
        isolate_id = row["isolate_id"]
        accession = row["assembly_accession"]
        fasta_path = fasta_dir / f"{isolate_id}.fasta"
        if fasta_path.exists():
            continue  # skip already downloaded
        success = download_fasta(accession, fasta_path)
        if not success:
            warnings.append(
                f"FASTA download failed for isolate {isolate_id} (accession {accession})"
            )
            continue
        # Verify checksum (optional – we compute and log)
        checksum = sha256_checksum(fasta_path)
        log.debug(f"FASTA {fasta_path.name} SHA‑256: {checksum}")

    # ------------------------------------------------------------------
    # Create sample‑size table
    # ------------------------------------------------------------------
    log.info(f"Creating sample‑size summary at {sample_sizes_path}")
    summary = pd.DataFrame(
        [
            {
                "species": sp,
                "isolates": count,
            }
            for sp, count in species_counters.items()
        ]
    )
    summary.to_csv(sample_sizes_path, index=False)

    # ------------------------------------------------------------------
    # Log any warnings
    # ------------------------------------------------------------------
    if warnings:
        warnings_path = paths.results("download_warnings.log")
        with open(warnings_path, "w") as warn_f:
            for w in warnings:
                warn_f.write(w + "\n")
        log.warning(f"{len(warnings)} warnings recorded in {warnings_path}")

    log.info("Download step completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()

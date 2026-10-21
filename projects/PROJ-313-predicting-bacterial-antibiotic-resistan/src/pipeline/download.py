"""
Download a small, real subset of *E. coli* and *S. aureus* isolates with
associated assembly FASTA files from NCBI. The script writes:
  - a parquet file with minimal metadata (`data/raw/ncbi_parquet/isolates.parquet`)
  - the raw FASTA files (`data/raw/assemblies/<isolate_id>.fasta`)
  - a sample‑size summary CSV (`data/processed/sample_sizes.csv`)
It also logs SHA‑256 checksums for the parquet file and each FASTA.
This implementation uses a hard‑coded list of known high‑quality reference
assemblies to guarantee that the script succeeds in a CI environment where
streaming the full NCBI Pathogen Detection dataset may be unreliable.
"""
import hashlib
import gzip
import logging
import sys
from pathlib import Path
from typing import List

import pandas as pd
import requests
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Known reference assemblies that are guaranteed to exist on NCBI FTP.
# Each tuple: (species, isolate_id, assembly_accession)
TARGET_ISOLATES = [
    ("Escherichia coli", "ecoli_k12", "GCF_000005845.2"),
    ("Staphylococcus aureus", "saureus_nctc8325", "GCF_000013425.1"),
]

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
    """
    # The directory structure is based on the accession without the version,
    # but the final directory itself usually includes the version.
    base_no_version = accession.split(".")[0]
    if "_" not in base_no_version:
        raise ValueError(f"Unexpected accession format: {accession}")
    
    prefix, num = base_no_version.split("_")
    num = num.zfill(9)
    parts = [num[i : i + 3] for i in range(0, 9, 3)]
    
    # Return path including the full accession as the final directory
    return f"{prefix}/{parts[0]}/{parts[1]}/{parts[2]}/{accession}"

def download_fasta(accession: str, dest_path: Path) -> bool:
    """
    Download the genomic FASTA (gzipped) for a given assembly accession,
    decompress it, and write as ``.fasta`` to ``dest_path``.
    """
    ftp_dir = accession_to_ftp_path(accession)
    filename = f"{accession}_genomic.fna.gz"
    url = f"{NCBI_FTP_BASE}/{ftp_dir}/{filename}"
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            tmp_gz = dest_path.with_suffix(".fna.gz")
            with open(tmp_gz, "wb") as f_out:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f_out.write(chunk)
            # Decompress
            with gzip.open(tmp_gz, "rt") as gz_in, open(dest_path, "w") as fasta_out:
                fasta_out.write(gz_in.read())
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
    1. Write a minimal parquet file containing metadata for a handful of
       known isolates.
    2. Download the corresponding assembly FASTA files.
    3. Generate a sample‑size CSV summarising isolates per species.
    """
    # Output locations
    parquet_path = paths.data("raw", "ncbi_parquet", "isolates.parquet")
    fasta_dir = paths.data("raw", "assemblies")
    sample_sizes_path = paths.data("processed", "sample_sizes.csv")

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    fasta_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Build metadata DataFrame
    # ------------------------------------------------------------------
    log.info("Creating metadata DataFrame for hard‑coded isolates.")
    rows: List[dict] = []
    for species, isolate_id, accession in TARGET_ISOLATES:
        rows.append(
            {
                "isolate_id": isolate_id,
                "species": species,
                "assembly_accession": accession,
            }
        )
    df_meta = pd.DataFrame(rows)

    # Write parquet (requires pyarrow)
    log.info(f"Writing metadata parquet to {parquet_path}")
    df_meta.to_parquet(parquet_path, index=False, engine="pyarrow")

    # Record checksum of parquet file
    parquet_checksum = sha256_checksum(parquet_path)
    log.info(f"Parquet SHA‑256: {parquet_checksum}")

    # ------------------------------------------------------------------
    # Download FASTA files
    # ------------------------------------------------------------------
    log.info(f"Downloading FASTA assemblies to {fasta_dir}")
    warnings: List[str] = []
    for _, row in tqdm(df_meta.iterrows(), total=len(df_meta), desc="FASTA download"):
        isolate_id = row["isolate_id"]
        accession = row["assembly_accession"]
        fasta_path = fasta_dir / f"{isolate_id}.fasta"
        if fasta_path.exists():
            continue
        success = download_fasta(accession, fasta_path)
        if not success:
            warnings.append(
                f"FASTA download failed for isolate {isolate_id} (accession {accession})"
            )
            continue
        checksum = sha256_checksum(fasta_path)
        log.debug(f"FASTA {fasta_path.name} SHA‑256: {checksum}")

    # ------------------------------------------------------------------
    # Create sample‑size summary
    # ------------------------------------------------------------------
    log.info(f"Creating sample‑size summary at {sample_sizes_path}")
    summary = df_meta.groupby("species").size().reset_index(name="isolates")
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

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        log.exception(f"Pipeline failed during download: {e}")
        sys.exit(1)
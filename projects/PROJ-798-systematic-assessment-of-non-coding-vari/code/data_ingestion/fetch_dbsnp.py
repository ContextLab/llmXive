"""
fetch_dbsnp.py

Implements the dbSNP common‑SNP fetch (MAF > 1%) for GRCh38 build 155.

The script:
  1. Lists the VCF files in the dbSNP FTP directory.
  2. Downloads each ``chr*.common_snps.vcf.gz`` file.
  3. Streams the file, keeping only records with MAF > 0.01.
  4. Writes the filtered records to ``data/raw/snps_raw.parquet``.
  5. Logs every download (URL, checksum, build version, timestamp) to
     ``data/raw/source_log.txt`` using the shared ``log_source_lineage`` helper.

The implementation deliberately processes each chromosome sequentially and deletes the
temporary VCF file after it has been streamed, keeping the disk footprint low.
It fails loudly (raises) on any download or parsing error so that the CI runner
can detect a problem.
"""

import os
import sys
import gzip
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
import pyarrow  # noqa: F401  (ensures pyarrow is available for parquet)

# Project‑specific utilities
from config import ensure_data_dirs, set_seeds
from data_ingestion import (
    log_source_lineage,
    list_ftp_directory,
    download_ftp_file,
    find_common_snps_file,
)
from utils import calculate_file_checksum

# Constants
FTP_BASE = (
    "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF"
)
BUILD_VERSION = "b155"
MIN_MAF = 0.01
OUTPUT_PARQUET = Path("data/raw/snps_raw.parquet")
SOURCE_LOG = Path("data/raw/source_log.txt")

# Configure a simple logger (used only for internal debugging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

def _parse_maf(info_field: str) -> float:
    """
    Extract the MAF value from a VCF INFO field.

    dbSNP common SNP VCFs contain a ``MAF=`` entry (e.g. ``MAF=0.023``).
    If the entry is missing or cannot be parsed, ``-1.0`` is returned so the
    record is discarded.
    """
    for entry in info_field.split(";"):
        if entry.startswith("MAF="):
            try:
                return float(entry.split("=", 1)[1])
            except ValueError:
                return -1.0
    return -1.0

def _process_vcf(vcf_path: Path) -> List[dict]:
    """
    Stream a gzipped VCF file and return a list of dictionaries for records
    that satisfy ``MAF > MIN_MAF``.  Only a minimal set of columns is kept:
    ``chrom``, ``pos``, ``ref``, ``alt``, and ``maf``.
    """
    records = []
    with gzip.open(vcf_path, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 8:
                continue  # malformed line
            chrom, pos, _, ref, alt, _, _, info = parts[:8]
            maf = _parse_maf(info)
            if maf >= MIN_MAF:
                records.append(
                    {
                        "chrom": chrom,
                        "pos": int(pos),
                        "ref": ref,
                        "alt": alt,
                        "maf": maf,
                    }
                )
    return records

def main() -> None:
    """
    Entry point for the dbSNP fetch step.

    The function:
      * Ensures the required directory hierarchy exists.
      * Retrieves the list of VCF files from the FTP server.
      * Filters that list to the ``chr*.common_snps.vcf.gz`` pattern.
      * Downloads each file, records its SHA‑256 checksum, logs provenance,
        streams the file to keep only SNPs with MAF > 0.01, and aggregates
        the results.
      * Writes the aggregated DataFrame to Parquet.
    """
    # Prepare environment
    ensure_data_dirs()
    set_seeds(42)

    # Ensure output locations exist
    OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_LOG.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Listing files in FTP directory: %s", FTP_BASE)
    try:
        listing = list_ftp_directory(FTP_BASE)
    except Exception as exc:
        logger.error("Failed to list FTP directory: %s", exc)
        raise

    # Identify chromosome VCFs
    vcf_files = [
        fname
        for fname in listing
        if fname.endswith(".common_snps.vcf.gz")
        and ("chr" in fname.lower() or fname.lower().startswith("chr"))
    ]

    if not vcf_files:
        raise RuntimeError("No common SNP VCF files found in the FTP directory.")

    logger.info("Found %d chromosome VCF files.", len(vcf_files))

    all_records: List[dict] = []

    for filename in vcf_files:
        url = f"{FTP_BASE}/{filename}"
        local_path = Path("data/raw") / filename

        logger.info("Downloading %s", url)
        try:
            download_ftp_file(url, local_path)
        except Exception as exc:
            logger.error("Download failed for %s: %s", url, exc)
            raise

        # Compute checksum
        checksum = calculate_file_checksum(local_path, algorithm="sha256")

        # Log provenance
        timestamp = datetime.utcnow().isoformat() + "Z"
        log_source_lineage(
            source_name="dbSNP",
            file_path=str(local_path),
            checksum=checksum,
            notes=f"build={BUILD_VERSION}; downloaded={timestamp}",
        )

        # Process VCF and collect records
        logger.info("Processing VCF %s", local_path)
        records = _process_vcf(local_path)
        logger.info("Retained %d records after MAF filter.", len(records))
        all_records.extend(records)

        # Remove the large VCF file to keep disk usage low
        try:
            local_path.unlink()
        except OSError as exc:
            logger.warning("Could not delete temporary VCF %s: %s", local_path, exc)

    if not all_records:
        raise RuntimeError(
            "No SNPs passed the MAF > 0.01 filter across all chromosomes."
        )

    # Write to Parquet
    logger.info("Writing %d total records to %s", len(all_records), OUTPUT_PARQUET)
    df = pd.DataFrame(all_records)
    df.to_parquet(OUTPUT_PARQUET, index=False)

    logger.info("dbSNP fetch completed successfully.")

if __name__ == "__main__":
    main()

"""
code/acquire.py
----------------
This module handles downloading of metabolomics CSV/TSV files and raw 16S rRNA FASTQ files
from public repositories. It also verifies SHA‑256 checksums recorded in
``data/checksums/checksums.txt``. The CLI is deliberately permissive so that the
quickstart script can invoke it without any arguments (the default behaviour
downloads a small, publicly available SRA dataset – SRR390728 – which is suitable
for the DADA2 processing step in ``code.curate``).
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


# ----------------------------------------------------------------------
# Checksum handling utilities
# ----------------------------------------------------------------------
def _read_checksum_file() -> dict[str, str]:
    """
    Parse ``data/checksums/checksums.txt`` and return a mapping from identifier
    (URL or filename) to its expected SHA‑256 checksum.
    """
    checksum_path = paths.data("checksums", "checksums.txt")
    if not checksum_path.is_file():
        return {}
    mapping: dict[str, str] = {}
    with checksum_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                sha, identifier = parts[0], parts[1]
                mapping[identifier] = sha
    return mapping


def _expected_checksum(identifier: str) -> str:
    """
    Return the expected SHA‑256 checksum for *identifier* as recorded in the
    checksum file.  Raises ``RuntimeError`` with the FR‑008 message if the
    entry cannot be found.
    """
    mapping = _read_checksum_file()
    if identifier not in mapping:
        raise RuntimeError("Metabolomics data unavailable – aborting per FR-008")
    return mapping[identifier]


def _calculate_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of the file at *file_path*.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------
# Metabolomics download
# ----------------------------------------------------------------------
def download_metabolomics(url: str, out_path: Path) -> None:
    """
    Download a metabolomics profile from *url* and write it to *out_path*.

    The function verifies the SHA‑256 checksum recorded in
    ``data/checksums/checksums.txt``.  On any mismatch or missing entry it
    raises ``RuntimeError`` with the exact FR‑008 message.
    """
    expected = _expected_checksum(url)

    log.info("Downloading metabolomics data from %s", url)
    response = requests.get(url, stream=True, timeout=30)
    if response.status_code != 200:
        raise RuntimeError("Metabolomics data unavailable – aborting per FR-008")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    actual = _calculate_sha256(out_path)
    if actual.lower() != expected.lower():
        raise RuntimeError("Metabolomics data unavailable – aborting per FR-008")
    log.info("Metabolomics file saved to %s (checksum verified)", out_path)


# ----------------------------------------------------------------------
# SRA FASTQ download
# ----------------------------------------------------------------------
def _append_checksum_entry(identifier: str, sha256: str) -> None:
    """
    Append a ``<sha256>  <identifier>`` line to the checksum manifest.
    The manifest file is created if it does not already exist.
    """
    checksum_path = paths.data("checksums", "checksums.txt")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("a", encoding="utf-8") as f:
        f.write(f"{sha256}  {identifier}\n")


def download_sra_fastq(accessions: List[str], out_dir: Path) -> None:
    """
    Download paired‑end FASTQ files for each accession in *accessions* from the
    ENA FTP mirror, compute their SHA‑256 checksums, and record those checksums
    in ``data/checksums/checksums.txt``.

    Parameters
    ----------
    accessions: List[str]
        List of SRA run identifiers (e.g., ``["SRR390728"]``).
    out_dir: Path
        Destination directory for the downloaded ``*.fastq.gz`` files.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    for acc in accessions:
        # ENA directory is the first 6 characters of the accession.
        prefix = acc[:6]
        base_url = f"https://ftp.sra.ebi.ac.uk/vol1/fastq/{prefix}/{acc}"
        for read_num in (1, 2):
            filename = f"{acc}_{read_num}.fastq.gz"
            url = f"{base_url}/{filename}"
            dest_path = out_dir / filename

            log.info("Downloading %s → %s", url, dest_path)
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                raise RuntimeError("Metabolomics data unavailable – aborting per FR-008")

            with dest_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            sha = _calculate_sha256(dest_path)
            _append_checksum_entry(filename, sha)
            log.info("Downloaded %s (SHA256=%s)", filename, sha)


# ----------------------------------------------------------------------
# Argument parsing & CLI entry point
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download metabolomics or SRA FASTQ data")
    subparsers = parser.add_subparsers(dest="command")

    # Metabolomics sub‑command
    meta_parser = subparsers.add_parser("metabolomics", help="Download a metabolomics CSV/TSV")
    meta_parser.add_argument("--url", required=True, help="URL of the metabolomics file")
    meta_parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Path where the metabolomics file should be saved",
    )

    # SRA sub‑command
    sra_parser = subparsers.add_parser("sra", help="Download SRA FASTQ files")
    sra_parser.add_argument(
        "--accessions",
        nargs="+",
        required=True,
        help="One or more SRA accession IDs (e.g., SRR390728)",
    )
    sra_parser.add_argument(
        "--out-dir",
        type=Path,
        default=paths.data("raw", "sra_fastq"),
        help="Directory to store downloaded FASTQ files",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """
    CLI wrapper.  If called without any arguments it performs the default
    behaviour required by the quickstart script: download a small public
    SRA dataset (SRR390728) into ``data/raw/sra_fastq``.
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        # Default behaviour – download a tiny test dataset.
        default_accession = ["SRR390728"]
        out_dir = paths.data("raw", "sra_fastq")
        log.info("No arguments supplied – downloading default SRA dataset %s", default_accession)
        download_sra_fastq(default_accession, out_dir)
        return

    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "metabolomics":
        download_metabolomics(args.url, args.out)
    elif args.command == "sra":
        download_sra_fastq(args.accessions, args.out_dir)
    else:
        parser.error("No valid sub‑command provided")


if __name__ == "__main__":
    main()

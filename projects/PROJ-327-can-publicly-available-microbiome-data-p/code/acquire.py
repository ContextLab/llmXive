"""
acquire.py
==========
Utilities for acquiring external data assets needed by the pipeline.

This module provides two public functions:

- ``download_metabolomics(url: str, out_path: Path) -> None``
- ``download_sra_fastq(accessions: List[str], out_dir: Path) -> None``

The former downloads a metabolomics TSV/CSV file and verifies its SHA‑256
checksum against the entry recorded in ``data/checksums/checksums.txt``.
The latter downloads raw 16S rRNA FASTQ files (paired reads) from NCBI
SRA given a list of accession identifiers, writes them to ``out_dir`` as
``{accession}_1.fastq.gz`` and ``{accession}_2.fastq.gz`` (if both pairs
exist), and records SHA‑256 checksums for each downloaded file in the
same checksum manifest.

Both functions raise a ``RuntimeError`` with the exact FR‑008 message
``Metabolomics data unavailable – aborting per FR-008`` when any step
fails (download error, missing checksum entry, checksum mismatch, etc.).
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List

import requests

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions (shared)
# ----------------------------------------------------------------------

def _read_checksum_file() -> dict[str, str]:
    """
    Parse ``data/checksums/checksums.txt`` and return a mapping from URL
    (or filename) to its expected SHA‑256 checksum.

    The checksum file is expected to contain lines of the form::

        <sha256>  <url-or-filename>

    Blank lines and lines starting with ``#`` are ignored.
    """
    checksum_path = paths.data("checksums", "checksums.txt")
    if not checksum_path.is_file():
        raise RuntimeError(
            "Metabolomics data unavailable – aborting per FR-008"
        )

    mapping: dict[str, str] = {}
    with checksum_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            # Guard against malformed lines – we require at least two tokens.
            if len(parts) < 2:
                continue
            checksum, identifier = parts[0], parts[1]
            mapping[identifier] = checksum
    return mapping


def _expected_checksum(identifier: str) -> str:
    """
    Return the expected SHA‑256 checksum for *identifier* as recorded in the
    checksum file.  Raises ``RuntimeError`` with the FR‑008 message if the
    entry cannot be found.
    """
    checksums = _read_checksum_file()
    try:
        return checksums[identifier]
    except KeyError as exc:
        raise RuntimeError(
            "Metabolomics data unavailable – aborting per FR-008"
        ) from exc


def _calculate_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of the file at *file_path*.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


# ----------------------------------------------------------------------
# Public API – Metabolomics
# ----------------------------------------------------------------------

def download_metabolomics(url: str, out_path: Path) -> None:
    """
    Download a metabolomics profile from *url* and write it to ``out_path``.

    The function performs the following steps:

    1. Retrieve the expected SHA‑256 checksum from
       ``data/checksums/checksums.txt``.  If the entry is missing, raise
       ``RuntimeError`` with the exact FR‑008 message.
    2. Issue an HTTP GET request (streamed).  If the request fails (status
       code != 200), raise the same ``RuntimeError``.
    3. Write the response body to ``out_path`` (creating parent directories
       as needed).
    4. Compute the SHA‑256 checksum of the downloaded file and compare it
       to the expected value.  On mismatch, raise the same ``RuntimeError``.

    Parameters
    ----------
    url: str
        The HTTP(S) URL pointing to the metabolomics TSV/CSV file.
    out_path: pathlib.Path
        Destination path for the downloaded file.  The caller is expected
        to point this under ``data/raw/metabolomics/`` but the function
        does not enforce a specific directory layout.

    Raises
    ------
    RuntimeError
        If the download fails, the checksum entry is missing, or the
        checksum verification fails.  The error message is exactly:

        ``Metabolomics data unavailable – aborting per FR-008``
    """
    log.info("Starting download of metabolomics data from %s", url)

    # Step 1: obtain expected checksum
    expected = _expected_checksum(url)
    log.debug("Expected SHA‑256 checksum: %s", expected)

    # Step 2: perform HTTP request
    try:
        response = requests.get(url, stream=True, timeout=30)
    except Exception as exc:
        log.error("HTTP request failed: %s", exc)
        raise RuntimeError(
            "Metabolomics data unavailable – aborting per FR-008"
        ) from exc

    if response.status_code != 200:
        log.error(
            "Failed to download file: HTTP %s", response.status_code
        )
        raise RuntimeError(
            "Metabolomics data unavailable – aborting per FR-008"
        )

    # Ensure parent directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 3: write to disk
    try:
        with out_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep‑alive chunks
                    f.write(chunk)
    except Exception as exc:
        log.error("Failed to write downloaded file: %s", exc)
        raise RuntimeError(
            "Metabolomics data unavailable – aborting per FR-008"
        ) from exc

    # Step 4: verify checksum
    actual = _calculate_sha256(out_path)
    log.debug("Actual SHA‑256 checksum: %s", actual)
    if actual.lower() != expected.lower():
        log.error(
            "Checksum mismatch for %s: expected %s, got %s",
            out_path,
            expected,
            actual,
        )
        raise RuntimeError(
            "Metabolomics data unavailable – aborting per FR-008"
        )

    log.info("Successfully downloaded and verified %s", out_path)


# ----------------------------------------------------------------------
# Public API – SRA FASTQ download
# ----------------------------------------------------------------------

def download_sra_fastq(accessions: List[str], out_dir: Path) -> None:
    """
    Download raw 16S rRNA FASTQ files for each SRA accession in *accessions*.

    For each accession the function attempts to download the paired‑end
    FASTQ files (``{accession}_1.fastq.gz`` and ``{accession}_2.fastq.gz``)
    from a public FTP mirror (ENA).  The URLs are constructed using the
    ENA pattern::

        https://ftp.sra.ebi.ac.uk/vol1/fastq/<first three letters>/<accession>/<accession>_1.fastq.gz
        https://ftp.sra.ebi.ac.uk/vol1/fastq/<first three letters>/<accession>/<accession>_2.fastq.gz

    The function:

    1. Ensures ``out_dir`` exists.
    2. For each accession, builds the two URLs and streams each file to
       ``out_dir/{accession}_1.fastq.gz`` and ``out_dir/{accession}_2.fastq.gz``.
    3. Computes the SHA‑256 checksum of each downloaded file.
    4. Appends a line ``<sha256>  <filename>`` to the project's checksum
       manifest (``data/checksums/checksums.txt``).  The *identifier* stored
       is the filename (e.g., ``SRR123456_1.fastq.gz``) so that later
       validation can locate the entry.
    5. If any HTTP request fails (status != 200) or a checksum cannot be
       written, the function raises ``RuntimeError`` with the exact FR‑008
       message.

    Parameters
    ----------
    accessions: List[str]
        List of SRA run accession identifiers (e.g., ``["SRR123456"]``).
    out_dir: pathlib.Path
        Directory where the downloaded FASTQ files will be placed.

    Raises
    ------
    RuntimeError
        If a download fails, a checksum entry is missing, or any other
        step cannot be completed.  The message is exactly:

        ``Metabolomics data unavailable – aborting per FR-008``
    """
    log.info("Starting SRA FASTQ download for %d accession(s)", len(accessions))

    # Ensure the output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)

    # Path to the shared checksum manifest
    checksum_path = paths.data("checksums", "checksums.txt")
    # Ensure the manifest file exists so that we can append to it
    if not checksum_path.is_file():
        # Create an empty file if it does not exist yet
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        checksum_path.touch()

    for acc in accessions:
        # Derive the first three characters after the prefix (e.g., "SRR")
        # This follows the ENA directory layout.
        prefix = acc[:3]  # e.g., "SRR"
        # Construct URLs for paired reads
        url_template = (
            "https://ftp.sra.ebi.ac.uk/vol1/fastq/{prefix}/{acc}/{acc}_{pair}.fastq.gz"
        )
        for pair in ("1", "2"):
            url = url_template.format(prefix=prefix, acc=acc, pair=pair)
            filename = f"{acc}_{pair}.fastq.gz"
            out_path = out_dir / filename

            log.debug("Downloading %s -> %s", url, out_path)

            try:
                response = requests.get(url, stream=True, timeout=30)
            except Exception as exc:
                log.error("HTTP request failed for %s: %s", url, exc)
                raise RuntimeError(
                    "Metabolomics data unavailable – aborting per FR-008"
                ) from exc

            if response.status_code != 200:
                log.error(
                    "Failed to download %s: HTTP %s", url, response.status_code
                )
                raise RuntimeError(
                    "Metabolomics data unavailable – aborting per FR-008"
                )

            # Write the streamed content to disk
            try:
                with out_path.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            except Exception as exc:
                log.error("Failed to write %s: %s", out_path, exc)
                raise RuntimeError(
                    "Metabolomics data unavailable – aborting per FR-008"
                ) from exc

            # Compute checksum and record it
            checksum = _calculate_sha256(out_path)
            log.debug("Checksum for %s: %s", out_path, checksum)

            # Append to the checksum file (one line per file)
            with checksum_path.open("a", encoding="utf-8") as chk_f:
                chk_f.write(f"{checksum}  {filename}\n")

    log.info("Completed SRA FASTQ download for all accessions")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Download a metabolomics TSV/CSV file and verify its SHA‑256 "
            "checksum against the project's checksum manifest."
        )
    )
    parser.add_argument(
        "--url",
        required=True,
        help="HTTP(S) URL of the metabolomics file to download.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help=(
            "Destination path for the downloaded file.  The parent "
            "directory will be created if missing."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """
    CLI wrapper that parses arguments and invokes ``download_metabolomics``.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        download_metabolomics(args.url, args.out)
    except RuntimeError as exc:
        # Propagate the exact message to the console and exit with non‑zero.
        log.error(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()

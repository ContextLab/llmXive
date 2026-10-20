"""
Real-data ingestion from NASA CDAWeb via pyspedas.

Fetches ACE SWICS composition, WIND SMS/STICS composition, and OMNI
hourly bulk/IMF/indices data, preserves the raw CDF files UNCHANGED
under data/raw/, and writes SHA-256 checksums to
data/raw/checksums.yaml.

The loader FAILS LOUDLY on any fetch failure (ConnectionError /
RuntimeError). There is no synthetic fallback anywhere in this module.
"""
import argparse
import hashlib
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import List

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _validate_date(date_str: str) -> str:
    """Validate a YYYY-MM-DD date string, raising loudly on bad input."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(
            f"Invalid date '{date_str}' (expected YYYY-MM-DD): {e}"
        ) from e
    return date_str


def _fetch_cdf_files(datatype: str, source_name: str, trange: List[str]) -> List[Path]:
    """
    Download the raw CDF files for one source via pyspedas.cdaweb.

    Uses ``downloadonly=True`` so the loader returns the list of
    downloaded local file paths without loading them into tplot.
    Raises ConnectionError on any fetch failure — never a fallback.
    """
    log.info(
        "Fetching %s via pyspedas.cdaweb for %s..%s",
        source_name,
        trange[0],
        trange[1],
    )
    try:
        # Lazy import to keep the module importable without pyspedas being present at import time.
        from pyspedas import cdaweb  # type: ignore
    except Exception as e:
        # Convert import problems into a runtime‑type error expected by the tests.
        raise RuntimeError(
            "pyspedas is required for real-data ingestion but could not be imported."
        ) from e

    try:
        # pyspedas.cdaweb returns a list of file paths (strings)
        files = cdaweb.cdaweb(trange=trange, datatype=datatype, downloadonly=True)
    except Exception as e:
        raise ConnectionError(
            f"Failed to fetch {source_name} from CDAWeb via pyspedas: {e}"
        ) from e

    if not files:
        raise RuntimeError(
            f"pyspedas.cdaweb returned an empty file list for {source_name}; "
            "the CDAWeb fetch did not succeed"
        )
    cdfs = [Path(f) for f in files if str(f).lower().endswith(".cdf")]
    if not cdfs:
        raise RuntimeError(
            f"No CDF files downloaded for {source_name}; loader returned {files!r}"
        )
    for f in cdfs:
        if not f.exists():
            raise RuntimeError(f"Downloaded file missing on disk: {f}")
    log.info("Fetched %d raw CDF file(s) for %s", len(cdfs), source_name)
    return cdfs


def preserve_raw_files(files: List[Path], target_dir: Path) -> int:
    """
    Copy raw files UNCHANGED (byte-for-byte, shutil.copy2) from the
    pyspedas cache into the project's data/raw directory.

    Returns the number of files preserved; raises RuntimeError if
    nothing could be preserved.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    files_copied = 0
    for item in files:
        item = Path(item)
        if not item.is_file():
            raise RuntimeError(f"Expected raw file {item} is missing")
        shutil.copy2(item, target_dir / item.name)
        files_copied += 1
    if files_copied == 0:
        raise RuntimeError(
            f"No files preserved into {target_dir}; download must have failed"
        )
    log.info("Preserved %d raw file(s) unchanged in %s", files_copied, target_dir)
    return files_copied


def download_and_preserve(start: str = "2000-01-01", end: str = "2020-12-31") -> dict:
    """
    Main routine: fetch real data from CDAWeb via pyspedas and save
    raw artifacts plus SHA-256 checksums.

    Sources (all real, NASA CDAWeb):
      - OMNI hourly (bulk parameters, IMF, Dst, Kp)
      - ACE SWICS ion composition (H, He, C, O, Fe charge-state fluxes)
      - WIND SMS/STICS composition

    Raises ConnectionError/RuntimeError on any failure. No synthetic
    fallback exists.
    """
    start = _validate_date(start)
    end = _validate_date(end)
    trange = [start, end]

    raw_root = paths.data("raw")
    raw_ace = raw_root / "ace_swics"
    raw_wind = raw_root / "wind_sms"
    raw_omni = raw_root / "omni"
    checksum_file = raw_root / "checksums.yaml"

    # 1. OMNI hourly data
    omni_files = _fetch_cdf_files("omni_h0", "OMNI hourly", trange)
    preserve_raw_files(omni_files, raw_omni)

    # 2. ACE SWICS composition data
    ace_files = _fetch_cdf_files("ace_swics_1min", "ACE SWICS composition", trange)
    preserve_raw_files(ace_files, raw_ace)

    # 3. WIND SMS/STICS composition data
    wind_files = _fetch_cdf_files("wind_sms_1m", "WIND SMS/STICS composition", trange)
    preserve_raw_files(wind_files, raw_wind)

    # 4. Generate SHA-256 checksums for every preserved raw file
    log.info("Generating SHA-256 checksums for all raw files...")
    checksums = {}
    for folder in [raw_ace, raw_wind, raw_omni]:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                rel_path = file.relative_to(raw_root)
                checksums[str(rel_path)] = compute_sha256(file)

    if not checksums:
        raise RuntimeError("No raw files found to checksum; ingestion failed")

    with checksum_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(checksums, f, sort_keys=True)

    log.info(
        "Checksums for %d raw files written to %s",
        len(checksums),
        checksum_file,
    )
    log.info(
        "Real-data ingestion complete for period %s..%s (%d raw files preserved unchanged)",
        start,
        end,
        len(ace_files) + len(wind_files) + len(omni_files),
    )
    return {
        "start": start,
        "end": end,
        "n_omni_files": len(omni_files),
        "n_ace_files": len(ace_files),
        "n_wind_files": len(wind_files),
        "checksums_file": str(checksum_file),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download REAL solar-wind/geomagnetic data from NASA CDAWeb via pyspedas (no synthetic fallback)."
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2000-01-01",
        help="Start date YYYY-MM-DD",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2020-12-31",
        help="End date YYYY-MM-DD",
    )
    args = parser.parse_args()
    summary = download_and_preserve(start=args.start, end=args.end)
    log.info("Ingestion summary: %s", summary)


if __name__ == "__main__":
    main()
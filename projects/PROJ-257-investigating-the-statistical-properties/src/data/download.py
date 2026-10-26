"""
src/data/download.py

Download GWTC‑1 and GWTC‑2 posterior‑sample HDF5 archives from Zenodo,
verify their integrity, and write a ``checksums.json`` manifest.
The implementation now robustly handles records that provide the data
as a compressed ``.zip`` archive (the real GWTC releases are zipped).
After download the archive is unpacked and the contained HDF5 file is
placed at the expected ``data/raw/<target_name>`` location.  The checksum
recorded in the manifest corresponds to the extracted HDF5 file, not the
intermediate zip.
"""

import json
import time
import zipfile
from pathlib import Path
from typing import List, Tuple

import requests
from llmxive_toolkit import paths, get_logger

# Local imports
from src.utils.checksum import compute_file_hash

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – list of DOIs and the expected target filenames
# ----------------------------------------------------------------------
DATASETS: List[Tuple[str, str]] = [
    ("10.5281/zenodo.3966973", "gwtc1.h5"),
    ("10.5281/zenodo.3966974", "gwtc2.h5"),
]

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _doi_to_record_id(doi: str) -> str:
    """
    Convert a Zenodo DOI to the numerical record identifier used by the
    Zenodo API.
    """
    try:
        return doi.rsplit(".", 1)[-1]
    except Exception as exc:
        raise RuntimeError(
            f"Failed to extract record ID from DOI '{doi}': {exc}"
        ) from exc


def _select_file_info(meta: dict) -> Tuple[str, str]:
    """
    From a Zenodo record metadata dictionary, select a file to download.

    The official GWTC releases are distributed as a ``.zip`` containing a
    single HDF5 file.  The selector therefore prefers any entry whose
    ``key`` ends with ``.h5`` or ``.hdf5``; if none are found it falls back
    to the first available file (typically the zip archive).
    """
    files = meta.get("files", [])
    # First, look for explicit HDF5 files.
    for entry in files:
        fname = entry.get("key", "")
        if fname.lower().endswith((".h5", ".hdf5")):
            url = entry.get("links", {}).get("download")
            if not url:
                raise RuntimeError(
                    f"Download link missing for HDF5 file '{fname}'"
                )
            return fname, url

    # Fallback: return the first file (e.g. a .zip archive)
    if files:
        entry = files[0]
        fname = entry.get("key", "")
        url = entry.get("links", {}).get("download")
        if not url:
            raise RuntimeError(
                f"Download link missing for file '{fname}'"
            )
        return fname, url

    raise RuntimeError("No files listed in Zenodo record metadata")


def _is_hdf5(file_path: Path) -> bool:
    """
    Very lightweight check that the file starts with the HDF5 magic header.
    """
    try:
        with file_path.open("rb") as f:
            magic = f.read(8)
        return magic == b"\x89HDF\r\n\x1a\n"
    except Exception as exc:
        log.error(
            "Failed to read file %s for HDF5 validation: %s", file_path, exc
        )
        return False


def _extract_hdf5_from_zip(zip_path: Path, target_path: Path) -> None:
    """
    Extract the first HDF5 file found inside ``zip_path`` and place it at
    ``target_path``.  The zip archive is removed after successful extraction.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find the first HDF5 member
        hdf5_name = None
        for member in zf.namelist():
            if member.lower().endswith((".h5", ".hdf5")):
                hdf5_name = member
                break
        if hdf5_name is None:
            raise RuntimeError(
                f"No HDF5 file found inside zip archive {zip_path}"
            )
        # Extract to a temporary location then move to the final target
        tmp_extracted = zip_path.with_suffix(".extracted")
        tmp_extracted.mkdir(parents=True, exist_ok=True)
        zf.extract(hdf5_name, path=tmp_extracted)
        extracted_path = tmp_extracted / hdf5_name
        # Ensure the extracted file is indeed HDF5
        if not _is_hdf5(extracted_path):
            raise RuntimeError(
                f"Extracted file {extracted_path} is not a valid HDF5 archive."
            )
        # Move the extracted file to the desired location
        extracted_path.rename(target_path)
        # Clean‑up temporary directory and the original zip
        try:
            # Remove extracted directory recursively
            for child in tmp_extracted.rglob("*"):
                if child.is_file():
                    child.unlink()
            tmp_extracted.rmdir()
        except Exception:
            pass
    zip_path.unlink(missing_ok=True)


def _download_with_retries(url: str, dest: Path, max_retries: int = 3) -> None:
    """
    Download a file from ``url`` to ``dest`` with exponential back‑off
    (1 s, 2 s, 4 s).  After download the function validates the result:
    if the file is a zip archive it is unpacked to obtain the HDF5 payload;
    otherwise the file must already be a valid HDF5 file.
    """
    for attempt in range(max_retries + 1):
        try:
            log.info("Downloading %s (attempt %d)", url, attempt + 1)
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)

            tmp_path = dest.with_suffix(dest.suffix + ".part")
            with open(tmp_path, "wb") as fh:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
            tmp_path.rename(dest)
            log.info("Download succeeded: %s -> %s", url, dest)

            # If we received a zip archive, unpack it to obtain the HDF5 file.
            if dest.suffix.lower() == ".zip":
                _extract_hdf5_from_zip(dest, dest.with_suffix(".h5"))
            # After any unpacking, ensure the final file is HDF5.
            final_path = dest.with_suffix(".h5") if dest.suffix.lower() == ".zip" else dest
            if not _is_hdf5(final_path):
                raise RuntimeError(f"File {final_path} is not a valid HDF5 archive.")
            return
        except Exception as exc:
            if attempt >= max_retries:
                raise RuntimeError(
                    f"Failed to download {url} after {max_retries} retries: {exc}"
                ) from exc
            delay = 2 ** attempt  # 1, 2, 4
            log.warning(
                "Download attempt %d/%d failed (%s). Retrying in %d s...",
                attempt + 1,
                max_retries + 1,
                exc,
                delay,
            )
            time.sleep(delay)


# ----------------------------------------------------------------------
# Core download routine
# ----------------------------------------------------------------------
def download_all() -> dict:
    """
    Download the GWTC datasets, verify they are genuine HDF5 files,
    compute SHA‑256 hashes, and write a ``checksums.json`` manifest
    under ``data/raw/``.
    """
    downloaded = {}
    for doi, target_name in DATASETS:
        record_id = _doi_to_record_id(doi)
        meta_url = f"https://zenodo.org/api/records/{record_id}"
        log.info(
            "Fetching Zenodo metadata for record %s (DOI %s)",
            record_id,
            doi,
        )
        resp = requests.get(meta_url, timeout=60)
        resp.raise_for_status()
        meta = resp.json()

        fname, download_url = _select_file_info(meta)
        if fname != target_name:
            log.warning(
                "Expected filename %s but Zenodo returned %s; proceeding with %s",
                target_name,
                fname,
                fname,
            )

        dest_path = paths.data("raw", target_name)
        _download_with_retries(download_url, dest_path)

        # Compute checksum of the *final* HDF5 file (dest_path)
        sha256 = compute_file_hash(str(dest_path), algorithm="sha256")
        log.info("SHA‑256 for %s: %s", target_name, sha256)
        downloaded[target_name] = dest_path

    checksums_path = paths.data("raw", "checksums.json")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        name: compute_file_hash(str(p), algorithm="sha256")
        for name, p in downloaded.items()
    }
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log.info("Wrote checksums manifest to %s", checksums_path)

    return downloaded


def main() -> None:
    """CLI entry point."""
    try:
        download_all()
        log.info(
            "All GWTC datasets downloaded and verified successfully."
        )
    except Exception as exc:
        log.error("Data download failed: %s", exc)
        raise

if __name__ == "__main__":
    main()

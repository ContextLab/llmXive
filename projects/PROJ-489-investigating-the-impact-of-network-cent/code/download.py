"""
Download Sleep‑EDF dataset from PhysioNet using MNE‑Python.

- Downloads up to ``n_subjects`` recordings (each night counts as a separate recording).
- Verifies each downloaded file by attempting to read it with MNE.
- Computes SHA‑256 checksums for successfully read files.
- Writes a tab‑separated log ``download_log.txt`` containing:
    <filename>\t<sha256_checksum>
  Corrupted or unreadable files are logged with the prefix ``ERROR`` and are removed.
- Raises on any network‑level failure; corrupted files are *skipped* but do not abort the whole run.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Tuple

import mne
from mne.datasets import sleep_physionet

from integrity import calculate_file_checksum
from config_utils import load_config

# Configure module‑level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


def _download_one_record(subject: int, night: int, dest_dir: Path) -> Path:
    """
    Download a single subject/night recording using MNE's fetch_data.

    Parameters
    ----------
    subject : int
        Subject identifier (0‑19 for the Sleep‑EDF dataset).
    night : int
        Night number (1 or 2).
    dest_dir : Path
        Directory where the raw EDF file will be placed.

    Returns
    -------
    Path
        Path to the downloaded EDF file (already copied into ``dest_dir``).

    Raises
    ------
    Exception
        Propagates any network‑level errors from ``fetch_data``.
    """
    # ``fetch_data`` returns a list of file paths; for a single subject/night it
    # should contain exactly one element.
    fetched = sleep_physionet.fetch_data(
        subjects=[subject],
        recording="sleep-edf",
        path=str(dest_dir),
        night=night,
        verbose=False,
    )
    if not fetched:
        raise RuntimeError(f"No files returned for subject {subject} night {night}")

    src_path = Path(fetched[0])
    dst_path = dest_dir / src_path.name

    # Copy to our dedicated raw directory if not already present
    if not dst_path.exists():
        shutil.copy2(src_path, dst_path)

    return dst_path


def download_sleep_edf(output_dir: str = "data/raw/", n_subjects: int = 30) -> Tuple[List[Path], List[Tuple[str, str]]]:
    """
    Download ``n_subjects`` Sleep‑EDF recordings.

    Parameters
    ----------
    output_dir : str
        Directory where raw EDF files will be stored.
    n_subjects : int
        Number of *recordings* (each night counts as one) to download.
        The function will request both nights for each subject until the
        target count is reached (maximum 40 recordings for the full set).

    Returns
    -------
    successful_paths : list[Path]
        Paths of files that passed integrity verification.
    error_entries : list[tuple[str, str]]
        List of (filename, error_message) for files that were corrupted
        or could not be read.
    """
    base_path = Path(output_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    successful_paths: List[Path] = []
    error_entries: List[Tuple[str, str]] = []
    log_lines: List[str] = []

    max_subjects = 20  # Sleep‑EDF provides subjects 0‑19
    recordings_downloaded = 0

    for subject in range(max_subjects):
        for night in (1, 2):
            if recordings_downloaded >= n_subjects:
                break

            try:
                logger.info(f"Fetching subject {subject}, night {night}...")
                edf_path = _download_one_record(subject, night, base_path)

                # Verify that MNE can read the file
                try:
                    _ = mne.io.read_raw_edf(edf_path, preload=False, verbose=False)
                except Exception as exc:
                    logger.warning(f"Corrupted EDF detected ({edf_path.name}): {exc}")
                    error_entries.append((edf_path.name, str(exc)))
                    edf_path.unlink(missing_ok=True)
                    log_lines.append(f"ERROR\t{edf_path.name}\t{exc}")
                    continue

                # Compute SHA‑256 checksum
                checksum = calculate_file_checksum(edf_path, algorithm="sha256")
                successful_paths.append(edf_path)
                log_lines.append(f"{edf_path.name}\t{checksum}")
                recordings_downloaded += 1

            except Exception as e:
                # Any network‑level or fetch‑related exception propagates upward
                logger.error(f"Failed to fetch subject {subject}, night {night}: {e}")
                raise

        if recordings_downloaded >= n_subjects:
            break

    # Write the log file (both successful and error entries)
    log_path = base_path / "download_log.txt"
    with open(log_path, "w", encoding="utf-8") as log_f:
        for line in log_lines:
            log_f.write(line + "\n")

    logger.info(
        f"Download completed: {len(successful_paths)} files verified, {len(error_entries)} errors."
    )
    return successful_paths, error_entries


def main() -> None:
    """
    Entry point used by ``python code/download.py``.

    Loads configuration (if present) to obtain custom output directory
    and subject count, then calls :func:`download_sleep_edf`.
    """
    cfg = load_config()
    raw_dir = cfg.get("paths", {}).get("raw_data", "data/raw/")
    n_subj = cfg.get("statistics", {}).get("min_sample_size", 30)  # N_MIN

    # Ensure we request at least the minimum required number of recordings.
    download_sleep_edf(output_dir=raw_dir, n_subjects=n_subj)


if __name__ == "__main__":
    main()

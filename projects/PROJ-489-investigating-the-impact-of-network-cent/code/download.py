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
# The MNE API for the Sleep‑EDF dataset changed in recent versions.
# Older versions expose ``fetch_data`` directly under ``mne.datasets.sleep_physionet``.
# Newer versions expose it under the ``age`` submodule.
# We support both by probing the attribute at runtime.
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


def _fetch_sleep_data(
    subjects: List[int],
    recordings: str,
    path: Path,
    night: int,
) -> List[Path]:
    """
    Wrapper around the MNE Sleep‑EDF fetch function that adapts to the
    installed MNE version.

    Parameters
    ----------
    subjects : List[int]
        Subject identifiers.
    recordings : str
        Recording type (e.g., ``"sleep-edf"``).
    path : Path
        Destination directory for the downloaded files.
    night : int
        Night number (1 or 2).

    Returns
    -------
    List[Path]
        List of file paths returned by the underlying MNE fetch routine.
    """
    # Newer MNE versions expose ``fetch_data`` under ``sleep_physionet.age``.
    # Older versions expose it directly under ``sleep_physionet``.
    fetch_func = getattr(sleep_physionet, "fetch_data", None)

    if fetch_func is None:
        # Try the submodule ``age``.
        age_mod = getattr(sleep_physionet, "age", None)
        if age_mod is None:
            raise AttributeError(
                "MNE's sleep_physionet dataset does not expose a fetch_data function."
            )
        fetch_func = getattr(age_mod, "fetch_data", None)
        if fetch_func is None:
            raise AttributeError(
                "MNE's sleep_physionet.age submodule does not expose fetch_data."
            )

    # Call the discovered fetch function.
    return fetch_func(
        subjects=subjects,
        recordings=recordings,
        path=str(path),
        night=night,
        verbose=False,
    )


def download_sleep_edf(output_dir: str = "data/raw/", n_subjects: int = 30) -> Tuple[List[Path], List[Tuple[str, str]]]:
    """
    Download ``n_subjects`` Sleep‑EDF recordings.

    Parameters
    ----------
    output_dir : str
        Directory where raw EDF files will be stored.
    n_subjects : int
        Number of *recordings* (not unique subjects) to download.
        The function will request both nights for each subject until the target
        count is reached (maximum 40 recordings for the full Sleep‑EDF set).

    Returns
    -------
    successful_paths : list[Path]
        Paths of files that passed integrity verification.
    error_entries : list[tuple[str, str]]
        List of (filename, error_message) for files that were corrupted or could not be read.
    """
    base_path = Path(output_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Determine which subject/night combinations to fetch.
    # Sleep‑EDF contains 20 subjects (IDs 0‑19), each with two nights.
    # We generate a flat list of (subject, night) pairs and truncate
    # to the requested number of recordings.
    # ------------------------------------------------------------------
    max_subjects = 20
    subject_night_pairs = [(subj, night) for subj in range(max_subjects) for night in (1, 2)]
    selected_pairs = subject_night_pairs[:n_subjects]

    successful_paths: List[Path] = []
    error_entries: List[Tuple[str, str]] = []

    log_lines: List[str] = []

    for subj, night in selected_pairs:
        try:
            logger.info(f"Fetching subject {subj}, night {night}...")
            fetched_files = _fetch_sleep_data(
                subjects=[subj],
                recordings="sleep-edf",
                path=base_path,
                night=night,
            )

            for src_path in fetched_files:
                src_path = Path(src_path)
                dst_path = base_path / src_path.name

                # Copy to our dedicated raw directory (if not already present)
                if not dst_path.exists():
                    shutil.copy2(src_path, dst_path)

                # Verify the file can be opened by MNE
                try:
                    _ = mne.io.read_raw_edf(dst_path, preload=False, verbose=False)
                except Exception as exc:
                    logger.warning(f"Corrupted EDF detected ({dst_path.name}): {exc}")
                    error_entries.append((dst_path.name, str(exc)))
                    # Remove the bad file so it does not remain in the raw folder
                    dst_path.unlink(missing_ok=True)
                    log_lines.append(f"ERROR\\t{dst_path.name}\\t{exc}")
                    continue

                # Compute SHA‑256 checksum
                checksum = calculate_file_checksum(dst_path, algorithm="sha256")
                successful_paths.append(dst_path)
                log_lines.append(f"{dst_path.name}\\t{checksum}")

        except Exception as e:
            # Any network‑level or fetch‑related exception propagates upward
            logger.error(f"Failed to fetch subject {subj}, night {night}: {e}")
            raise

    # Write the log file (both successful and error entries)
    log_path = base_path / "download_log.txt"
    with open(log_path, "w", encoding="utf-8") as log_f:
        for line in log_lines:
            log_f.write(line + "\n")

    logger.info(f"Download completed: {len(successful_paths)} files verified, {len(error_entries)} errors.")
    return successful_paths, error_entries


def main() -> None:
    """
    Entry point used by ``python code/download.py``.

    Loads configuration (if present) to obtain custom output directory
    and subject count, then calls :func:`download_sleep_edf`.
    """
    # Load configuration – defaults are defined in ``code/config.yaml``.
    cfg = load_config()
    raw_dir = cfg.get("paths", {}).get("raw_data", "data/raw/")
    n_subj = cfg.get("statistics", {}).get("min_sample_size", 30)  # use the N_MIN value

    # Ensure we request at least the minimum required number of recordings.
    # The Sleep‑EDF dataset provides 40 recordings total, so the request is safe.
    download_sleep_edf(output_dir=raw_dir, n_subjects=n_subj)


if __name__ == "__main__":
    main()

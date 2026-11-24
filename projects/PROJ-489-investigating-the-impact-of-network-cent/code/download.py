import logging
import shutil
import hashlib
from pathlib import Path
from typing import List, Tuple
import mne
from mne.datasets.sleep_physionet import fetch_data

from integrity import calculate_file_checksum
from config_utils import load_config

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def _download_one_record(subject: int, night: int, dest_dir: Path) -> Path:
    """
    Download a single subject/night recording using MNE's fetch_data.
    """
    # Explicitly use the imported fetch_data function to avoid AttributeError
    fetched = fetch_data(
        subjects=[subject],
        recording="sleep-edf",
        path=str(dest_dir),
        night=night,
        verbose=False,
    )
    if not fetched:
        raise RuntimeError(f"No files returned for subject {subject} night {night}")

    # fetch_data returns a list of paths to the downloaded files in the MNE cache
    # We move the .edf file to our project's data/raw directory
    src_path = Path(fetched[0])
    dst_path = dest_dir / src_path.name

    if not dst_path.exists():
        shutil.copy2(src_path, dst_path)

    return dst_path

def download_sleep_edf(output_dir: str = "data/raw/", n_subjects: int = 30) -> Tuple[List[Path], List[Tuple[str, str]]]:
    """
    Download n_subjects Sleep-EDF recordings.
    """
    base_path = Path(output_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    successful_paths: List[Path] = []
    error_entries: List[Tuple[str, str]] = []
    log_lines: List[str] = []

    # Sleep-EDF Expanded has 100 subjects. 
    # We iterate until we have enough unique subjects with at least one valid recording.
    subjects_verified = 0
    
    for subject in range(1, 101):
        if subjects_verified >= n_subjects:
            break

        subject_had_valid_file = False
        for night in (1, 2):
            try:
                logger.info(f"Fetching subject {subject}, night {night}...")
                edf_path = _download_one_record(subject, night, base_path)

                # Verify file integrity by attempting to read the header
                try:
                    _ = mne.io.read_raw_edf(edf_path, preload=False, verbose=False)
                except Exception as exc:
                    logger.warning(f"Corrupted EDF detected ({edf_path.name}): {exc}")
                    error_entries.append((edf_path.name, str(exc)))
                    edf_path.unlink(missing_ok=True)
                    log_lines.append(f"ERROR\t{edf_path.name}\t{exc}")
                    continue

                # Compute SHA-256 checksum for the verified file
                checksum = calculate_file_checksum(edf_path, algorithm="sha256")
                successful_paths.append(edf_path)
                log_lines.append(f"{edf_path.name}\t{checksum}")
                subject_had_valid_file = True

            except Exception as e:
                # Network failures or MNE fetch errors raise loudly as per requirements
                logger.error(f"Critical failure fetching subject {subject}, night {night}: {e}")
                raise

        if subject_had_valid_file:
            subjects_verified += 1

    # Write log file
    log_path = base_path / "download_log.txt"
    with open(log_path, "w", encoding="utf-8") as log_f:
        for line in log_lines:
            log_f.write(line + "\n")

    logger.info(f"Download completed: {subjects_verified} subjects verified, {len(successful_paths)} files total, {len(error_entries)} errors.")
    return successful_paths, error_entries

def main() -> None:
    cfg = load_config()
    raw_dir = cfg.get("paths", {}).get("raw_data", "data/raw/")
    n_subj = cfg.get("statistics", {}).get("min_sample_size", 30)
    download_sleep_edf(output_dir=raw_dir, n_subjects=n_subj)

if __name__ == "__main__":
    main()
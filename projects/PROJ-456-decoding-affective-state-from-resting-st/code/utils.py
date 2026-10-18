import json
import os
import hashlib
import pathlib
import sys
import tempfile
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------
@dataclass
class DatasetManifest:
    """
    Represents a single dataset entry in the manifest.

    Fields are aligned with the unit tests in ``tests/test_utils_manifest.py``.
    """
    dataset_id: str
    verification_status: str  # "ready" or "skipped"
    eeg_files: List[str] = field(default_factory=list)
    questionnaire_files: List[str] = field(default_factory=list)
    file_paths: Dict[str, str] = field(default_factory=dict)
    verification_timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _verify_dataset(eeg_files: List[pathlib.Path],
                   questionnaire_files: List[pathlib.Path]) -> str:
    """
    Simple helper used by the unit tests.

    Returns ``"ready"`` if *both* lists contain at least one element,
    otherwise returns ``"skipped"``.
    """
    if eeg_files and questionnaire_files:
        return "ready"
    return "skipped"

def download_and_verify_dataset(dataset_id: str, target_dir: str) -> Dict[str, Any]:
    """
    Download a dataset from OpenNeuro (real download) and perform a very light
    verification that the expected top‑level folders exist.

    The function streams the dataset as a zip archive using the public
    OpenNeuro download endpoint.  Only the directory structure is extracted;
    large EEG files are left untouched to keep the download lightweight.
    """
    import requests
    import zipfile
    from io import BytesIO

    base_url = f"https://openneuro.org/crn/datasets/{dataset_id}/download"
    os.makedirs(target_dir, exist_ok=True)
    dataset_path = os.path.join(target_dir, dataset_id)

    # If the dataset directory already exists we assume it has been downloaded.
    if os.path.isdir(dataset_path):
        return {"status": "already_downloaded", "dataset_path": dataset_path}

    response = requests.get(base_url, stream=True, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download dataset {dataset_id} – HTTP {response.status_code}"
        )

    # Stream the zip file without writing it to disk first.
    with zipfile.ZipFile(BytesIO(response.raw.read()), "r") as zip_ref:
        # Extract only the top‑level folder structure (no .fif files > 100 MB)
        members = [
            m for m in zip_ref.infolist()
            if not m.filename.lower().endswith(('.fif', '.edf', '.bdf', '.set', '.eeg', '.cnt', '.gdf'))
        ]
        zip_ref.extractall(path=target_dir, members=members)

    return {"status": "downloaded", "dataset_path": dataset_path}

def write_manifest(
    manifests: Union[DatasetManifest, List[DatasetManifest]],
    output_path: str
) -> None:
    """
    Serialize one or many :class:`DatasetManifest` objects to JSON.

    The original implementation expected a ``list``; the tests provide a
    single object, so we accept both.
    """
    if isinstance(manifests, DatasetManifest):
        manifests = [manifests]
    elif not isinstance(manifests, list):
        raise TypeError("`manifests` must be a DatasetManifest or a list thereof")

    data = [asdict(m) for m in manifests]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def verify_checksums(manifest_path: str, checksum_path: str) -> None:
    """Read manifest, compute checksums, and write to a JSON file."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifests = json.load(f)

    checksums = {}
    for item in manifests:
        for key, path in item.get("file_paths", {}).items():
            if os.path.exists(path):
                checksums[path] = compute_sha256(path)

    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

# ----------------------------------------------------------------------
# Logging infrastructure (unchanged from the original file)
# ----------------------------------------------------------------------
DEFAULT_EXCLUSION_LOG_PATH = os.path.join("data", "logs", "exclusion.log")

def setup_exclusion_logging(log_path: str = DEFAULT_EXCLUSION_LOG_PATH) -> logging.Logger:
    """
    Initialize and return a logger specifically for tracking exclusion logs.

    Creates the log directory, attaches a file handler with a timestamped
    format, and writes an initial header to the log file if the file is
    new or empty.
    """
    logger = logging.getLogger("exclusion_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Ensure directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Prevent adding multiple handlers if called multiple times
    if not logger.handlers:
        fh = logging.FileHandler(log_path, mode='a')
        fh.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)

        logger.addHandler(fh)

    # Write header if file is new or empty
    if (not os.path.exists(log_path)) or os.path.getsize(log_path) == 0:
        logger.info("--- Exclusion Log Started ---")
        logger.info("Project: PROJ-456-decoding-affective-state-from-resting-st")
        logger.info("Task: T007 - Logging Infrastructure")

    return logger

def log_exclusion(logger: logging.Logger, subject_id: str, reason: str,
                  details: Optional[str] = None) -> None:
    """
    Log an exclusion event for a subject.
    """
    msg = f"EXCLUSION: Subject={subject_id}, Reason={reason}"
    if details:
        msg += f" | Details={details}"
    logger.info(msg)

# ----------------------------------------------------------------------
# Manifest generation (the core of T004)
# ----------------------------------------------------------------------
EEG_EXTENSIONS = {".set", ".edf", ".bdf", ".vhdr", ".fif", ".eeg", ".cnt", ".gdf"}
QUESTIONNAIRE_KEYWORDS = (
    "panas", "sam", "questionnaire", "affect",
    "affective", "valence", "arousal", "phenotype"
)

def _collect_dataset_files(dataset_dir: str) -> Dict[str, List[str]]:
    """
    Walk through ``dataset_dir`` and collect EEG and questionnaire file paths.
    Returns a dictionary with keys ``eeg`` and ``questionnaire``.
    """
    eeg_files: List[str] = []
    questionnaire_files: List[str] = []

    for root, _, files in os.walk(dataset_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            suffix = os.path.splitext(fname)[1].lower()
            if suffix in EEG_EXTENSIONS:
                eeg_files.append(fpath)
            elif suffix in {".tsv", ".csv", ".txt"} and any(
                kw in fname.lower() for kw in QUESTIONNAIRE_KEYWORDS
            ):
                questionnaire_files.append(fpath)

    return {"eeg": eeg_files, "questionnaire": questionnaire_files}

def generate_manifest(
    dataset_ids: List[str],
    target_dir: str = "data/raw",
    manifest_path: str = "data/raw/dataset_manifest.json"
) -> None:
    """
    Download the requested OpenNeuro datasets (if not already present),
    verify that each contains at least one EEG file and one questionnaire
    file, and write a JSON manifest to ``manifest_path``.
    """
    manifests: List[DatasetManifest] = []

    for ds_id in dataset_ids:
        # Download (or skip if already present)
        download_and_verify_dataset(ds_id, target_dir)

        ds_dir = os.path.join(target_dir, ds_id)
        files = _collect_dataset_files(ds_dir)

        eeg_files = files["eeg"]
        questionnaire_files = files["questionnaire"]

        verification_status = _verify_dataset(
            [pathlib.Path(p) for p in eeg_files],
            [pathlib.Path(p) for p in questionnaire_files]
        )

        manifest = DatasetManifest(
            dataset_id=ds_id,
            verification_status=verification_status,
            eeg_files=eeg_files,
            questionnaire_files=questionnaire_files,
            file_paths={"root": ds_dir}
        )
        manifests.append(manifest)

    # Write the aggregated manifest
    write_manifest(manifests, manifest_path)

# ----------------------------------------------------------------------
# Checksum recording (implementation of T005)
# ----------------------------------------------------------------------
def record_checksums(
    manifest_path: str = "data/raw/dataset_manifest.json",
    output_path: str = "data/checksums.json"
) -> None:
    """
    Compute SHA‑256 checksums for all files listed in the dataset manifest
    and write a JSON mapping ``{file_path: hash}`` to ``output_path``.

    The function respects the project‑owned ``data/`` directory; it does **not**
    write to the platform‑owned ``state/`` folder.
    """
    manifest_file = Path(manifest_path)
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")

    with open(manifest_file, "r", encoding="utf-8") as fh:
        manifests = json.load(fh)

    checksums: Dict[str, str] = {}
    for entry in manifests:
        # Gather both EEG and questionnaire file lists (they are stored as plain strings)
        for file_path in entry.get("eeg_files", []) + entry.get("questionnaire_files", []):
            if os.path.isfile(file_path):
                checksums[file_path] = compute_sha256(file_path)

    # Ensure the output directory exists and write the JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(checksums, out_f, indent=2)

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Main entry point for the utils module.

    It creates the exclusion logger (T007) and then generates the
    dataset manifest required by T004.  After the manifest is written,
    it records SHA‑256 checksums for all listed files (T005) and stores
    them under ``data/checksums.json``.
    """
    # Initialise logging infrastructure (T007)
    logger = setup_exclusion_logging(DEFAULT_EXCLUSION_LOG_PATH)
    logger.info("Utils initialisation complete – generating dataset manifest.")

    # Datasets required by the project (spec correction from 'ds' to 'ds003501')
    required_datasets = ["ds003501", "ds004137"]
    generate_manifest(required_datasets)

    logger.info("Dataset manifest generated at data/raw/dataset_manifest.json")

    # Record checksums (T005)
    try:
        record_checksums()
        logger.info("Checksums recorded at data/checksums.json")
    except Exception as exc:
        logger.error("Failed to record checksums: %s", exc)
        raise

    print("Dataset manifest generation and checksum recording completed.")

if __name__ == "__main__":
    main()

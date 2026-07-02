"""
save_processed.py
-----------------
This script orchestrates the full preprocessing pipeline for the EEG dataset
and saves both the preprocessed EEG recordings and the derived microstate
label sequences to ``data/processed/``.  Each saved artifact is accompanied by
a JSON metadata file that includes the mandatory ``analysis_type:
associational`` flag.

The pipeline re‑uses the public functions defined in the existing modules:

* ``download_eeg`` – fetches the raw OpenNeuro dataset (if not already
  present).
* ``apply_bandpass_filter`` – applies a 1‑40 Hz FIR band‑pass filter.
* ``run_ica_artifact_removal`` – removes ocular/muscle components.
* ``apply_average_rereference`` – re‑references the data to the average.
* ``apply_microstate_template`` – derives microstate labels.  The current
  implementation falls back to a simple K‑Means clustering on the
  pre‑processed time‑points (4 clusters) when a template is not available.

The script is safe to run repeatedly; existing files are overwritten.
"""

import os
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import mne
from sklearn.cluster import KMeans

# Import public pipeline functions
from preprocessing import (
    download_eeg,
    apply_bandpass_filter,
    run_ica_artifact_removal,
    apply_average_rereference,
    verify_preprocessing_quality,
)
from microstate import (
    load_microstate_template,
    apply_microstate_template,
)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _ensure_dir(path: Path) -> None:
    """Create ``path`` (and parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def _subject_id_from_path(raw_path: Path) -> str:
    """Derive a simple subject identifier from the raw file name."""
    return raw_path.stem  # e.g. ``sub-01_eeg`` → ``sub-01_eeg``

def _save_metadata(metadata_path: Path, metadata: dict) -> None:
    """Write a JSON metadata file."""
    with metadata_path.open("w", encoding="utf-8") as fp:
        json.dump(metadata, fp, indent=2, sort_keys=True)

# ----------------------------------------------------------------------
# Core processing function
# ----------------------------------------------------------------------
def process_and_save_subject(raw_path: Path, out_dir: Path) -> None:
    """
    Load a raw EEG file, run the full preprocessing pipeline, derive
    microstate labels, and write all outputs to ``out_dir``.

    Parameters
    ----------
    raw_path : Path
        Path to the raw EEG file (expected ``.fif`` format).
    out_dir : Path
        Destination directory for the processed artifacts.
    """
    # ------------------------------------------------------------------
    # 1. Load raw data
    # ------------------------------------------------------------------
    raw = mne.io.read_raw_fif(raw_path, preload=True, verbose=False)

    # ------------------------------------------------------------------
    # 2. Preprocess
    # ------------------------------------------------------------------
    raw = apply_bandpass_filter(raw)
    raw = run_ica_artifact_removal(raw)
    raw = apply_average_rereference(raw)

    # Verify quality (throws if thresholds are not met)
    verify_preprocessing_quality(raw)

    # ------------------------------------------------------------------
    # 3. Derive microstate labels
    # ------------------------------------------------------------------
    try:
        # Try to use a literature template if it exists
        template = load_microstate_template()
        labels = apply_microstate_template(raw, template)
    except Exception:
        # Fallback: simple K‑Means clustering on the time‑points
        data = raw.get_data().T  # shape (n_times, n_channels)
        kmeans = KMeans(n_clusters=4, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(data)

    # ------------------------------------------------------------------
    # 4. Save outputs
    # ------------------------------------------------------------------
    subject_id = _subject_id_from_path(raw_path)

    # 4a. Preprocessed EEG (MNE .fif)
    eeg_out_path = out_dir / f"{subject_id}_preproc_raw.fif"
    raw.save(eeg_out_path, overwrite=True)

    # 4b. Microstate label sequence (NumPy .npy)
    labels_out_path = out_dir / f"{subject_id}_microstate_labels.npy"
    np.save(labels_out_path, labels)

    # 4c. Metadata JSON
    metadata = {
        "subject_id": subject_id,
        "analysis_type": "associational",
        "processing_date": datetime.utcnow().isoformat() + "Z",
        "preprocessed_eeg_path": str(eeg_out_path.relative_to(Path.cwd())),
        "microstate_labels_path": str(labels_out_path.relative_to(Path.cwd())),
    }
    metadata_path = out_dir / f"{subject_id}_metadata.json"
    _save_metadata(metadata_path, metadata)

    print(f"[INFO] Processed and saved subject '{subject_id}'")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the script.

    Steps:
    1. Ensure the raw dataset is present (download if necessary).
    2. Locate all raw ``.fif`` files under ``data/raw/``.
    3. Process each subject and write results to ``data/processed/``.
    """
    project_root = Path(__file__).resolve().parents[1]  # repository root
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    _ensure_dir(processed_dir)

    # Step 1 – download if the raw directory is empty
    if not any(raw_dir.rglob("*.fif")):
        print("[INFO] Raw data not found – initiating download.")
        download_eeg()  # Expected to populate ``data/raw/``

    # Step 2 – iterate over raw files
    raw_files = list(raw_dir.rglob("*.fif"))
    if not raw_files:
        raise FileNotFoundError(
            f"No raw EEG files (*.fif) found in '{raw_dir}'."
        )

    for raw_path in raw_files:
        try:
            process_and_save_subject(raw_path, processed_dir)
        except Exception as exc:
            print(f"[ERROR] Failed processing {raw_path}: {exc}")

    print("[INFO] All subjects processed. Results are in 'data/processed/'.")

if __name__ == "__main__":
    main()

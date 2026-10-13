"""Download OpenNeuro fMRI datasets (ds000246) and prepare manifest & checksums.

This script:
1. Downloads the OpenNeuro dataset `ds000246` via the HuggingFace `datasets`
   library.
2. Copies each subject's NIfTI file into
   `data/raw/openneuro/ds000246/` with a deterministic filename
   `<subject_id>_<run_label>.nii.gz`.
3. Generates `manifest.json` containing the required columns:
   `subject_id`, `run_label`, `age`, `years_training`, `fd`.
4. Computes SHA‑256 checksums for every copied file and writes them to
   `data/raw/checksums.json`.
5. Performs validation:
   * At least 20 distinct subjects are present.
   * Every subject has at least one “Improv” and one “Scripted” run.
   * All required columns exist; otherwise a clear `ValueError` is raised.

The script aborts loudly on any validation failure, satisfying the
requirement that no synthetic fallback is used.
"""
import json
import hashlib
import shutil
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from datasets import load_dataset

log = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of `file_path`."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    # Destination directories
    raw_dir: Path = paths.data("raw", "openneuro", "ds000246")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Load the dataset (non‑streaming to trigger download)
    log.info("Loading OpenNeuro dataset ds000246...")
    ds = load_dataset("openneuro", "ds000246")
    # The dataset typically has a single split (e.g., 'train')
    split_name = next(iter(ds))
    dataset = ds[split_name]

    manifest = []
    checksums = {}

    for idx, row in enumerate(dataset):
        # Required columns
        try:
            subject_id = row["subject_id"]
            run_label = row["run_label"]
            age = row["age"]
            years_training = row["years_training"]
            fd = row["fd"]
        except KeyError as exc:
            raise ValueError(
                f"Row {idx} is missing required column {exc.args[0]!r}."
            ) from None

        manifest.append(
            {
                "subject_id": subject_id,
                "run_label": run_label,
                "age": age,
                "years_training": years_training,
                "fd": fd,
            }
        )

        # The dataset provides a file column; its exact name varies
        # between OpenNeuro releases. We try a few common names.
        file_info = (
            row.get("file")
            or row.get("path")
            or row.get("filename")
            or row.get("url")
        )
        if not file_info:
            raise ValueError(
                f"Row {idx} (subject {subject_id}, run {run_label}) does not contain a file reference."
            )

        # `file_info` may be a dict with a 'path' key (local cache) or a string URL.
        if isinstance(file_info, dict) and "path" in file_info:
            src_path = Path(file_info["path"])
        elif isinstance(file_info, str):
            # When a plain string is given, the datasets library stores the file
            # locally and returns the path as a string.
            src_path = Path(file_info)
        else:
            raise ValueError(
                f"Unrecognised file reference format for row {idx}: {file_info!r}"
            )

        if not src_path.is_file():
            raise FileNotFoundError(
                f"Expected file {src_path} for subject {subject_id} run {run_label} does not exist."
            )

        # Create a deterministic destination filename
        dest_name = f"{subject_id}_{run_label}.nii.gz"
        dest_path = raw_dir / dest_name

        # Copy the file (preserving metadata)
        shutil.copy2(src_path, dest_path)

        # Compute and store checksum
        checksums[dest_name] = compute_sha256(dest_path)

    # Write manifest.json
    manifest_path = raw_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    log.info(f"Wrote manifest with {len(manifest)} entries to {manifest_path}")

    # Write checksums.json at the top‑level raw folder
    checksums_path = paths.data("raw", "checksums.json")
    checksums_path.write_text(json.dumps(checksums, indent=2))
    log.info(f"Wrote checksums for {len(checksums)} files to {checksums_path}")

    # ----- Validation -------------------------------------------------
    # 1) Minimum number of subjects
    subjects = {entry["subject_id"] for entry in manifest}
    if len(subjects) < 20:
        raise ValueError(
            f"Dataset contains only {len(subjects)} subjects; at least 20 are required."
        )
    log.info(f"Found {len(subjects)} unique subjects (>=20 required).")

    # 2) Each subject must have both Improv and Scripted runs
    runs_by_subject = {}
    for entry in manifest:
        runs_by_subject.setdefault(entry["subject_id"], set()).add(entry["run_label"])

    missing = {
        sid: runs
        for sid, runs in runs_by_subject.items()
        if not {"Improv", "Scripted"}.issubset(runs)
    }
    if missing:
        missing_str = ", ".join(f"{sid} ({', '.join(runs)})" for sid, runs in missing.items())
        raise ValueError(
            f"The following subjects lack required runs (Improv & Scripted): {missing_str}"
        )
    log.info("All subjects contain both Improv and Scripted runs.")

    log.info("OpenNeuro download and verification completed successfully.")

if __name__ == "__main__":
    main()

import sys
from pathlib import Path
import json
from huggingface_hub import hf_hub_download
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# The QM9 dataset as hosted on HuggingFace
DATASET_NAME = "deepchem/qm9"

# Columns that must be present according to the original QM9 publication
REQUIRED_COLUMNS = {"smiles", "homo"}

def _load_dataset_schema(repo_id: str):
    """
    Load the dataset schema (column names) from the HuggingFace repository
    without pulling in heavy dependencies like ``datasets`` or ``pyarrow``.
    The repository contains a ``dataset_infos.json`` file that lists the
    feature names.  This function downloads that JSON file, parses it, and
    returns a simple ``list`` of column names.
    """
    try:
        info_path = hf_hub_download(repo_id=repo_id, filename="dataset_infos.json")
    except Exception as exc:
        log.error(f"Failed to download dataset infos: {exc}")
        raise RuntimeError("Could not retrieve QM9 schema information") from exc

    try:
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
    except Exception as exc:
        log.error(f"Failed to parse dataset infos JSON: {exc}")
        raise RuntimeError("Corrupt dataset infos file") from exc

    # The JSON structure follows the 🤗 datasets convention:
    #   {"features": {"smiles": {...}, "homo": {...}, ...}, ...}
    features = info.get("features")
    if not isinstance(features, dict):
        raise RuntimeError("Dataset infos JSON does not contain a 'features' mapping")

    column_names = list(features.keys())
    log.debug(f"Discovered columns in QM9: {column_names}")
    return column_names

def download_and_verify() -> None:
    """
    Download the QM9 dataset from HuggingFace, verify that the required columns
    (SMILES and HOMO) are present, and persist a placeholder parquet file for
    downstream steps.

    Raises:
        RuntimeError: If the dataset cannot be downloaded or required columns are
                      missing.
    """
    log.info(f"Fetching QM9 schema from HuggingFace repository '{DATASET_NAME}'")
    try:
        column_names = _load_dataset_schema(DATASET_NAME)
    except RuntimeError as exc:
        raise

    missing = REQUIRED_COLUMNS - set(column_names)
    if missing:
        raise RuntimeError(
            f"QM9 dataset is missing required columns: {', '.join(sorted(missing))}"
        )
    log.info("All required columns are present in the QM9 dataset schema.")

    # Download a representative parquet file (the training split).  The exact
    # split name is not critical for later steps – they only need a parquet file
    # that can be read by downstream scripts.  We store it as ``qm9.parquet``.
    try:
        parquet_path = hf_hub_download(
            repo_id=DATASET_NAME,
            filename="data/train.parquet",  # common path in the repo
        )
    except Exception as exc:
        log.error(f"Failed to download QM9 parquet file: {exc}")
        raise RuntimeError("Could not download QM9 data file") from exc

    out_path: Path = paths.data("raw", "qm9.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy the downloaded file to the canonical location expected by the pipeline.
    # This avoids re‑downloading in later stages.
    try:
        out_path.write_bytes(Path(parquet_path).read_bytes())
    except Exception as exc:
        log.error(f"Failed to write parquet file to {out_path}: {exc}")
        raise RuntimeError("Could not persist QM9 parquet file") from exc

    log.info(f"QM9 dataset parquet saved to {out_path}")
    log.info("Download and verification completed successfully.")

if __name__ == "__main__":
    download_and_verify()

import json
import logging
import time
from pathlib import Path
from hashlib import sha256

# Import the verified datasets library; will raise if not installed.
try:
    from datasets import load_dataset, concatenate_datasets
except ImportError as e:
    raise ImportError(
        "The 'datasets' package is required. Please install it via 'pip install datasets'."
    ) from e

# Use the shared logger from llmxive_toolkit if available; otherwise fall back to std lib.
try:
    from llmxive_toolkit import get_logger, paths
    log = get_logger(__name__)
    data_root = paths.data  # callable that creates paths inside the project
except Exception:  # pragma: no cover
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    log = logging.getLogger(__name__)

    def data_root(*subpaths):
        """Fallback helper mimicking llmxive_toolkit.paths.data."""
        p = Path("data", *subpaths)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA‑256 hash of a file."""
    h = sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()

def download_oqmd_dataset(output_path: Path, max_retries: int = 3) -> None:
    """
    Download the OQMD subset from the verified Hugging Face source
    and materialize it as a Parquet file.
    Implements exponential‑backoff retry logic.
    """
    dataset_name = "jablonkagroup/oqmd"
    config_name = "raw_data"

    attempt = 0
    while attempt < max_retries:
        try:
            log.info(
                f"Attempt {attempt + 1}/{max_retries}: loading {dataset_name} "
                f"(config={config_name})..."
            )
            ds_dict = load_dataset(dataset_name, config_name, trust_remote_code=True)

            # Combine all splits into one Dataset
            if isinstance(ds_dict, dict):
                ds = concatenate_datasets(list(ds_dict.values()))
            else:
                ds = ds_dict

            log.info(f"Dataset loaded successfully – {len(ds)} records.")
            log.info(f"Writing dataset to {output_path} ...")
            ds.to_parquet(str(output_path))
            log.info("Dataset materialization complete.")
            return
        except Exception as exc:  # pragma: no cover
            attempt += 1
            if attempt < max_retries:
                wait = 2 ** attempt
                log.warning(
                    f"Download failed (attempt {attempt}/{max_retries}): {exc}. "
                    f"Retrying in {wait} seconds..."
                )
                time.sleep(wait)
            else:
                log.error(f"All download attempts failed: {exc}")
                raise RuntimeError(
                    f"Failed to download OQMD dataset after {max_retries} attempts."
                ) from exc

def main() -> None:
    """
    Entry point for task T001a.
    - Downloads the OQMD subset (if not present).
    - Computes & stores a SHA‑256 checksum.
    - On subsequent runs, verifies the checksum and aborts on mismatch.
    """
    # Resolve output locations
    raw_dir = data_root("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = raw_dir / "oqmd_subset.parquet"
    checksum_path = data_root("checksums.json")

    # If the dataset already exists, verify its integrity.
    if parquet_path.exists() and checksum_path.exists():
        log.info(f"Found existing dataset at {parquet_path}. Verifying checksum...")
        with open(checksum_path, "r") as f:
            saved = json.load(f)
        expected = saved.get("sha256")
        actual = calculate_sha256(str(parquet_path))
        if expected != actual:
            raise RuntimeError(
                f"Checksum mismatch for {parquet_path} – expected {expected}, got {actual}."
            )
        log.info("Checksum verification passed – existing dataset is valid.")
        return

    # Otherwise, download the dataset.
    log.info("Downloading OQMD subset...")
    download_oqmd_dataset(parquet_path)

    # Compute and persist checksum.
    log.info("Computing SHA‑256 checksum for the downloaded file...")
    current_hash = calculate_sha256(str(parquet_path))
    checksum_record = {
        "filename": parquet_path.name,
        "sha256": current_hash,
    }
    with open(checksum_path, "w") as f:
        json.dump(checksum_record, f, indent=2)
    log.info(f"Checksum written to {checksum_path}: {current_hash}")

if __name__ == "__main__":
    main()
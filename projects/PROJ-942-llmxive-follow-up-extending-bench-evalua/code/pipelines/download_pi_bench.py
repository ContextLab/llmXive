import argparse
from pathlib import Path
from llmxive_toolkit import paths, get_logger
from datasets import load_dataset, DatasetDict
from datasets.exceptions import DatasetNotFoundError

log = get_logger(__name__)

# The official π‑Bench dataset is hosted on the Hugging Face Hub under the
# namespace "allenai". Using the fully‑qualified identifier ensures that the
# dataset can be resolved on the CI runner without requiring any custom
# authentication or trust‑remote‑code flags.
DEFAULT_DATASET_ID = "allenai/pi_bench"

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the π‑Bench dataset into data/raw"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(paths.data("raw")),
        help="Directory to store raw dataset files (used for downstream pipelines)",
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default=DEFAULT_DATASET_ID,
        help="HuggingFace dataset identifier (e.g., 'allenai/pi_bench')",
    )
    args = parser.parse_args()
    raw_dir = Path(args.data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Downloading dataset {args.dataset_id}")

    # Attempt to download the dataset.  We deliberately avoid passing
    # `data_dir` to `load_dataset` because that argument is intended for
    # local dataset scripts; providing it for a hub dataset can cause a
    # `DatasetNotFoundError`.  Instead we rely on the library's default
    # cache location and, after a successful download, write a small
    # manifest file into `raw_dir` so downstream steps can verify that the
    # download succeeded.
    try:
        ds: DatasetDict = load_dataset(args.dataset_id)
    except DatasetNotFoundError as e:
        log.error(f"Failed to locate dataset '{args.dataset_id}': {e}")
        raise

    # Force materialisation of at least one example from each split to
    # guarantee that the download has completed successfully.
    for split_name, split in ds.items():
        try:
            _ = split[0]
            log.debug(f"Loaded first example from split '{split_name}'.")
        except Exception as e:
            log.error(f"Failed to load example from split '{split_name}': {e}")
            raise

    # Write a simple manifest file that records which splits were downloaded.
    manifest_path = raw_dir / "download_manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as f:
        for split_name in ds.keys():
            f.write(f"{split_name}\\n")
    log.info(f"Download completed successfully. Manifest written to {manifest_path}")

    # Log the location of cached files for debugging purposes.
    for cache_file in ds.cache_files.values():
        if isinstance(cache_file, dict):
            cache_path = cache_file.get("filename")
            if cache_path:
                log.debug(f"Cached file: {cache_path}")

if __name__ == "__main__":
    main()

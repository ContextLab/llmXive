import argparse
from pathlib import Path
from llmxive_toolkit import paths, get_logger
from datasets import load_dataset, DatasetDict

log = get_logger(__name__)

# The official π‑Bench dataset is hosted on the Hugging Face Hub under the
# namespace "allenai".  Using the fully‑qualified identifier ensures that the
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
        help="Directory to store raw dataset files",
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

    log.info(f"Downloading dataset {args.dataset_id} into {raw_dir}")

    # Load the dataset; the `data_dir` argument tells the `datasets` library
    # to store the downloaded files under `raw_dir`.  This also enables the
    # library's built‑in checksum verification.
    ds: DatasetDict = load_dataset(args.dataset_id, data_dir=str(raw_dir))

    # Force materialisation of at least one example from each split to
    # guarantee that the download has completed successfully.
    for split_name, split in ds.items():
        try:
            _ = split[0]
            log.debug(f"Loaded first example from split '{split_name}'.")
        except Exception as e:
            log.error(f"Failed to load example from split '{split_name}': {e}")
            raise

    log.info("Download completed successfully.")
    for p in raw_dir.rglob("*"):
        if p.is_file():
            log.debug(f"Downloaded file: {p} ({p.stat().st_size} bytes)")

if __name__ == "__main__":
    main()

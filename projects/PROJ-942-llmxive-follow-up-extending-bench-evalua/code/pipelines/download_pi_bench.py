import argparse
from pathlib import Path
from llmxive_toolkit import paths, get_logger
from datasets import load_dataset

log = get_logger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the pi_bench dataset into data/raw"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(paths.data("raw")),
        help="Directory to store raw dataset files",
    )
    args = parser.parse_args()
    raw_dir = Path(args.data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Downloading pi_bench dataset into {raw_dir}")
    # The HF `datasets` library handles checksum verification internally.
    ds = load_dataset("pi_bench", data_dir=str(raw_dir))

    # Force materialization of at least one example to ensure download completes.
    if "train" in ds:
        _ = ds["train"][0]
    else:
        # If the dataset does not expose a 'train' split, just take the first split.
        first_split = list(ds.keys())[0]
        _ = ds[first_split][0]

    log.info("Download completed successfully.")
    for p in raw_dir.rglob("*"):
        if p.is_file():
            log.debug(f"Downloaded file: {p} ({p.stat().st_size} bytes)")

if __name__ == "__main__":
    main()

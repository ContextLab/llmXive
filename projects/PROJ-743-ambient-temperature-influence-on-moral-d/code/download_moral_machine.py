import sys
import logging
import gzip
from pathlib import Path
import requests

from config import DATA_RAW_DIR

# Figshare direct download link for a publicly-available excerpt of the Moral Machine dataset.
MORAL_MACHINE_URL = "https://figshare.com/ndownloader/files/23117579"
DEFAULT_OUTPUT = DATA_RAW_DIR / "moral_machine.csv.gz"

def download_moral_machine(output_path: Path = DEFAULT_OUTPUT, url: str = MORAL_MACHINE_URL) -> None:
    """
    Download the Moral Machine CSV and save it as a compressed .csv.gz file.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading Moral Machine dataset from {url} to {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            # The source is a CSV; we compress it on the fly to .csv.gz
            with gzip.open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        logger.info(f"Successfully downloaded and compressed dataset to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to download Moral Machine dataset: {exc}")
        raise

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Download the Moral Machine CSV dataset.")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    try:
        download_moral_machine(Path(args.output))
        return 0
    except Exception:
        return 1

if __name__ == "__main__":
    sys.exit(main())

import urllib.request
import zipfile
import json
import pandas as pd
import logging
import tempfile
from pathlib import Path
from llmxive_toolkit import paths
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def _ensure_pyarrow():
    """
    Ensure that the 'pyarrow' package is available for parquet support.
    If it cannot be imported, attempt to install it via pip.
    """
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        log.info("pyarrow not found, installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyarrow"])
        # Re‑import to verify installation
        import pyarrow  # noqa: F401
        log.info("pyarrow installed successfully.")

def main():
    """
    Download MS‑COCO 2017 validation captions and store them as a Parquet file.
    The official COCO annotations zip is used as a verified real source.
    """
    url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    output_path = paths.data("raw", "coco_captions.parquet")

    try:
        log.info(f"Downloading COCO annotations from {url}...")
        with urllib.request.urlopen(url) as resp:
            data = resp.read()

        with tempfile.TemporaryDirectory() as td:
            zip_path = Path(td) / "coco.zip"
            with open(zip_path, "wb") as f:
                f.write(data)

            with zipfile.ZipFile(zip_path, "r") as z:
                # Extract validation captions JSON
                with z.open('annotations/captions_val2017.json') as jf:
                    coco_data = json.load(jf)

        # Convert list of caption dicts to a DataFrame
        df = pd.DataFrame(coco_data)

        if 'image_id' not in df.columns or 'caption' not in df.columns:
            raise KeyError(
                f"Expected columns 'image_id' and 'caption' not found. Columns present: {df.columns}"
            )

        # Keep only required columns
        df = df[['image_id', 'caption']]

        # Ensure parquet engine is available
        _ensure_pyarrow()

        log.info(f"Saving {len(df)} validation captions to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(str(output_path), index=False)

        log.info("Successfully downloaded and saved COCO validation captions.")
    except Exception as e:
        # Fail loudly as required by the task constraints
        raise RuntimeError(f"Failed to fetch COCO validation dataset: {e}") from e

if __name__ == "__main__":
    main()

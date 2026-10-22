import pandas as pd
import logging
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
        import pyarrow  # noqa: F401
        log.info("pyarrow installed successfully.")

def main():
    """
    Read the raw COCO parquet file and write a curated CSV of prompts.
    The resulting CSV must contain at least 400 rows and have the header:
    'image_id,caption'.
    """
    input_path = paths.data("raw", "coco_captions.parquet")
    output_path = paths.data("processed", "prompts.csv")

    try:
        # Ensure parquet engine is present before reading
        _ensure_pyarrow()

        log.info(f"Reading raw data from {input_path}...")
        df = pd.read_parquet(input_path)

        # Validate required columns
        if 'image_id' not in df.columns or 'caption' not in df.columns:
            raise KeyError(
                f"Expected columns 'image_id' and 'caption' not found in {df.columns}"
            )

        processed_df = df[['image_id', 'caption']]

        log.info(f"Writing {len(processed_df)} rows to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        processed_df.to_csv(output_path, index=False)

        if len(processed_df) < 400:
            raise RuntimeError(
                f"Dataset contains only {len(processed_df)} rows, expected >= 400."
            )

        log.info("Preprocessing complete.")
    except Exception as e:
        raise RuntimeError(f"Failed to preprocess COCO captions: {e}") from e

if __name__ == "__main__":
    main()

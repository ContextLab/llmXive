import pandas as pd
import logging
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def main():
    """
    Read the raw COCO parquet file and write a curated CSV of prompts.
    Must contain >= 400 rows.
    """
    input_path = paths.data("raw", "coco_captions.parquet")
    output_path = paths.data("processed", "prompts.csv")

    try:
        log.info(f"Reading raw data from {input_path}...")
        df = pd.read_parquet(input_path)

        if 'image_id' not in df.columns or 'caption' not in df.columns:
            raise KeyError(f"Required columns 'image_id' or 'caption' missing from {input_path}")

        # Curate the prompt table
        processed_df = df[['image_id', 'caption']]

        if len(processed_df) < 400:
            raise RuntimeError(f"Dataset contains only {len(processed_df)} rows, expected >= 400.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        processed_df.to_csv(output_path, index=False)
        log.info(f"Successfully wrote {len(processed_df)} rows to {output_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to preprocess COCO captions: {e}") from e

if __name__ == "__main__":
    main()

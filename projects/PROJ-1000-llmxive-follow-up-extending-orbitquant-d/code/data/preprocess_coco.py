import pandas as pd
import logging
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def main():
    """
    Preprocess the raw COCO parquet file into a CSV of prompts.
    """
    input_path = paths.data("raw", "coco_captions.parquet")
    output_path = paths.data("processed", "prompts.csv")

    try:
        log.info(f"Reading raw data from {input_path}...")
        df = pd.read_parquet(input_path)
        
        # The nlpconnect/coco_captions dataset has 'image_id' and 'caption'
        # Ensure we only keep these two columns
        if 'image_id' not in df.columns or 'caption' not in df.columns:
            raise KeyError(f"Expected columns 'image_id' and 'caption' not found in {df.columns}")
        
        processed_df = df[['image_id', 'caption']]
        
        log.info(f"Writing {len(processed_df)} rows to {output_path}...")
        processed_df.to_csv(output_path, index=False)
        
        if len(processed_df) < 400:
            raise RuntimeError(f"Dataset contains only {len(processed_df)} rows, expected >= 400.")
        
        log.info("Preprocessing complete.")
    except Exception as e:
        raise RuntimeError(f"Failed to preprocess COCO captions: {e}") from e

if __name__ == "__main__":
    main()

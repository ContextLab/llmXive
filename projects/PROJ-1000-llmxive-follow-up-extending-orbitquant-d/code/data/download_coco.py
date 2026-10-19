import urllib.request
import zipfile
import json
import pandas as pd
import logging
import tempfile
from pathlib import Path
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def main():
    """
    Download MS-COCO 2017 validation captions.
    Note: The 'nlpconnect/coco_captions' HuggingFace dataset is currently gated/private (401).
    Using the verified real source: the official COCO annotations zip.
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
                # Extract validation captions
                with z.open('annotations/captions_val2017.json') as jf:
                    coco_data = json.load(jf)
        
        # Convert the list of caption dicts to a DataFrame
        # Expected format: [{"image_id": ..., "caption": ..., "id": ...}, ...]
        df = pd.DataFrame(coco_data)
        
        if 'image_id' not in df.columns or 'caption' not in df.columns:
            raise KeyError(f"Expected columns 'image_id' and 'caption' not found in dataset. Columns: {df.columns}")
        
        # Keep only the necessary columns
        df = df[['image_id', 'caption']]
        
        log.info(f"Saving {len(df)} validation captions to {output_path}...")
        df.to_parquet(str(output_path), index=False)
        
        log.info("Successfully downloaded and saved COCO validation captions.")
    except Exception as e:
        # Fail loudly as per constraints
        raise RuntimeError(f"Failed to fetch COCO validation dataset: {e}") from e

if __name__ == "__main__":
    main()

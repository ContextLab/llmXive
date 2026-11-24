import os
import urllib.request
import zipfile
import tempfile
import pandas as pd
import logging
from pathlib import Path
from pycocotools.coco import COCO
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def main():
    """
    Download MS-COCO 2017 validation captions and store them as a Parquet file.
    Uses the verified real source recipe.
    """
    url = 'http://images.cocodataset.org/annotations/annotations_trainval2017.zip'
    output_path = paths.data("raw", "coco_captions.parquet")

    try:
        log.info(f"Downloading COCO annotations from {url}...")
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, 'anno.zip')
            urllib.request.urlretrieve(url, zip_path)

            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(tmp)

            ann_file = os.path.join(tmp, 'annotations', 'captions_val2017.json')
            if not os.path.exists(ann_file):
                raise FileNotFoundError(f"Expected annotation file {ann_file} not found in zip.")

            coco = COCO(ann_file)
            ids = coco.getAnnIds()
            anns = coco.loadAnns(ids)

            log.info(f"Loaded {len(anns)} records from COCO validation set.")

            # Convert to DataFrame and filter columns
            df = pd.DataFrame(anns)
            if 'image_id' not in df.columns or 'caption' not in df.columns:
                raise KeyError("Expected columns 'image_id' and 'caption' not found in annotations.")

            df = df[['image_id', 'caption']]

            # Save to parquet
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(str(output_path), index=False)
            log.info(f"Successfully saved captions to {output_path}")

    except Exception as e:
        # Fail loudly as required
        raise RuntimeError(f"Failed to download and save COCO captions: {e}") from e

if __name__ == "__main__":
    main()

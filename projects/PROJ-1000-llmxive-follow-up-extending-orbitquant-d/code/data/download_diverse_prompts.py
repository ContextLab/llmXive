import urllib.request
import zipfile
import json
import csv
import tempfile
import random
import logging
from pathlib import Path
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def main():
    """
    Download a diverse external prompt set from COCO 2017 training captions.
    """
    url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    output_path = paths.data("processed", "diverse_prompts.csv")
    
    try:
        log.info(f"Downloading diverse prompts from {url}...")
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
        
        with tempfile.TemporaryDirectory() as td:
            zip_path = Path(td) / "coco.zip"
            with open(zip_path, "wb") as f:
                f.write(data)
            
            with zipfile.ZipFile(zip_path, "r") as z:
                # Use training set for diversity
                with z.open('annotations/captions_train2017.json') as jf:
                    coco_data = json.load(jf)
        
        # Fixed seed for reproducibility
        random.seed(42)
        all_annotations = coco_data['annotations']
        
        # Sample at least 150 rows
        num_samples = 200
        sampled_annotations = random.sample(all_annotations, min(num_samples, len(all_annotations)))
        
        records = []
        for i, ann in enumerate(sampled_annotations):
            records.append({
                "prompt_id": f"diverse_{i}",
                "caption": ann['caption'],
                "source": "coco_train2017"
            })
        
        if len(records) < 150:
            raise RuntimeError(f"Sampled only {len(records)} prompts, expected >= 150.")

        log.info(f"Writing {len(records)} diverse prompts to {output_path}...")
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["prompt_id", "caption", "source"])
            writer.writeheader()
            writer.writerows(records)
        
        log.info("Diverse prompts downloaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch diverse prompts: {e}") from e

if __name__ == "__main__":
    main()
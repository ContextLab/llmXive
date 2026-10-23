import os
import urllib.request
import zipfile
import tempfile
import random
import csv
import logging
from pathlib import Path
from pycocotools.coco import COCO
from datasets import load_dataset
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def main():
    """
    Download a diverse set of prompts from at least two external public collections.
    Source 1: COCO 2017 Train.
    Source 2: lambdalabs/pokemon-blip-captions (HF).
    """
    output_path = paths.data("processed", "diverse_prompts.csv")
    records = []
    random.seed(42)

    try:
        # Source 1: COCO 2017 Train
        log.info("Fetching prompts from COCO 2017 Train...")
        coco_url = 'http://images.cocodataset.org/annotations/annotations_trainval2017.zip'
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, 'coco_diverse.zip')
            urllib.request.urlretrieve(coco_url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(tmp)
            
            ann_file = os.path.join(tmp, 'annotations', 'captions_train2017.json')
            coco = COCO(ann_file)
            ids = coco.getAnnIds()
            anns = coco.loadAnns(ids)
            
            # Sample 100
            sampled_coco = random.sample(anns, min(100, len(anns)))
            for i, ann in enumerate(sampled_coco):
                records.append({
                    "prompt_id": f"coco_{i}",
                    "caption": ann['caption'],
                    "source": "coco2017_train"
                })

        # Source 2: HuggingFace - pokemon-blip-captions (Real public dataset)
        log.info("Fetching prompts from HF pokemon-blip-captions...")
        ds = load_dataset("lambdalabs/pokemon-blip-captions", split="train", streaming=True)
        
        count = 0
        for item in ds:
            if count >= 100:
                break
            # The dataset has 'text' as the caption field
            caption = item.get('text', '')
            if caption:
                records.append({
                    "prompt_id": f"blip_{count}",
                    "caption": caption,
                    "source": "pokemon_blip"
                })
                count += 1

        if len(records) < 150:
            raise RuntimeError(f"Sampled only {len(records)} prompts, expected >= 150.")

        # Save to CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["prompt_id", "caption", "source"])
            writer.writeheader()
            writer.writerows(records)
        
        log.info(f"Successfully wrote {len(records)} diverse prompts to {output_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to download diverse prompts: {e}") from e

if __name__ == "__main__":
    main()
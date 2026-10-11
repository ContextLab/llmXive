"""
Fetch a diverse set of text prompts from the MS-COCO training set using HuggingFace datasets.
Writes the result to data/processed/diverse_prompts.csv.
"""
import csv
import logging
import sys
import random
from pathlib import Path
from typing import List, Dict

try:
    from datasets import load_dataset
except ImportError:
    raise RuntimeError("The 'datasets' library is required. Please run 'pip install datasets'.")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def fetch_diverse_prompts(num_samples: int = 1000) -> List[Dict[str, str]]:
    """
    Fetches diverse text prompts from the COCO training split via streaming.
    """
    try:
        logger.info("Streaming MS-COCO training set from HuggingFace (nlpconnect/coco_captions)...")
        dataset = load_dataset("nlpconnect/coco_captions", split="train", streaming=True)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch COCO training dataset from HuggingFace: {e}") from e

    prompts = []
    # Use a fixed seed for reproducibility of the "diverse" sample
    random.seed(42)
    
    count = 0
    for item in dataset:
        caption = item.get("caption")
        if isinstance(caption, str) and caption.strip():
            prompts.append({
                "id": f"train_{count}",
                "caption": caption.strip(),
                "source": "coco_train2017"
            })
            count += 1
        if len(prompts) >= num_samples:
            break
    
    if not prompts:
        raise RuntimeError("No valid captions were extracted from the COCO training dataset.")
    
    logger.info(f"Fetched {len(prompts)} diverse prompts.")
    return prompts

def main() -> None:
    config = Config()
    prompts = fetch_diverse_prompts(num_samples=1000)
    
    output_path = config.processed_data_dir / "diverse_prompts.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "caption", "source"])
        writer.writeheader()
        writer.writerows(prompts)
    
    logger.info(f"Diverse prompts saved to {output_path}")

if __name__ == "__main__":
    main()

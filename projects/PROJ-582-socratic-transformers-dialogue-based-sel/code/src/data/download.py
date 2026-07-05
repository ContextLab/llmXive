"""
Dataset Downloader for Socratic Transformers Project.

Fetches GSM8K and MATH datasets from HuggingFace datasets.
Produces real data files in data/processed/ for downstream processing.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure project root is in path for imports if run as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from datasets import load_dataset
from src.utils.config import get_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

DATASET_CONFIGS = {
    "gsm8k": {
        "name": "gsm8k",
        "config": "main",
        "split": "train",
        "output_file": "gsm8k_train.jsonl",
        "description": "Grade School Math 8K dataset for reasoning tasks."
    },
    "math": {
        "name": "competition_math",
        "config": "main",
        "split": "train",
        "output_file": "math_train.jsonl",
        "description": "MATH dataset (competition math problems)."
    }
}

def download_dataset(
    dataset_name: str,
    output_dir: Optional[Path] = None,
    max_samples: Optional[int] = None
) -> Path:
    """
    Download a specific dataset from HuggingFace and save to JSONL.

    Args:
        dataset_name: Key in DATASET_CONFIGS (e.g., 'gsm8k', 'math')
        output_dir: Directory to save the output file. Defaults to config data path.
        max_samples: If provided, limit the dataset to this many samples.

    Returns:
        Path to the saved JSONL file.
    """
    config = get_config()
    if output_dir is None:
        output_dir = Path(config.data_processed_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    if dataset_name not in DATASET_CONFIGS:
        raise ValueError(f"Unknown dataset: {dataset_name}. Available: {list(DATASET_CONFIGS.keys())}")

    ds_config = DATASET_CONFIGS[dataset_name]
    output_file = output_dir / ds_config["output_file"]

    logger.info(f"Loading dataset: {ds_config['name']} (config: {ds_config['config']})")
    logger.info(f"Description: {ds_config['description']}")

    try:
        dataset = load_dataset(
            ds_config["name"],
            ds_config["config"],
            split=ds_config["split"]
        )
    except Exception as e:
        logger.error(f"Failed to load dataset {ds_config['name']}: {e}")
        raise

    if max_samples and max_samples > 0:
        logger.info(f"Limiting dataset to {max_samples} samples.")
        dataset = dataset.select(range(min(max_samples, len(dataset))))

    logger.info(f"Saving {len(dataset)} samples to {output_file}")

    # Determine column mapping based on dataset structure
    # GSM8K: question, answer
    # MATH: problem, solution (sometimes split differently depending on HF version)
    # We normalize to a standard schema: question, answer, source_dataset
    normalized_data = []

    for item in dataset:
        record = {
            "source_dataset": ds_config["name"],
            "original_index": item.get("id", None)
        }

        if dataset_name == "gsm8k":
            # GSM8K format: question, answer (contains final answer and reasoning)
            record["question"] = item.get("question", "")
            record["answer"] = item.get("answer", "")
        elif dataset_name == "math":
            # MATH format: problem, solution
            record["question"] = item.get("problem", "")
            record["answer"] = item.get("solution", "")
        else:
            # Fallback for unexpected structures
            record["question"] = str(item)
            record["answer"] = ""

        normalized_data.append(record)

    # Write to JSONL
    with open(output_file, "w", encoding="utf-8") as f:
        for record in normalized_data:
            import json
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"Successfully downloaded and saved {dataset_name} to {output_file}")
    return output_file


def download_all_datasets(
    output_dir: Optional[Path] = None,
    max_samples: Optional[int] = None
) -> Dict[str, Path]:
    """
    Download all configured datasets.

    Args:
        output_dir: Directory to save output files.
        max_samples: Limit for each dataset.

    Returns:
        Dictionary mapping dataset_name to output file path.
    """
    results = {}
    for name in DATASET_CONFIGS.keys():
        try:
            path = download_dataset(name, output_dir, max_samples)
            results[name] = path
        except Exception as e:
            logger.error(f"Skipping {name} due to error: {e}")
            results[name] = None
    return results


def main():
    """
    Entry point for script execution.
    Downloads GSM8K and MATH datasets to data/processed/.
    """
    config = get_config()
    output_dir = Path(config.data_processed_dir)

    logger.info(f"Starting dataset download. Output dir: {output_dir}")

    # Default: download full datasets.
    # For quick testing, users can set MAX_SAMPLES env var.
    max_samples = None
    if "MAX_SAMPLES" in os.environ:
        try:
            max_samples = int(os.environ["MAX_SAMPLES"])
            logger.info(f"Using MAX_SAMPLES limit: {max_samples}")
        except ValueError:
            logger.warning("Invalid MAX_SAMPLES value, ignoring limit.")

    results = download_all_datasets(output_dir, max_samples)

    success_count = sum(1 for v in results.values() if v is not None)
    total_count = len(results)

    if success_count == total_count:
        logger.info(f"Download complete. All {total_count} datasets saved.")
        return 0
    else:
        logger.warning(f"Download incomplete. {success_count}/{total_count} datasets saved.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

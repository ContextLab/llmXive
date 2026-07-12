import os
import json
import logging
from typing import Dict, List, Any, Optional, Generator
import pandas as pd
from datasets import load_dataset

from logging_config import setup_logging

logger = setup_logging(__name__)


def ensure_dirs(base_path: str) -> None:
    """Ensure that the required directories exist."""
    os.makedirs(os.path.join(base_path, "raw"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "processed"), exist_ok=True)
    logger.info(f"Ensured directories under {base_path}")


def fetch_gatemem(dataset_name: str = "llmXive/GateMem", split: str = "train") -> Any:
    """
    Fetch the GateMem dataset from HuggingFace.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load (e.g., 'train', 'test').

    Returns:
        The loaded dataset object.
    """
    logger.info(f"Fetching dataset: {dataset_name} (split={split})")
    try:
        dataset = load_dataset(dataset_name, split=split)
        logger.info(f"Successfully loaded {len(dataset)} examples")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise


def parse_jsonl_file(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Parse a JSONL file line by line to save memory.

    Args:
        file_path: Path to the JSONL file.

    Yields:
        Parsed dictionary for each line.
    """
    logger.info(f"Parsing JSONL file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")


def save_to_jsonl(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save a list of dictionaries to a JSONL file.

    Args:
        data: List of dictionaries to save.
        output_path: Path to the output JSONL file.
    """
    logger.info(f"Saving {len(data)} records to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")


def load_from_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    Load a JSONL file into a list of dictionaries.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of parsed dictionaries.
    """
    logger.info(f"Loading JSONL file: {file_path}")
    return list(parse_jsonl_file(file_path))


def get_dataset_statistics(dataset: Any) -> Dict[str, Any]:
    """
    Calculate basic statistics for a dataset.

    Args:
        dataset: The dataset object (e.g., from HuggingFace).

    Returns:
        Dictionary containing statistics.
    """
    stats = {
        "total_examples": len(dataset),
        "columns": dataset.column_names if hasattr(dataset, "column_names") else [],
    }
    logger.info(f"Dataset statistics: {stats}")
    return stats


def run_data_loader_pipeline(
    dataset_name: str = "llmXive/GateMem",
    output_dir: str = "data",
    split: str = "train"
) -> str:
    """
    Run the full data loading pipeline.

    Args:
        dataset_name: HuggingFace dataset name.
        output_dir: Directory to save processed data.
        split: Dataset split to load.

    Returns:
        Path to the saved processed data file.
    """
    ensure_dirs(output_dir)
    dataset = fetch_gatemem(dataset_name, split)
    stats = get_dataset_statistics(dataset)

    output_path = os.path.join(output_dir, "processed", "gatemem_train.jsonl")
    data_list = [dict(row) for row in dataset]
    save_to_jsonl(data_list, output_path)

    logger.info(f"Pipeline complete. Output saved to {output_path}")
    return output_path

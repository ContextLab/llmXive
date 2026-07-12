import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datasets import Dataset

from logging_config import setup_logging

logger = setup_logging(__name__)


def clean_text(text: str) -> str:
    """
    Clean text by removing special characters and normalizing whitespace.

    Args:
        text: Input text.

    Returns:
        Cleaned text.
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_and_format(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and format a list of records.

    Args:
        data: List of dictionaries.

    Returns:
        List of cleaned dictionaries.
    """
    cleaned = []
    for item in data:
        new_item = {}
        for k, v in item.items():
            if isinstance(v, str):
                new_item[k] = clean_text(v)
            else:
                new_item[k] = v
        cleaned.append(new_item)
    return cleaned


def run_preprocessing_pipeline(
    data: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run the full preprocessing pipeline.

    Args:
        data: Input data list.
        output_path: Optional path to save results.

    Returns:
        Processed data list.
    """
    logger.info(f"Preprocessing {len(data)} records")
    processed = clean_and_format(data)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(processed, f, indent=2)
        logger.info(f"Saved processed data to {output_path}")

    return processed


def main() -> None:
    """Main entry point."""
    logger.info("Running preprocess main")
    sample_data = [{"text": "Hello, World!", "id": "1"}]
    result = run_preprocessing_pipeline(sample_data, "data/processed/sample_clean.json")
    logger.info(f"Processed result: {result}")


if __name__ == "__main__":
    main()

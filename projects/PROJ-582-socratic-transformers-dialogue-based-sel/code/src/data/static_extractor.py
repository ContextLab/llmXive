"""
Static QA Extractor for GSM8K and MATH datasets.

This module extracts static (question, answer) tuples from the downloaded
GSM8K and MATH datasets to create a baseline dataset for comparative study.
It implements the non-origination-compliant process required by FR-001.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Ensure the project root is in the path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_config


def extract_gsm8k(dataset_split: str = "train") -> List[Dict[str, Any]]:
    """
    Extract static QA tuples from the GSM8K dataset.

    Args:
        dataset_split: The split of the dataset to load (e.g., 'train', 'test').

    Returns:
        A list of dictionaries with 'question' and 'answer' keys.
    """
    tuples = []
    try:
        # Load the dataset using the datasets library
        # GSM8K is hosted by openai/gsm8k
        dataset = load_dataset("openai/gsm8k", "main", split=dataset_split)

        for item in dataset:
            # GSM8K format: question (str), answer (str with reasoning and final answer)
            question = item.get("question", "")
            answer = item.get("answer", "")

            if question and answer:
                tuples.append({
                    "question": question,
                    "answer": answer,
                    "source": "gsm8k",
                    "split": dataset_split
                })
    except Exception as e:
        # Fail loudly if data cannot be loaded
        raise RuntimeError(f"Failed to load GSM8K dataset: {e}")

    return tuples


def extract_math(dataset_split: str = "train") -> List[Dict[str, Any]]:
    """
    Extract static QA tuples from the MATH dataset.

    Args:
        dataset_split: The split of the dataset to load (e.g., 'train', 'test').

    Returns:
        A list of dictionaries with 'question' and 'answer' keys.
    """
    tuples = []
    try:
        # Load the dataset using the datasets library
        # MATH is hosted by hendrycks/math
        dataset = load_dataset("hendrycks/math", "train", split=dataset_split)

        for item in dataset:
            # MATH format: problem (str), solution (str)
            question = item.get("problem", "")
            answer = item.get("solution", "")

            if question and answer:
                tuples.append({
                    "question": question,
                    "answer": answer,
                    "source": "math",
                    "split": dataset_split
                })
    except Exception as e:
        # Fail loudly if data cannot be loaded
        raise RuntimeError(f"Failed to load MATH dataset: {e}")

    return tuples


def extract_static_qa(
    gsm8k_split: str = "train",
    math_split: str = "train",
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Combine static QA tuples from GSM8K and MATH datasets.

    Args:
        gsm8k_split: The split of the GSM8K dataset to use.
        math_split: The split of the MATH dataset to use.
        limit: Optional maximum number of total tuples to return.

    Returns:
        A combined list of static QA tuples.
    """
    all_tuples = []

    # Extract from GSM8K
    gsm8k_tuples = extract_gsm8k(gsm8k_split)
    all_tuples.extend(gsm8k_tuples)

    # Extract from MATH
    math_tuples = extract_math(math_split)
    all_tuples.extend(math_tuples)

    # Apply limit if specified
    if limit is not None and len(all_tuples) > limit:
        all_tuples = all_tuples[:limit]

    return all_tuples


def write_jsonl(
    data: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Write a list of dictionaries to a JSONL file.

    Args:
        data: List of dictionaries to write.
        output_path: Path to the output JSONL file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main() -> None:
    """
    Main entry point for the static QA extractor.

    Loads data from GSM8K and MATH, extracts static tuples, and writes them
    to the specified output file.
    """
    config = get_config()

    # Define output path relative to project root
    output_path = PROJECT_ROOT / "data" / "processed" / "static_tuples.jsonl"

    print(f"Extracting static QA tuples...")
    print(f"  GSM8K split: {config.get('GSM8K_SPLIT', 'train')}")
    print(f"  MATH split: {config.get('MATH_SPLIT', 'train')}")

    # Extract data
    # Using a limit for testing purposes if specified in config, otherwise all
    limit = config.get("DATA_EXTRACT_LIMIT")
    static_tuples = extract_static_qa(
        gsm8k_split=config.get('GSM8K_SPLIT', 'train'),
        math_split=config.get('MATH_SPLIT', 'train'),
        limit=limit
    )

    print(f"Extracted {len(static_tuples)} static tuples.")

    # Write to file
    write_jsonl(static_tuples, str(output_path))
    print(f"Wrote static tuples to: {output_path}")


if __name__ == "__main__":
    main()

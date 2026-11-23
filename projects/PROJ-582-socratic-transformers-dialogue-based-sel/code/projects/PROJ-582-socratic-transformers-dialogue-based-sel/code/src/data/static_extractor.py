"""
Static QA Extractor for GSM8K and MATH datasets.

This module implements the extraction of static question-answer pairs from
the downloaded GSM8K and MATH datasets to create a baseline dataset for
comparative study (FR-001).

Output: data/processed/static_tuples.jsonl
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Add project root to path to ensure imports work when run from code/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import get_logger

logger = get_logger(__name__)

def extract_gsm8k(dataset_name: str = "gsm8k", split: str = "train") -> List[Dict[str, str]]:
    """
    Extracts question and answer pairs from the GSM8K dataset.

    Args:
        dataset_name: HuggingFace dataset name (default: gsm8k)
        split: Dataset split to load (default: train)

    Returns:
        List of dictionaries with 'question' and 'answer' keys.
    """
    logger.info(f"Loading GSM8K dataset: {dataset_name}, split: {split}")
    try:
        dataset = load_dataset(dataset_name, "main", split=split, trust_remote_code=True)
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise

    tuples = []
    for i, item in enumerate(dataset):
        # GSM8K format: question (str), answer (str containing solution and final answer)
        question = item.get("question", "")
        answer = item.get("answer", "")

        if not question or not answer:
            logger.warning(f"Skipping GSM8K item {i}: missing question or answer")
            continue

        tuples.append({
            "question": question,
            "answer": answer,
            "source": "gsm8k"
        })

    logger.info(f"Extracted {len(tuples)} tuples from GSM8K")
    return tuples

def extract_math(dataset_name: str = "math", split: str = "train") -> List[Dict[str, str]]:
    """
    Extracts question and answer pairs from the MATH dataset.

    Args:
        dataset_name: HuggingFace dataset name (default: math)
        split: Dataset split to load (default: train)

    Returns:
        List of dictionaries with 'question' and 'answer' keys.
    """
    logger.info(f"Loading MATH dataset: {dataset_name}, split: {split}")
    try:
        # MATH dataset usually has a 'problem' and 'solution' field
        dataset = load_dataset(dataset_name, split=split, trust_remote_code=True)
    except Exception as e:
        logger.error(f"Failed to load MATH dataset: {e}")
        raise

    tuples = []
    for i, item in enumerate(dataset):
        # MATH format: problem (str), solution (str)
        question = item.get("problem", "")
        answer = item.get("solution", "")

        if not question or not answer:
            logger.warning(f"Skipping MATH item {i}: missing problem or solution")
            continue

        tuples.append({
            "question": question,
            "answer": answer,
            "source": "math"
        })

    logger.info(f"Extracted {len(tuples)} tuples from MATH")
    return tuples

def extract_static_qa(output_path: Optional[Path] = None) -> Path:
    """
    Main function to extract static QA tuples from GSM8K and MATH datasets
    and write them to a JSONL file.

    Args:
        output_path: Path to the output JSONL file. Defaults to data/processed/static_tuples.jsonl

    Returns:
        Path to the created output file.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "data" / "processed" / "static_tuples.jsonl"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting static QA extraction. Output will be written to: {output_path}")

    all_tuples = []

    # Extract from GSM8K
    try:
        gsm8k_tuples = extract_gsm8k()
        all_tuples.extend(gsm8k_tuples)
    except Exception as e:
        logger.error(f"Failed to extract GSM8K data: {e}")
        # Continue with other datasets if one fails

    # Extract from MATH
    try:
        math_tuples = extract_math()
        all_tuples.extend(math_tuples)
    except Exception as e:
        logger.error(f"Failed to extract MATH data: {e}")
        # Continue if one fails

    if not all_tuples:
        logger.warning("No tuples were extracted from any dataset. Output file will be empty.")

    # Write to JSONL
    logger.info(f"Writing {len(all_tuples)} tuples to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for item in all_tuples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info(f"Successfully wrote static tuples to {output_path}")
    return output_path

def write_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes a list of dictionaries to a JSONL file.

    Args:
        data: List of dictionaries to write.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info(f"Wrote {len(data)} items to {output_path}")

def main() -> None:
    """Main entry point for the static extractor script."""
    output_path = PROJECT_ROOT / "data" / "processed" / "static_tuples.jsonl"
    extract_static_qa(output_path)
    logger.info("Static QA extraction completed successfully.")

if __name__ == "__main__":
    main()

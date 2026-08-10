"""
Static QA Extractor for GSM8K and MATH datasets.

This module implements the baseline dataset generation (Question, Answer)
required for comparative study (FR-001). It extracts static tuples from
the downloaded raw datasets without generating any dialogue or critique.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Ensure we can import from the project root if run as a script
# This handles both `python src/data/static_extractor.py` and module imports
_project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.logging import get_logger

logger = get_logger(__name__)


def extract_gsm8k(
    raw_data_path: Optional[Path] = None,
    split: str = "train",
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract static QA tuples from the GSM8K dataset.

    Args:
        raw_data_path: Path to the cached/downloaded dataset directory.
                       If None, loads directly from HuggingFace 'openai/gsm8k'.
        split: Dataset split to use (default: 'train').
        limit: Maximum number of samples to extract. If None, uses all.

    Returns:
        List of dictionaries with keys: 'question', 'answer'.
    """
    logger.info(f"Loading GSM8K dataset (split={split}, limit={limit})")

    # Load dataset
    # The dataset name is 'openai/gsm8k' and we need the 'main' config
    try:
        dataset = load_dataset(
            "openai/gsm8k",
            "main",
            split=split,
            cache_dir=str(raw_data_path) if raw_data_path else None,
            trust_remote_code=True
        )
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise

    extracted = []
    count = 0

    for item in dataset:
        if limit and count >= limit:
            break

        question = item.get("question", "")
        answer = item.get("answer", "")

        if not question or not answer:
            logger.warning("Skipping GSM8K item with missing question or answer")
            continue

        extracted.append({
            "question": question,
            "answer": answer,
            "source": "gsm8k"
        })
        count += 1

    logger.info(f"Extracted {len(extracted)} static QA tuples from GSM8K")
    return extracted


def extract_math(
    raw_data_path: Optional[Path] = None,
    split: str = "train",
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract static QA tuples from the MATH dataset.

    Args:
        raw_data_path: Path to the cached/downloaded dataset directory.
                       If None, loads directly from HuggingFace 'hendrycks/math'.
        split: Dataset split to use (default: 'train').
        limit: Maximum number of samples to extract. If None, uses all.

    Returns:
        List of dictionaries with keys: 'question', 'answer'.
    """
    logger.info(f"Loading MATH dataset (split={split}, limit={limit})")

    try:
        dataset = load_dataset(
            "hendrycks/math",
            split=split,
            cache_dir=str(raw_data_path) if raw_data_path else None,
            trust_remote_code=True
        )
    except Exception as e:
        logger.error(f"Failed to load MATH dataset: {e}")
        raise

    extracted = []
    count = 0

    for item in dataset:
        if limit and count >= limit:
            break

        question = item.get("problem", "")
        answer = item.get("solution", "")

        if not question or not answer:
            logger.warning("Skipping MATH item with missing problem or solution")
            continue

        extracted.append({
            "question": question,
            "answer": answer,
            "source": "math"
        })
        count += 1

    logger.info(f"Extracted {len(extracted)} static QA tuples from MATH")
    return extracted


def extract_static_qa(
    output_dir: Path,
    gsm8k_limit: Optional[int] = None,
    math_limit: Optional[int] = None,
    raw_data_dir: Optional[Path] = None
) -> Path:
    """
    Main entry point to generate the static baseline dataset.

    Extracts data from both GSM8K and MATH, combines them, and writes
    a single JSONL file to the specified output directory.

    Args:
        output_dir: Directory where the output JSONL file will be written.
        gsm8k_limit: Optional limit for GSM8K samples.
        math_limit: Optional limit for MATH samples.
        raw_data_dir: Optional path to pre-downloaded raw data.

    Returns:
        Path to the generated JSONL file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "static_qa_baseline.jsonl"

    logger.info(f"Starting static QA extraction to {output_file}")

    # Extract from GSM8K
    gsm8k_data = extract_gsm8k(raw_data_path=raw_data_dir, limit=gsm8k_limit)

    # Extract from MATH
    math_data = extract_math(raw_data_path=raw_data_dir, limit=math_limit)

    # Combine
    all_data = gsm8k_data + math_data
    logger.info(f"Total combined static QA tuples: {len(all_data)}")

    # Write to JSONL
    write_jsonl(all_data, output_file)

    logger.info(f"Successfully wrote static baseline to {output_file}")
    return output_file


def write_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write a list of dictionaries to a JSONL file.

    Args:
        data: List of dictionaries to write.
        output_path: Path to the output file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main() -> None:
    """
    CLI entry point for the static extractor.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract static QA tuples from GSM8K and MATH datasets."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to write the output JSONL file."
    )
    parser.add_argument(
        "--gsm8k-limit",
        type=int,
        default=None,
        help="Maximum number of GSM8K samples to extract."
    )
    parser.add_argument(
        "--math-limit",
        type=int,
        default=None,
        help="Maximum number of MATH samples to extract."
    )
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default=None,
        help="Path to pre-downloaded raw data (optional)."
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    raw_data_dir = Path(args.raw_data_dir) if args.raw_data_dir else None

    extract_static_qa(
        output_dir=output_dir,
        gsm8k_limit=args.gsm8k_limit,
        math_limit=args.math_limit,
        raw_data_dir=raw_data_dir
    )


if __name__ == "__main__":
    main()

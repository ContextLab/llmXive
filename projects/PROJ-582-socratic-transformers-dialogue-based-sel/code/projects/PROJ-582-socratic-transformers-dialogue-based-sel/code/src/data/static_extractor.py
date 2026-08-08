"""
Static QA Extractor for GSM8K and MATH datasets.

This module extracts baseline (question, answer) tuples from downloaded
mathematical reasoning datasets to serve as a control condition for
the Socratic dialogue generation pipeline.

It adheres to the project's data structure and logging conventions.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Add project root to path for relative imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.logging import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)

def extract_gsm8k(
    split: str = "train",
    sample_size: Optional[int] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Extracts static QA tuples from the GSM8K dataset.

    Args:
        split: The dataset split to load (e.g., 'train', 'test').
        sample_size: If provided, limits the extraction to the first N samples.
        output_path: If provided, writes the JSONL output to this path.

    Returns:
        A list of dictionaries with keys: 'question', 'answer', 'source'.
    """
    logger.info(f"Loading GSM8K dataset (split={split})...")
    try:
        dataset = load_dataset("gsm8k", "main", split=split)
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise

    if sample_size:
        logger.info(f"Sampling {sample_size} items from GSM8K {split}...")
        dataset = dataset.select(range(min(sample_size, len(dataset))))

    records = []
    for i, item in enumerate(dataset):
        # GSM8K format: question (str), answer (str containing "#### final_answer")
        question = item["question"]
        answer = item["answer"]

        # Clean answer: GSM8K answers often end with "#### <number>"
        # We keep the full string for baseline comparison as per FR-001
        records.append({
            "question": question,
            "answer": answer,
            "source": "gsm8k",
            "id": f"gsm8k_{split}_{i}"
        })

    logger.info(f"Extracted {len(records)} static QA tuples from GSM8K.")

    if output_path:
        write_jsonl(records, output_path)

    return records

def extract_math(
    split: str = "train",
    sample_size: Optional[int] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Extracts static QA tuples from the MATH dataset.

    Args:
        split: The dataset split to load (e.g., 'train', 'test').
        sample_size: If provided, limits the extraction to the first N samples.
        output_path: If provided, writes the JSONL output to this path.

    Returns:
        A list of dictionaries with keys: 'question', 'answer', 'source'.
    """
    logger.info(f"Loading MATH dataset (split={split})...")
    try:
        # MATH dataset on HF: 'hendrycks/competition_math'
        dataset = load_dataset("hendrycks/competition_math", "main", split=split)
    except Exception as e:
        logger.error(f"Failed to load MATH dataset: {e}")
        raise

    if sample_size:
        logger.info(f"Sampling {sample_size} items from MATH {split}...")
        dataset = dataset.select(range(min(sample_size, len(dataset))))

    records = []
    for i, item in enumerate(dataset):
        question = item["problem"]
        answer = item["solution"]

        records.append({
            "question": question,
            "answer": answer,
            "source": "math",
            "id": f"math_{split}_{i}"
        })

    logger.info(f"Extracted {len(records)} static QA tuples from MATH.")

    if output_path:
        write_jsonl(records, output_path)

    return records

def extract_static_qa(
    gsm8k_sample: Optional[int] = None,
    math_sample: Optional[int] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """
    Orchestrates the extraction of static QA datasets from both sources.

    This implements FR-001: Generate the baseline dataset (question, answer)
    from downloaded sources for comparative study.

    Args:
        gsm8k_sample: Number of GSM8K samples to extract (None for all).
        math_sample: Number of MATH samples to extract (None for all).
        output_dir: Directory to write output files. Defaults to data/processed/.

    Returns:
        A dictionary mapping source names to their output file paths.
    """
    config = get_config()
    base_output_dir = output_dir or Path(config.data_dir) / "processed"
    base_output_dir.mkdir(parents=True, exist_ok=True)

    output_paths = {}

    # Extract GSM8K
    gsm8k_path = base_output_dir / "static_gsm8k_baseline.jsonl"
    extract_gsm8k(sample_size=gsm8k_sample, output_path=gsm8k_path)
    output_paths["gsm8k"] = gsm8k_path

    # Extract MATH
    math_path = base_output_dir / "static_math_baseline.jsonl"
    extract_math(sample_size=math_sample, output_path=math_path)
    output_paths["math"] = math_path

    logger.info(f"Static QA extraction complete. Files written to {base_output_dir}")
    return output_paths

def write_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    """
    Writes a list of records to a JSONL file.

    Args:
        records: List of dictionaries to write.
        path: Target file path.
    """
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info(f"Wrote {len(records)} records to {path}")

def main() -> None:
    """
    Entry point for the static extractor script.
    Reads configuration from environment or defaults and runs extraction.
    """
    config = get_config()
    # Default to small sample for quick verification if not specified
    # but allow full extraction if sample_size is None or explicitly set high
    gsm8k_n = int(os.getenv("GSM8K_SAMPLE_SIZE", "0")) or None
    math_n = int(os.getenv("MATH_SAMPLE_SIZE", "0")) or None

    logger.info("Starting Static QA Extraction (Task T013)...")
    extract_static_qa(gsm8k_sample=gsm8k_n, math_sample=math_n)
    logger.info("Static QA Extraction finished successfully.")

if __name__ == "__main__":
    main()

"""
Static QA Extractor for Socratic Transformers Project.

This module extracts static (question, answer) tuples from source datasets
(GSM8K, MATH) to create a baseline dataset for comparative study (FR-001).
It relies on the data downloaded by `download.py` to be present in `data/raw/`.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Ensure project root is in path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


def extract_gsm8k(
    raw_data_path: Path,
    output_path: Path,
    max_samples: Optional[int] = None
) -> int:
    """
    Extract static QA tuples from the GSM8K dataset.

    GSM8K format:
    - question: str
    - answer: str (contains the solution steps and the final answer, e.g., "Answer: 42")

    Args:
        raw_data_path: Path to the raw GSM8K dataset directory/file.
        output_path: Path to write the extracted JSONL file.
        max_samples: Optional limit on number of samples to process.

    Returns:
        The number of samples extracted.
    """
    logger.info(f"Loading GSM8K from {raw_data_path}")

    # Load dataset
    # Assuming the download task placed it in a cache or a specific path.
    # We try to load from the local cache or the specific split if available.
    # If raw_data_path is a directory containing the dataset files, we load from there.
    try:
        dataset = load_dataset(
            "json",
            data_files={"train": str(raw_data_path / "train.jsonl")},
            split="train"
        )
    except FileNotFoundError:
        # Fallback: try loading from HF cache if path is just a name, or specific structure
        # The download task should have ensured data is in data/raw/gsm8k/
        # If the file structure is different, we adapt.
        # Standard GSM8K on HF is 'gsm8k', 'main'.
        # If we are loading local files, we assume the structure from download.py.
        # Let's assume download.py saved it as data/raw/gsm8k/train.jsonl
        raise FileNotFoundError(f"Could not find GSM8K train data at {raw_data_path / 'train.jsonl'}")

    logger.info(f"Loaded {len(dataset)} GSM8K samples")

    extracted_count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f_out:
        for i, item in enumerate(dataset):
            if max_samples and i >= max_samples:
                break

            # GSM8K 'answer' field contains "The answer is X" or similar.
            # We keep the full answer string as the baseline 'answer' for FR-001.
            question = item.get("question", "").strip()
            answer = item.get("answer", "").strip()

            if not question or not answer:
                logger.warning(f"Skipping sample {i} due to missing question or answer")
                continue

            record = {
                "source": "gsm8k",
                "question": question,
                "answer": answer
            }

            f_out.write(json.dumps(record) + "\n")
            extracted_count += 1

            if extracted_count % 1000 == 0:
                logger.info(f"Extracted {extracted_count} GSM8K samples...")

    logger.info(f"Finished extracting {extracted_count} GSM8K samples to {output_path}")
    return extracted_count


def extract_math(
    raw_data_path: Path,
    output_path: Path,
    max_samples: Optional[int] = None
) -> int:
    """
    Extract static QA tuples from the MATH dataset.

    MATH format:
    - problem: str
    - solution: str
    - level: str
    - type: str

    Args:
        raw_data_path: Path to the raw MATH dataset directory/file.
        output_path: Path to write the extracted JSONL file.
        max_samples: Optional limit on number of samples to process.

    Returns:
        The number of samples extracted.
    """
    logger.info(f"Loading MATH from {raw_data_path}")

    try:
        dataset = load_dataset(
            "json",
            data_files={"train": str(raw_data_path / "train.jsonl")},
            split="train"
        )
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find MATH train data at {raw_data_path / 'train.jsonl'}")

    logger.info(f"Loaded {len(dataset)} MATH samples")

    extracted_count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f_out:
        for i, item in enumerate(dataset):
            if max_samples and i >= max_samples:
                break

            question = item.get("problem", "").strip()
            answer = item.get("solution", "").strip()

            if not question or not answer:
                logger.warning(f"Skipping sample {i} due to missing problem or solution")
                continue

            record = {
                "source": "math",
                "question": question,
                "answer": answer
            }

            f_out.write(json.dumps(record) + "\n")
            extracted_count += 1

            if extracted_count % 1000 == 0:
                logger.info(f"Extracted {extracted_count} MATH samples...")

    logger.info(f"Finished extracting {extracted_count} MATH samples to {output_path}")
    return extracted_count


def extract_static_qa(
    config: Optional[SocraticConfig] = None,
    max_samples_per_dataset: Optional[int] = None
) -> Dict[str, int]:
    """
    Orchestrates the extraction of static QA tuples from all configured datasets.

    This function implements FR-001: Generate the baseline dataset (question, answer)
    from downloaded sources for comparative study.

    Args:
        config: The SocraticConfig instance. If None, loads from environment.
        max_samples_per_dataset: Optional limit on samples per dataset.

    Returns:
        A dictionary mapping dataset names to the number of extracted samples.
    """
    if config is None:
        config = get_config()

    stats = {}

    # Define paths based on config
    raw_dir = Path(config.data_raw_dir)
    processed_dir = Path(config.data_processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # GSM8K Extraction
    gsm8k_raw = raw_dir / "gsm8k"
    if gsm8k_raw.exists():
        gsm8k_output = processed_dir / "static_gsm8k.jsonl"
        try:
            count = extract_gsm8k(gsm8k_raw, gsm8k_output, max_samples=max_samples_per_dataset)
            stats["gsm8k"] = count
        except FileNotFoundError as e:
            logger.error(f"Failed to extract GSM8K: {e}")
            stats["gsm8k"] = 0
    else:
        logger.warning(f"GSM8K raw data not found at {gsm8k_raw}. Skipping.")
        stats["gsm8k"] = 0

    # MATH Extraction
    math_raw = raw_dir / "math"
    if math_raw.exists():
        math_output = processed_dir / "static_math.jsonl"
        try:
            count = extract_math(math_raw, math_output, max_samples=max_samples_per_dataset)
            stats["math"] = count
        except FileNotFoundError as e:
            logger.error(f"Failed to extract MATH: {e}")
            stats["math"] = 0
    else:
        logger.warning(f"MATH raw data not found at {math_raw}. Skipping.")
        stats["math"] = 0

    # Combine into a single baseline file if both exist, or just list them
    # For FR-001, we produce the baseline dataset. We'll create a combined file too.
    combined_output = processed_dir / "static_baseline.jsonl"
    combined_count = 0
    with open(combined_output, 'w', encoding='utf-8') as f_out:
        for dataset_name, count in stats.items():
            if count > 0:
                input_file = processed_dir / f"static_{dataset_name}.jsonl"
                with open(input_file, 'r', encoding='utf-8') as f_in:
                    for line in f_in:
                        f_out.write(line)
                        combined_count += 1

    logger.info(f"Created combined static baseline with {combined_count} samples at {combined_output}")
    stats["combined"] = combined_count

    return stats


def main():
    """Main entry point for the static extractor script."""
    config = get_config()
    logger.info("Starting Static QA Extraction (FR-001)")
    
    # Optional: limit samples for quick testing if configured
    # max_samples = config.get("debug_max_samples", None)
    max_samples = None 

    results = extract_static_qa(config, max_samples_per_dataset=max_samples)
    
    logger.info("Extraction Summary:")
    for ds, count in results.items():
        logger.info(f"  {ds}: {count} samples")
    
    if sum(results.values()) == 0:
        logger.error("No samples were extracted. Check data paths.")
        sys.exit(1)
    else:
        logger.info("Static QA extraction completed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()

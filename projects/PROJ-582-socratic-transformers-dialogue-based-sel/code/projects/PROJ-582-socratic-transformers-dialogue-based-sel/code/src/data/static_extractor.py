"""
Static QA Extractor for Socratic Transformers Project.

This module extracts baseline (question, answer) tuples from GSM8K and MATH
datasets to serve as the static control condition (FR-001).
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Ensure project root is in path for relative imports if run as script
# but rely on installed package structure for normal usage
try:
    from src.utils.logging import get_logger
except ImportError:
    # Fallback for direct execution without package install
    import logging
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)

def extract_gsm8k(output_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract static QA tuples from the GSM8K dataset.

    Args:
        output_path: Path to write the JSONL output file.
        limit: Maximum number of samples to extract. If None, extracts all.

    Returns:
        List of dictionaries containing 'question' and 'answer'.
    """
    logger.info(f"Loading GSM8K dataset (limit={limit})...")
    try:
        dataset = load_dataset("gsm8k", "main", split="train")
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise

    extracted_data = []
    count = 0

    for item in dataset:
        if limit is not None and count >= limit:
            break

        # GSM8K format: question (str), answer (str with solution and final answer)
        # We store the raw answer string as provided by the dataset for baseline comparison.
        question = item.get("question", "")
        answer = item.get("answer", "")

        if not question or not answer:
            logger.warning("Skipping item with missing question or answer.")
            continue

        record = {
            "source": "gsm8k",
            "question": question,
            "answer": answer,
            "type": "static_baseline"
        }
        extracted_data.append(record)
        count += 1

    logger.info(f"Extracted {len(extracted_data)} samples from GSM8K.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for record in extracted_data:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return extracted_data

def extract_math(output_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract static QA tuples from the MATH dataset.

    Args:
        output_path: Path to write the JSONL output file.
        limit: Maximum number of samples to extract. If None, extracts all.

    Returns:
        List of dictionaries containing 'question' and 'answer'.
    """
    logger.info(f"Loading MATH dataset (limit={limit})...")
    try:
        # MATH dataset is often large; we load the train split
        dataset = load_dataset("hendrycks/competition_math", "main", split="train")
    except Exception as e:
        logger.error(f"Failed to load MATH dataset: {e}")
        raise

    extracted_data = []
    count = 0

    for item in dataset:
        if limit is not None and count >= limit:
            break

        question = item.get("problem", "")
        answer = item.get("solution", "") # MATH often provides the full solution in 'solution' or 'answer'
        # Sometimes 'answer' contains just the final result, but for baseline we want the ground truth.
        # The 'solution' field usually contains the step-by-step and final answer.
        # If 'solution' is empty, fallback to 'answer'.
        if not answer and "answer" in item:
            answer = item.get("answer", "")

        if not question or not answer:
            logger.warning("Skipping MATH item with missing question or answer.")
            continue

        record = {
            "source": "math",
            "question": question,
            "answer": answer,
            "type": "static_baseline"
        }
        extracted_data.append(record)
        count += 1

    logger.info(f"Extracted {len(extracted_data)} samples from MATH.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for record in extracted_data:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return extracted_data

def extract_static_qa(
    gsm8k_limit: Optional[int] = 100,
    math_limit: Optional[int] = 100,
    base_output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Main entry point to generate the baseline static dataset.

    Downloads/loads GSM8K and MATH, extracts QA pairs, and writes them to JSONL files.

    Args:
        gsm8k_limit: Max samples from GSM8K.
        math_limit: Max samples from MATH.
        base_output_dir: Base directory for output files. Defaults to project data/results/.

    Returns:
        Dictionary mapping dataset name to output file path.
    """
    if base_output_dir is None:
        # Default to project structure: projects/.../code/data/results/
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent.parent.parent
        base_output_dir = project_root / "data" / "results"

    base_output_dir.mkdir(parents=True, exist_ok=True)

    gsm8k_path = base_output_dir / "static_gsm8k_baseline.jsonl"
    math_path = base_output_dir / "static_math_baseline.jsonl"

    logger.info(f"Output directory set to: {base_output_dir}")

    extract_gsm8k(gsm8k_path, limit=gsm8k_limit)
    extract_math(math_path, limit=math_limit)

    return {
        "gsm8k": str(gsm8k_path),
        "math": str(math_path)
    }

def main():
    """CLI entry point for static QA extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract static QA baseline from GSM8K and MATH.")
    parser.add_argument("--gsm8k-limit", type=int, default=100, help="Max GSM8K samples")
    parser.add_argument("--math-limit", type=int, default=100, help="Max MATH samples")
    parser.add_argument("--output-dir", type=str, default=None, help="Base output directory")

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        results = extract_static_qa(
            gsm8k_limit=args.gsm8k_limit,
            math_limit=args.math_limit,
            base_output_dir=output_dir
        )
        print("Extraction successful. Output files:")
        for source, path in results.items():
            print(f"  {source}: {path}")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

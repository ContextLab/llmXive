"""
Static QA Extractor for GSM8K and MATH datasets.

This module extracts baseline (question, answer) tuples from the downloaded
GSM8K and MATH datasets to create a static baseline dataset for comparative
study (FR-001). The output is a JSONL file where each line is a JSON object
containing 'question' and 'answer' fields.

The extraction process is deterministic and does not involve any model generation,
ensuring a consistent baseline for evaluating the Socratic dialogue method.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))

from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger


logger = get_logger(__name__)


def extract_gsm8k(output_path: Path, limit: Optional[int] = None) -> int:
    """
    Extract static QA tuples from the GSM8K dataset.

    Args:
        output_path: Path to the output JSONL file.
        limit: Maximum number of samples to extract. If None, uses all data.

    Returns:
        Number of samples extracted.
    """
    logger.info(f"Loading GSM8K dataset for extraction (limit={limit})")

    try:
        # Load the train split of GSM8K
        # GSM8K has 'question' and 'answer' fields
        # answer field format: "The answer is <answer>. The final answer is <answer>"
        # We need to parse the answer to extract just the final number
        dataset = load_dataset("gsm8k", "main", split="train", streaming=True)

        extracted_count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for i, item in enumerate(dataset):
                if limit is not None and extracted_count >= limit:
                    break

                question = item["question"]
                raw_answer = item["answer"]

                # Parse GSM8K answer format: "The answer is X. The final answer is Y"
                # We want just the final answer
                # GSM8K answers typically end with "#### <answer>"
                if "####" in raw_answer:
                    final_answer = raw_answer.split("####")[-1].strip()
                else:
                    # Fallback: use the whole answer if format is unexpected
                    final_answer = raw_answer.strip()

                # Create the static tuple
                static_tuple = {
                    "question": question,
                    "answer": final_answer,
                    "source": "gsm8k",
                    "id": f"gsm8k_{i}"
                }

                f.write(json.dumps(static_tuple, ensure_ascii=False) + "\n")
                extracted_count += 1

                if extracted_count % 100 == 0:
                    logger.debug(f"Extracted {extracted_count} GSM8K samples")

        logger.info(f"Successfully extracted {extracted_count} samples from GSM8K to {output_path}")
        return extracted_count

    except Exception as e:
        logger.error(f"Failed to extract GSM8K data: {e}")
        raise


def extract_math(output_path: Path, limit: Optional[int] = None) -> int:
    """
    Extract static QA tuples from the MATH dataset.

    Args:
        output_path: Path to the output JSONL file.
        limit: Maximum number of samples to extract. If None, uses all data.

    Returns:
        Number of samples extracted.
    """
    logger.info(f"Loading MATH dataset for extraction (limit={limit})")

    try:
        # Load the train split of MATH
        # MATH has 'problem' and 'solution' fields
        dataset = load_dataset("hendrycks/math", split="train", streaming=True)

        extracted_count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for i, item in enumerate(dataset):
                if limit is not None and extracted_count >= limit:
                    break

                problem = item["problem"]
                solution = item["solution"]

                # Extract the final answer from the solution
                # MATH solutions typically end with "\boxed{<answer>}"
                if "\\boxed{" in solution:
                    # Extract content between \boxed{ and }
                    start_idx = solution.find("\\boxed{") + len("\\boxed{")
                    end_idx = solution.find("}", start_idx)
                    if end_idx != -1:
                        final_answer = solution[start_idx:end_idx]
                    else:
                        final_answer = solution
                else:
                    # Fallback: use the whole solution if format is unexpected
                    final_answer = solution.strip()

                # Create the static tuple
                static_tuple = {
                    "question": problem,
                    "answer": final_answer,
                    "source": "math",
                    "id": f"math_{i}"
                }

                f.write(json.dumps(static_tuple, ensure_ascii=False) + "\n")
                extracted_count += 1

                if extracted_count % 100 == 0:
                    logger.debug(f"Extracted {extracted_count} MATH samples")

        logger.info(f"Successfully extracted {extracted_count} samples from MATH to {output_path}")
        return extracted_count

    except Exception as e:
        logger.error(f"Failed to extract MATH data: {e}")
        raise


def extract_static_qa(
    output_dir: Optional[Path] = None,
    gsm8k_limit: Optional[int] = None,
    math_limit: Optional[int] = None,
    combine: bool = False
) -> Dict[str, str]:
    """
    Extract static QA tuples from both GSM8K and MATH datasets.

    Args:
        output_dir: Directory to save output files. If None, uses config default.
        gsm8k_limit: Maximum number of GSM8K samples to extract.
        math_limit: Maximum number of MATH samples to extract.
        combine: If True, also create a combined dataset.

    Returns:
        Dictionary mapping dataset names to output file paths.
    """
    config = get_config()
    if output_dir is None:
        output_dir = config.data_dir / "processed"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    # Extract GSM8K
    gsm8k_path = output_dir / "static_gsm8k.jsonl"
    gsm8k_count = extract_gsm8k(gsm8k_path, gsm8k_limit)
    results["gsm8k"] = str(gsm8k_path)
    logger.info(f"GSM8K extraction complete: {gsm8k_count} samples")

    # Extract MATH
    math_path = output_dir / "static_math.jsonl"
    math_count = extract_math(math_path, math_limit)
    results["math"] = str(math_path)
    logger.info(f"MATH extraction complete: {math_count} samples")

    # Optionally combine
    if combine:
        combined_path = output_dir / "static_combined.jsonl"
        logger.info(f"Creating combined dataset at {combined_path}")

        total_count = 0
        with open(combined_path, "w", encoding="utf-8") as f_out:
            # Add GSM8K samples
            with open(gsm8k_path, "r", encoding="utf-8") as f_in:
                for line in f_in:
                    f_out.write(line)
                    total_count += 1

            # Add MATH samples
            with open(math_path, "r", encoding="utf-8") as f_in:
                for line in f_in:
                    f_out.write(line)
                    total_count += 1

        results["combined"] = str(combined_path)
        logger.info(f"Combined dataset created: {total_count} total samples")

    return results


def main():
    """
    Main entry point for static QA extraction.

    Reads configuration from environment variables or uses defaults.
    Extracts GSM8K and MATH datasets and saves them as JSONL files.
    """
    logger.info("Starting static QA extraction for baseline dataset (FR-001)")

    try:
        config = get_config()

        # Parse command line arguments if any
        # For now, we use config values
        gsm8k_limit = config.get("gsm8k_extraction_limit", None)
        math_limit = config.get("math_extraction_limit", None)
        combine = config.get("combine_static_datasets", False)

        results = extract_static_qa(
            gsm8k_limit=gsm8k_limit,
            math_limit=math_limit,
            combine=combine
        )

        logger.info("Static QA extraction completed successfully")
        logger.info(f"Output files: {results}")

        # Print summary for quick verification
        print("\n=== Static QA Extraction Summary ===")
        for dataset_name, file_path in results.items():
            print(f"{dataset_name}: {file_path}")
        print("====================================\n")

        return 0

    except Exception as e:
        logger.error(f"Static QA extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

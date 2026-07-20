"""
Static QA Extractor for Socratic Transformers Project.

This module implements the extraction of baseline (question, answer) tuples
from downloaded datasets (GSM8K, MATH) for comparative study (FR-001).
It serves as the foundation for generating the static baseline dataset.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from src.utils.config import get_config
from src.utils.logging import get_logger


logger = get_logger(__name__)


def extract_gsm8k(
    dataset_path: Optional[str] = None,
    split: str = "train",
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract static QA tuples from the GSM8K dataset.

    Args:
        dataset_path: Path to the dataset. If None, loads from HuggingFace.
        split: Dataset split to use (default: "train").
        max_samples: Maximum number of samples to extract. If None, uses all.

    Returns:
        List of dictionaries with 'question' and 'answer' keys.
    """
    logger.info(f"Loading GSM8K dataset from {dataset_path or 'HuggingFace'}...")

    if dataset_path:
        dataset = load_dataset("json", data_files=dataset_path, split=split)
    else:
        # Load from HuggingFace datasets
        dataset = load_dataset("gsm8k", "main", split=split)

    logger.info(f"Extracting {len(dataset)} samples from GSM8K...")

    extracted = []
    for i, item in enumerate(dataset):
        if max_samples is not None and i >= max_samples:
            break

        question = item.get("question", "")
        answer = item.get("answer", "")

        if not question or not answer:
            logger.warning(f"Skipping sample {i} due to missing question or answer")
            continue

        extracted.append({
            "source": "gsm8k",
            "question": question,
            "answer": answer,
            "sample_id": f"gsm8k_{i}"
        })

    logger.info(f"Successfully extracted {len(extracted)} samples from GSM8K")
    return extracted


def extract_math(
    dataset_path: Optional[str] = None,
    split: str = "train",
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract static QA tuples from the MATH dataset.

    Args:
        dataset_path: Path to the dataset. If None, loads from HuggingFace.
        split: Dataset split to use (default: "train").
        max_samples: Maximum number of samples to extract. If None, uses all.

    Returns:
        List of dictionaries with 'question' and 'answer' keys.
    """
    logger.info(f"Loading MATH dataset from {dataset_path or 'HuggingFace'}...")

    if dataset_path:
        dataset = load_dataset("json", data_files=dataset_path, split=split)
    else:
        # Load from HuggingFace datasets
        # MATH dataset is under 'hendrycks/competition_math'
        dataset = load_dataset("hendrycks/competition_math", "main", split=split)

    logger.info(f"Extracting {len(dataset)} samples from MATH...")

    extracted = []
    for i, item in enumerate(dataset):
        if max_samples is not None and i >= max_samples:
            break

        question = item.get("problem", "")
        answer = item.get("solution", "")

        if not question or not answer:
            logger.warning(f"Skipping sample {i} due to missing problem or solution")
            continue

        # Clean up answer if it contains LaTeX formatting
        # MATH dataset often has \boxed{answer} format
        if "\\boxed{" in answer:
            # Extract content between \boxed{ and }
            start = answer.find("\\boxed{") + 7
            end = answer.find("}", start)
            if end != -1:
                answer = answer[start:end]

        extracted.append({
            "source": "math",
            "question": question,
            "answer": answer,
            "sample_id": f"math_{i}"
        })

    logger.info(f"Successfully extracted {len(extracted)} samples from MATH")
    return extracted


def extract_static_qa(
    output_dir: str,
    gsm8k_samples: Optional[int] = None,
    math_samples: Optional[int] = None
) -> Dict[str, str]:
    """
    Generate the baseline static QA dataset from GSM8K and MATH.

    This function creates the baseline dataset required for comparative study (FR-001).
    It extracts question-answer pairs from both datasets and saves them as JSONL files.

    Args:
        output_dir: Directory to save the output files.
        gsm8k_samples: Number of GSM8K samples to extract. If None, uses all.
        math_samples: Number of MATH samples to extract. If None, uses all.

    Returns:
        Dictionary with paths to the generated files:
        - 'gsm8k_path': Path to GSM8K static QA file
        - 'math_path': Path to MATH static QA file
        - 'combined_path': Path to combined static QA file
    """
    config = get_config()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting static QA extraction to {output_dir}")

    # Extract GSM8K samples
    gsm8k_data = extract_gsm8k(max_samples=gsm8k_samples)
    gsm8k_path = output_path / "static_gsm8k.jsonl"

    with open(gsm8k_path, "w", encoding="utf-8") as f:
        for item in gsm8k_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info(f"Wrote {len(gsm8k_data)} GSM8K samples to {gsm8k_path}")

    # Extract MATH samples
    math_data = extract_math(max_samples=math_samples)
    math_path = output_path / "static_math.jsonl"

    with open(math_path, "w", encoding="utf-8") as f:
        for item in math_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info(f"Wrote {len(math_data)} MATH samples to {math_path}")

    # Combine both datasets
    combined_data = gsm8k_data + math_data
    combined_path = output_path / "static_combined.jsonl"

    with open(combined_path, "w", encoding="utf-8") as f:
        for item in combined_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info(f"Wrote {len(combined_data)} combined samples to {combined_path}")

    return {
        "gsm8k_path": str(gsm8k_path),
        "math_path": str(math_path),
        "combined_path": str(combined_path)
    }


def main():
    """Main entry point for the static QA extractor."""
    config = get_config()

    # Determine output directory from config or default
    output_dir = config.static_data_output_dir
    if not output_dir:
        # Fallback to default path structure
        project_root = Path(__file__).resolve().parent.parent.parent
        output_dir = project_root / "data" / "processed" / "static_baseline"

    logger.info(f"Static QA extractor starting. Output directory: {output_dir}")

    # Extract static QA pairs
    # Use sample limits for initial run to avoid excessive data
    # These can be adjusted based on available resources
    gsm8k_limit = config.gsm8k_sample_limit if hasattr(config, 'gsm8k_sample_limit') else None
    math_limit = config.math_sample_limit if hasattr(config, 'math_sample_limit') else None

    result = extract_static_qa(
        output_dir=str(output_dir),
        gsm8k_samples=gsm8k_limit,
        math_samples=math_limit
    )

    logger.info(f"Static QA extraction complete. Files generated:")
    logger.info(f"  GSM8K: {result['gsm8k_path']}")
    logger.info(f"  MATH: {result['math_path']}")
    logger.info(f"  Combined: {result['combined_path']}")

    # Print summary to stdout for quick verification
    print(f"Static QA extraction complete:")
    print(f"  GSM8K samples: {sum(1 for _ in open(result['gsm8k_path']))}")
    print(f"  MATH samples: {sum(1 for _ in open(result['math_path']))}")
    print(f"  Combined samples: {sum(1 for _ in open(result['combined_path']))}")
    print(f"Output directory: {output_dir}")

    return result


if __name__ == "__main__":
    main()
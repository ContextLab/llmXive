"""
Static QA Extractor for Socratic Transformers Project.

Generates a baseline dataset of (question, answer) tuples from downloaded
sources (GSM8K, MATH) for comparative study (FR-001).
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset
from src.utils.config import get_config
from src.utils.logging import get_logger

# Ensure project root is in path for imports if running as script
if __name__ == "__main__":
    # Add parent directory to path to resolve src imports
    _project_root = Path(__file__).resolve().parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

logger = get_logger(__name__)

def extract_gsm8k(dataset: Any, split: str = "train", max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extracts (question, answer) tuples from the GSM8K dataset.

    GSM8K format:
    - question: str
    - answer: str (contains the final answer and reasoning, usually ending with ####)

    Args:
        dataset: The loaded GSM8K dataset object.
        split: The split to process (train or test).
        max_samples: Optional limit on number of samples.

    Returns:
        List of dicts with keys 'question', 'answer', 'source'.
    """
    logger.info(f"Extracting GSM8K {split} split...")
    samples = []
    data_split = dataset[split]

    count = 0
    for item in data_split:
        if max_samples and count >= max_samples:
            break

        question = item.get("question", "").strip()
        answer = item.get("answer", "").strip()

        if not question or not answer:
            logger.debug("Skipping item with missing question or answer.")
            continue

        samples.append({
            "question": question,
            "answer": answer,
            "source": "gsm8k",
            "type": "math_word_problem"
        })
        count += 1

    logger.info(f"Extracted {count} samples from GSM8K {split}.")
    return samples

def extract_math(dataset: Any, split: str = "train", max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extracts (question, answer) tuples from the MATH dataset.

    MATH format:
    - problem: str
    - solution: str (contains reasoning and final answer)
    - level: str (difficulty)
    - type: str (category)

    Args:
        dataset: The loaded MATH dataset object.
        split: The split to process.
        max_samples: Optional limit on number of samples.

    Returns:
        List of dicts with keys 'question', 'answer', 'source'.
    """
    logger.info(f"Extracting MATH {split} split...")
    samples = []
    data_split = dataset[split]

    count = 0
    for item in data_split:
        if max_samples and count >= max_samples:
            break

        question = item.get("problem", "").strip()
        solution = item.get("solution", "").strip()

        if not question or not solution:
            logger.debug("Skipping item with missing problem or solution.")
            continue

        samples.append({
            "question": question,
            "answer": solution,
            "source": "math",
            "type": item.get("type", "unknown"),
            "level": item.get("level", "unknown")
        })
        count += 1

    logger.info(f"Extracted {count} samples from MATH {split}.")
    return samples

def extract_static_qa(
    output_dir: Optional[str] = None,
    max_samples: Optional[int] = None,
    sources: Optional[List[str]] = None
) -> str:
    """
    Main entry point to extract static QA pairs from downloaded datasets.

    Args:
        output_dir: Directory to save the output JSONL file. Defaults to config output path.
        max_samples: Maximum number of samples to extract per dataset.
        sources: List of source names to process (default: ['gsm8k', 'math']).

    Returns:
        Path to the generated output file.
    """
    config = get_config()
    if output_dir is None:
        output_dir = config.output_dir

    output_path = Path(output_dir) / "static_qa_baseline.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if sources is None:
        sources = ["gsm8k", "math"]

    all_samples = []

    for source_name in sources:
        try:
            logger.info(f"Loading dataset: {source_name}")
            dataset = load_dataset(source_name, split="train")
            
            if source_name == "gsm8k":
                samples = extract_gsm8k(dataset, max_samples=max_samples)
            elif source_name == "math":
                samples = extract_math(dataset, max_samples=max_samples)
            else:
                logger.warning(f"Unknown source: {source_name}, skipping.")
                continue
            
            all_samples.extend(samples)
            logger.info(f"Successfully processed {source_name}: {len(samples)} samples.")
            
        except Exception as e:
            logger.error(f"Failed to process source {source_name}: {e}", exc_info=True)
            # Continue with other sources rather than failing completely

    if not all_samples:
        logger.warning("No samples were extracted. Check dataset availability.")
        # Create empty file to indicate completion
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("")
        return str(output_path)

    logger.info(f"Writing {len(all_samples)} total samples to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for sample in all_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    logger.info(f"Static QA extraction complete. Output saved to: {output_path}")
    return str(output_path)

def main():
    """CLI entry point for static QA extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract static QA pairs from source datasets.")
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of samples to extract per dataset."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for the JSONL file."
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["gsm8k", "math"],
        help="List of dataset sources to process."
    )

    args = parser.parse_args()

    extract_static_qa(
        output_dir=args.output_dir,
        max_samples=args.max_samples,
        sources=args.sources
    )

if __name__ == "__main__":
    main()
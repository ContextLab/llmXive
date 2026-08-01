"""
Static QA Extractor for GSM8K and MATH datasets.

This module implements FR-001: Generate the baseline dataset (question, answer)
from downloaded sources for comparative study.

It extracts static (question, answer) tuples from the real GSM8K and MATH datasets
loaded via HuggingFace `datasets`, writing them to JSONL files in the `data/processed/`
directory.

Dependencies:
    - datasets (from requirements.txt)
    - src.utils.config (for path configuration)
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Add project root to path to ensure imports work in execution environment
# This is necessary because the script might be run from the project root or code/
try:
    from src.utils.config import get_config
except ImportError:
    # Fallback for direct execution if src is not in PYTHONPATH
    # Assumes we are running from code/ or project root
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.config import get_config


def extract_gsm8k(output_path: Path, limit: Optional[int] = None) -> int:
    """
    Extract static QA tuples from the GSM8K dataset.

    Args:
        output_path: Path to the output JSONL file.
        limit: Maximum number of samples to extract (for testing).

    Returns:
        Number of records written.
    """
    print(f"Loading GSM8K dataset...")
    try:
        dataset = load_dataset("gsm8k", "main", split="train")
    except Exception as e:
        raise RuntimeError(f"Failed to load GSM8K dataset: {e}")

    records = []
    count = 0
    for item in dataset:
        if limit and count >= limit:
            break
        
        # GSM8K format: question, answer (contains "#### final_answer")
        question = item["question"]
        full_answer = item["answer"]
        
        # Extract just the final answer if it contains the separator
        if "####" in full_answer:
            final_answer = full_answer.split("####")[-1].strip()
        else:
            final_answer = full_answer.strip()

        records.append({
            "source": "gsm8k",
            "question": question,
            "answer": final_answer
        })
        count += 1

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Extracted {len(records)} GSM8K samples to {output_path}")
    return len(records)


def extract_math(output_path: Path, limit: Optional[int] = None) -> int:
    """
    Extract static QA tuples from the MATH dataset.

    Args:
        output_path: Path to the output JSONL file.
        limit: Maximum number of samples to extract (for testing).

    Returns:
        Number of records written.
    """
    print(f"Loading MATH dataset...")
    try:
        # MATH dataset is usually under 'math' with 'train' split
        dataset = load_dataset("hendrycks/math", "train", split="train")
    except Exception as e:
        raise RuntimeError(f"Failed to load MATH dataset: {e}")

    records = []
    count = 0
    for item in dataset:
        if limit and count >= limit:
            break

        # MATH format: problem, solution (contains boxed answer)
        question = item["problem"]
        solution = item["solution"]

        # Extract final answer if boxed
        # MATH answers are typically in \boxed{answer}
        import re
        match = re.search(r"\\boxed\{(.*?)\}", solution)
        if match:
            final_answer = match.group(1)
        else:
            final_answer = solution

        records.append({
            "source": "math",
            "question": question,
            "answer": final_answer
        })
        count += 1

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Extracted {len(records)} MATH samples to {output_path}")
    return len(records)


def extract_static_qa(config: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """
    Main entry point to extract static QA datasets.

    Reads configuration for output paths and limits, then runs extraction
    for both GSM8K and MATH.

    Args:
        config: Optional config dict. If None, loads from environment.

    Returns:
        Dictionary mapping dataset name to count of extracted records.
    """
    if config is None:
        config = get_config()

    # Determine output directory from config or defaults
    base_dir = Path(config.get("data_dir", "data"))
    processed_dir = base_dir / "processed"
    
    gsm8k_path = processed_dir / "gsm8k_static.jsonl"
    math_path = processed_dir / "math_static.jsonl"

    # Limits for testing (can be overridden by config)
    limit = config.get("data_limit", None)

    results = {}
    try:
        results["gsm8k"] = extract_gsm8k(gsm8k_path, limit=limit)
    except Exception as e:
        print(f"Error extracting GSM8K: {e}", file=sys.stderr)
        results["gsm8k"] = 0

    try:
        results["math"] = extract_math(math_path, limit=limit)
    except Exception as e:
        print(f"Error extracting MATH: {e}", file=sys.stderr)
        results["math"] = 0

    return results


def main():
    """CLI entry point."""
    print("Starting static QA extraction (T013)...")
    try:
        results = extract_static_qa()
        print(f"Extraction complete: {results}")
        
        # Verify outputs exist
        config = get_config()
        base_dir = Path(config.get("data_dir", "data"))
        processed_dir = base_dir / "processed"
        
        gsm8k_path = processed_dir / "gsm8k_static.jsonl"
        math_path = processed_dir / "math_static.jsonl"
        
        if gsm8k_path.exists():
            print(f"Verified: {gsm8k_path} exists ({gsm8k_path.stat().st_size} bytes)")
        else:
            print(f"Warning: {gsm8k_path} was not created", file=sys.stderr)
            
        if math_path.exists():
            print(f"Verified: {math_path} exists ({math_path.stat().st_size} bytes)")
        else:
            print(f"Warning: {math_path} was not created", file=sys.stderr)

    except Exception as e:
        print(f"Static extraction failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

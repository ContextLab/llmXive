"""
Static QA Extractor for Socratic Transformers Project.

This module extracts static (question, answer) pairs from source datasets
(GSM8K and MATH) to create a baseline dataset for comparative study.
It adheres to the principle of negative selection on belief by providing
a static baseline against which the dynamic dialogue tuples are compared.

Output: data/processed/static_tuples.jsonl
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Ensure we can import from the project root if run as a script
# The project structure places this file at:
# projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/data/static_extractor.py
# We need to add the 'code' directory to sys.path to resolve imports relative to it
# if running from the project root.
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger

logger = get_logger(__name__)

def extract_gsm8k(split: str = "train", limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract static QA pairs from the GSM8K dataset.

    Args:
        split: The dataset split to load (default: 'train').
        limit: Maximum number of samples to extract. If None, use all.

    Returns:
        List of dictionaries with 'question' and 'answer' keys.
    """
    logger.info(f"Loading GSM8K dataset (split={split})...")
    try:
        dataset = load_dataset("openai/gsm8k", "main", split=split)
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise

    extracted = []
    count = 0
    for item in dataset:
        if limit and count >= limit:
            break
        
        # GSM8K format: {'question': str, 'answer': str (contains "#### <answer>") }
        question = item['question']
        full_answer = item['answer']
        
        # Parse the answer to extract just the final result if possible,
        # though keeping the full reasoning string is often better for baseline.
        # The spec asks for (question, answer). We will store the full answer string
        # as provided by the dataset to ensure completeness, or split if strictly
        # the final number is needed. For a baseline, the full answer string
        # containing the reasoning is usually preferred to match the 'answer'
        # field in dialogue tuples where the model generates a full response.
        # However, standard GSM8K 'answer' includes the reasoning.
        # We will store it as is.
        
        extracted.append({
            "source": "gsm8k",
            "question": question,
            "answer": full_answer,
            "type": "static"
        })
        count += 1

    logger.info(f"Extracted {len(extracted)} static tuples from GSM8K.")
    return extracted

def extract_math(split: str = "train", limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract static QA pairs from the MATH dataset.

    Args:
        split: The dataset split to load (default: 'train').
        limit: Maximum number of samples to extract. If None, use all.

    Returns:
        List of dictionaries with 'question' and 'answer' keys.
    """
    logger.info(f"Loading MATH dataset (split={split})...")
    try:
        dataset = load_dataset("hendrycks/math", "train", split=split)
    except Exception as e:
        logger.error(f"Failed to load MATH dataset: {e}")
        raise

    extracted = []
    count = 0
    for item in dataset:
        if limit and count >= limit:
            break

        # MATH format: {'problem': str, 'solution': str, 'level': str, 'type': str, 'source': str}
        question = item['problem']
        full_solution = item['solution']

        extracted.append({
            "source": "math",
            "question": question,
            "answer": full_solution,
            "type": "static"
        })
        count += 1

    logger.info(f"Extracted {len(extracted)} static tuples from MATH.")
    return extracted

def extract_static_qa(limit_per_dataset: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Combine static QA pairs from GSM8K and MATH.

    Args:
        limit_per_dataset: Maximum number of samples to extract from each dataset.

    Returns:
        Combined list of static QA tuples.
    """
    gsm8k_data = extract_gsm8k(limit=limit_per_dataset)
    math_data = extract_math(limit=limit_per_dataset)
    
    combined = gsm8k_data + math_data
    logger.info(f"Total static tuples extracted: {len(combined)}")
    return combined

def write_jsonl(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write a list of dictionaries to a JSONL file.

    Args:
        data: List of dictionaries to write.
        output_path: Path to the output file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing {len(data)} records to {output_path}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    logger.info(f"Successfully wrote static tuples to {output_path}")

def main():
    """
    Main entry point for the static extractor.
    Generates data/processed/static_tuples.jsonl
    """
    # Define output path relative to project root
    # The task specifies output: data/processed/static_tuples.jsonl
    # We assume the script is run from the project root or the path is relative to it.
    # To be safe, we resolve relative to the project root (parent of 'code').
    project_root = Path(__file__).resolve().parent.parent.parent
    output_path = project_root / "data" / "processed" / "static_tuples.jsonl"

    logger.info(f"Starting static QA extraction. Output: {output_path}")

    try:
        # Extract data. 
        # Note: For a full run, we might want to limit this for speed if the datasets are huge,
        # but the task asks for the baseline dataset. We will extract a reasonable subset
        # if no limit is specified to ensure the script completes in a reasonable time
        # during verification, or we can run on the full set if the environment allows.
        # Given the "real data" constraint, we will attempt to load the full train split
        # but if memory/time is a concern, a limit can be set. 
        # For this implementation, we will NOT set a hard limit by default to satisfy "real dataset",
        # but the user can pass an environment variable or modify the call if needed.
        # However, to ensure the script is robust for the "execution stage" which might have limits,
        # we will extract ALL available data as per the "real data" requirement.
        # If the datasets are too large for the runner, the runner will fail, which is the correct behavior
        # (fail loudly) rather than faking data.
        
        static_data = extract_static_qa(limit_per_dataset=None)
        
        if not static_data:
            logger.warning("No data extracted. Check dataset availability.")
            return

        write_jsonl(static_data, str(output_path))
        logger.info("Static extraction completed successfully.")

    except Exception as e:
        logger.error(f"Static extraction failed: {e}")
        # Re-raise to ensure the script exits with non-zero code on failure
        raise

if __name__ == "__main__":
    main()

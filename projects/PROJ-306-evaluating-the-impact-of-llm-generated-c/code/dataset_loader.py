import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml

# The `datasets` library is required for loading benchmark datasets.
# It is listed in `requirements.txt`.
import datasets

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions for loading and persisting raw benchmark data
# ----------------------------------------------------------------------
def load_mbpp_dataset() -> datasets.DatasetDict:
    """
    Load the MBPP dataset using the HuggingFace `datasets` library.
    Returns the DatasetDict containing train/validation splits.
    """
    logger.info("Loading MBPP dataset...")
    return datasets.load_dataset("mbpp")

def save_raw_mbpp_files(dataset: datasets.DatasetDict, raw_dir: Path) -> None:
    """
    Persist each MBPP record as a JSON file under ``raw_dir``.
    The directory structure will be ``raw_dir/<task_id>.json``.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    for split_name, split in dataset.items():
        for idx, record in enumerate(split):
            task_id = f"MBPP/{record.get('task_id', idx)}"
            out_path = raw_dir / f"{task_id.replace('/', '_')}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

def load_humaneval_dataset() -> datasets.DatasetDict:
    """
    Load the HumanEval dataset. The verified source is
    ``openai/openai_humaneval``.
    """
    logger.info("Loading HumanEval dataset...")
    return datasets.load_dataset("openai/openai_humaneval")

def save_raw_humaneval_files(dataset: datasets.DatasetDict, raw_dir: Path) -> None:
    """
    Persist each HumanEval record as a JSON file under ``raw_dir``.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    for split_name, split in dataset.items():
        for idx, record in enumerate(split):
            task_id = f"HumanEval/{record.get('task_id', idx)}"
            out_path = raw_dir / f"{task_id.replace('/', '_')}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------
# Catalog creation & validation
# ----------------------------------------------------------------------
def extract_code_patterns(solution: str) -> List[str]:
    """
    Very lightweight placeholder that extracts simple code patterns.
    Real implementation would use static analysis; for now we return an empty list.
    """
    # Placeholder: real pattern extraction logic can be added later.
    return []

def validate_and_create_catalog(
    mbpp_dataset: Optional[datasets.DatasetDict] = None,
    humaneval_dataset: Optional[datasets.DatasetDict] = None,
) -> List[Dict[str, Any]]:
    """
    Combine MBPP and HumanEval entries into a single catalog with the required fields:
    - task_id
    - prompt
    - human_solution
    - test_suite_path
    - difficulty
    - code_patterns
    """
    catalog: List[Dict[str, Any]] = []

    # Helper to process a generic split
    def _process_record(record: Dict[str, Any], source: str) -> None:
        task_id = f"{source}/{record.get('task_id')}"
        prompt = record.get("prompt") or record.get("instruction") or ""
        # Human solution may be under different keys depending on dataset
        human_solution = (
            record.get("canonical_solution")
            or record.get("solution")
            or record.get("code")
            or ""
        )
        # For test suite, we store the raw string; later ``test_transformer`` will
        # turn it into a .py file.
        test_suite = record.get("test") or record.get("test_cases") or ""
        test_suite_path = f"data/benchmarks/processed/tests/{task_id.replace('/', '_')}_test.py"

        # Difficulty is not provided; we assign a placeholder based on source.
        difficulty = "medium"

        code_patterns = extract_code_patterns(human_solution)

        catalog.append(
            {
                "task_id": task_id,
                "prompt": prompt,
                "human_solution": human_solution,
                "test_suite_path": test_suite_path,
                "difficulty": difficulty,
                "code_patterns": code_patterns,
            }
        )

    if mbpp_dataset:
        for split in mbpp_dataset.values():
            for rec in split:
                _process_record(rec, "MBPP")

    if humaneval_dataset:
        for split in humaneval_dataset.values():
            for rec in split:
                _process_record(rec, "HumanEval")

    return catalog

def validate_and_save_catalog(
    output_path: Path = Path("data/benchmarks/processed/catalog.json"),
    mbpp_dir: Path = Path("data/benchmarks/raw/mbpp"),
    humaneval_dir: Path = Path("data/benchmarks/raw/humaneval"),
) -> None:
    """
    Load the raw datasets (or fetch them if missing), validate required fields,
    and write a normalized JSON catalog to ``output_path``.
    """
    # Ensure raw directories exist
    mbpp_dir.mkdir(parents=True, exist_ok=True)
    humaneval_dir.mkdir(parents=True, exist_ok=True)

    # Load datasets (this will download if not cached)
    mbpp_dataset = load_mbpp_dataset()
    humaneval_dataset = load_humaneval_dataset()

    # Save raw files for traceability
    save_raw_mbpp_files(mbpp_dataset, mbpp_dir)
    save_raw_humaneval_files(humaneval_dataset, humaneval_dir)

    # Create and validate catalog entries
    catalog = validate_and_create_catalog(mbpp_dataset, humaneval_dataset)

    # Write the catalog
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    logger.info(f"Catalog written to {output_path} with {len(catalog)} entries.")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Simple CLI to (re)generate the benchmark catalog.
    """
    logging.basicConfig(level=logging.INFO)
    validate_and_save_catalog()

if __name__ == "__main__":
    main()

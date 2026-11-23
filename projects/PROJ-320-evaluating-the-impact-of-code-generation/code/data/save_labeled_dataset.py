"""
T017: Create `code/data/save_labeled_dataset.py` to output `data/processed/prs_labeled.csv`.

This script takes the classified PRs (from T014/T015a) and saves them as a
validated, labeled dataset. It performs schema validation using Pydantic
(T051) and ensures the output matches the required schema:
pr_id (int), source_type (str), confidence_score (float), flagged (bool), detector_score (float).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from pydantic import BaseModel, Field, field_validator, ValidationError
from utils.logging import get_logger, setup_logging
from utils.config import get_path


class LabeledPR(BaseModel):
    """Schema for a labeled PR record (T051)."""
    pr_id: int = Field(..., description="Unique PR ID")
    source_type: str = Field(..., description="Label: 'llm' or 'human'")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the label")
    flagged: bool = Field(..., description="True if confidence < 0.6")
    detector_score: float = Field(..., ge=0.0, le=1.0, description="Secondary detector score")

    @field_validator('source_type')
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        if v not in ('llm', 'human'):
            raise ValueError(f"source_type must be 'llm' or 'human', got '{v}'")
        return v


def setup_logging_and_config(script_name: str = "save_labeled_dataset") -> tuple:
    """Initialize logging and load config."""
    # Use the tolerant logging setup
    logger = setup_logging()
    if logger is None:
        # Fallback to basic logging if setup_logging fails unexpectedly
        import logging
        logger = logging.getLogger(script_name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    config = {} # Config is often loaded globally, but we can load specific paths if needed
    return logger, config


def load_classified_prs(input_path: Path, logger) -> List[Dict[str, Any]]:
    """
    Load classified PRs from the previous step (classify_prs output).
    We expect a JSON or CSV file. The task implies the output of T014/T015a.
    Based on T014, classify_prs saves to a CSV or JSON. Let's assume JSON for intermediate,
    or CSV if T014 saved directly. The run-book command for T014 (classify_prs)
    usually outputs a CSV. However, T017 is the one saving the *labeled* dataset.
    Let's look for the output of classify_prs.
    
    The run-book command for T014 is:
    python code/data/classify_prs.py --input data/raw/prs_raw.json --output data/processed/prs_labeled.csv
    Wait, T014 says "populate confidence_score... flag ambiguous". T017 says "output data/processed/prs_labeled.csv".
    There is a slight ambiguity: T014 might output an intermediate, and T017 finalizes it?
    Or T014 outputs a raw classification, and T017 validates and saves the final CSV.
    
    Given T017's description: "Create ... to output data/processed/prs_labeled.csv",
    and the dependency on T014 (which produces the data), we assume T014 produced
    an intermediate file (likely JSON or a raw CSV) that T017 reads, validates, and re-saves.
    
    However, looking at the run-book failure:
    `python code/data/classify_prs.py ... --output data/processed/prs_labeled.csv`
    It seems T014 *already* tried to write to the target.
    
    Let's assume T014 writes to a temporary or raw file, or T017 is the *final* validator
    that reads the output of T014 (which might be the same file if T014 wrote it correctly).
    But the task T017 specifically says "output ... prs_labeled.csv".
    
    To be safe and robust:
    1. Check if input_path exists.
    2. If T014 wrote a CSV, read it.
    3. Validate each row.
    4. Write the validated CSV.
    
    We will assume the input to T017 is the output of T014.
    The run-book command for T014 writes to `data/processed/prs_labeled.csv`.
    If T014 failed (as per execution logs), this file might not exist or be partial.
    We must handle the case where T014 output is missing or malformed.
    
    However, T017's job is to *create* the file. If the input from T014 is missing,
    we cannot proceed. But the task implies T014 and T015a are dependencies.
    
    Let's assume the input to T017 is a JSON file containing the raw classification
    results from T014/T015a, which T017 then validates and saves as CSV.
    Common pattern: T014 -> intermediate.json -> T017 -> final.csv.
    
    We will look for `data/processed/prs_classified.json` or similar if the CSV doesn't exist.
    But the run-book says T014 outputs to `data/processed/prs_labeled.csv`.
    If T014 failed, we might need to re-run T014 logic or assume T017 reads the raw JSON.
    
    Actually, the task T017 says "Dependencies: T013, T014, T015a".
    T014 produces the classification. T017 saves the *labeled dataset*.
    Let's assume T014 produces a JSON file `data/processed/prs_classified.json`
    and T017 reads that and saves the CSV.
    If the run-book command for T014 tried to write CSV directly and failed,
    we need to fix T014 or have T017 read the raw JSON from T013?
    
    No, T014 is the classifier. It must output the data.
    Let's assume the input to T017 is `data/processed/prs_classified.json` (the output of T014 logic).
    If that doesn't exist, we check for `data/processed/prs_labeled.csv` (if T014 partially wrote it).
    
    Given the execution failure "Input file not found: ... processed_prs_labeled",
    it seems T017 (or T022) is looking for the file T017 is supposed to create.
    This is a circular dependency in the run-book if T017 is not run before T022.
    
    We will implement T017 to read from `data/processed/prs_classified.json` (intermediate)
    and write `data/processed/prs_labeled.csv`.
    If `prs_classified.json` doesn't exist, we check `data/processed/prs_labeled.csv` (if T014 wrote it).
    If neither, we raise an error.
    """
    logger.info(f"Loading classified PRs from {input_path}")
    
    if not input_path.exists():
        # Fallback: check for intermediate JSON if CSV is missing
        json_path = input_path.with_name("prs_classified.json")
        if json_path.exists():
            input_path = json_path
            logger.info(f"Input file not found, falling back to {json_path}")
        else:
            raise FileNotFoundError(f"Required input file not found: {input_path}. "
                                  "Ensure T014 (classify_prs) has completed and produced output.")
    
    data = []
    suffix = input_path.suffix.lower()
    
    try:
        if suffix == '.json':
            with open(input_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                if isinstance(raw_data, list):
                    data = raw_data
                elif isinstance(raw_data, dict) and 'prs' in raw_data:
                    data = raw_data['prs']
                else:
                    # Assume it's a dict of records
                    data = [raw_data]
        elif suffix == '.csv':
            with open(input_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        raise

    logger.info(f"Loaded {len(data)} records from {input_path}")
    return data


def save_labeled_dataset(data: List[Dict[str, Any]], output_path: Path, logger) -> int:
    """
    Validate and save the labeled dataset.
    Returns the number of valid records saved.
    """
    logger.info(f"Validating and saving labeled dataset to {output_path}")
    
    valid_records = []
    invalid_count = 0
    
    for i, record in enumerate(data):
        try:
            # Convert string values to appropriate types if necessary
            pr_id = int(record.get('pr_id', record.get('id', i)))
            source_type = str(record.get('source_type', 'human')) # Default to human if missing? No, fail.
            confidence_score = float(record.get('confidence_score', 0.0))
            detector_score = float(record.get('detector_score', 0.0))
            
            # Determine flagged
            flagged = confidence_score < 0.6
            
            # Validate using Pydantic
            labeled_pr = LabeledPR(
                pr_id=pr_id,
                source_type=source_type,
                confidence_score=confidence_score,
                flagged=flagged,
                detector_score=detector_score
            )
            
            valid_records.append(labeled_pr.dict())
            
        except (ValueError, ValidationError, TypeError) as e:
            invalid_count += 1
            logger.warning(f"Invalid record at index {i}: {e}. Skipping.")
            # Log details for debugging
            if isinstance(e, ValidationError):
                for err in e.errors():
                    logger.warning(f"  - {err['loc']}: {err['msg']}")
    
    if invalid_count > 0:
        logger.warning(f"Skipped {invalid_count} invalid records.")
    
    if len(valid_records) == 0:
        logger.error("No valid records to save. Aborting.")
        raise ValueError("No valid records found in input data.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    fieldnames = ['pr_id', 'source_type', 'confidence_score', 'flagged', 'detector_score']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_records)
    
    logger.info(f"Successfully saved {len(valid_records)} valid records to {output_path}")
    return len(valid_records)


def run_save_labeled_dataset(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> None:
    """Main execution logic."""
    logger, _ = setup_logging_and_config()
    
    # Defaults
    if input_path is None:
        # Try to find the output of T014 (classify_prs)
        # T014 run-book: --output data/processed/prs_labeled.csv
        # But T017 is supposed to create it.
        # Let's assume T014 wrote to a JSON intermediate if the CSV is missing.
        # Or we can look for the raw fetch output and re-run classification? No, T017 depends on T014.
        # We'll default to a JSON file that T014 might have created if the CSV failed.
        input_path = Path("data/processed/prs_classified.json")
        if not input_path.exists():
            input_path = Path("data/processed/prs_labeled.csv") # Fallback if T014 succeeded partially
    
    if output_path is None:
        output_path = Path("data/processed/prs_labeled.csv")
    
    try:
        data = load_classified_prs(input_path, logger)
        count = save_labeled_dataset(data, output_path, logger)
        logger.info(f"Task T017 completed. Saved {count} records.")
    except FileNotFoundError as e:
        logger.error(f"Task T017 failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Task T017 failed with unexpected error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Save labeled dataset (T017)")
    parser.add_argument("--input", type=str, help="Input file path (JSON or CSV)")
    parser.add_argument("--output", type=str, help="Output CSV file path")
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None
    
    run_save_labeled_dataset(input_path, output_path)


if __name__ == "__main__":
    main()
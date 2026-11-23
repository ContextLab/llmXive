import os
import json
import glob
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import logging
from logging_config import setup_logger

logger = setup_logger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    pass

def check_data_completeness(data: List[Dict[str, Any]], threshold: float = 0.95) -> bool:
    """
    Check if data rows meet the completeness threshold.

    Args:
        data: List of dictionaries representing data rows.
        threshold: Minimum completeness ratio (0.0 to 1.0).

    Returns:
        bool: True if all rows meet the threshold.

    Raises:
        DataValidationError: If completeness is below threshold.
    """
    if not data:
        raise DataValidationError("Data is empty.")

    for i, row in enumerate(data):
        total_keys = len(row)
        if total_keys == 0:
            continue
        filled_keys = sum(1 for v in row.values() if v is not None and v != "")
        completeness = filled_keys / total_keys
        if completeness < threshold:
            logger.error(f"Row {i} has completeness {completeness:.2f} < {threshold}")
            raise DataValidationError(f"Data completeness check failed: Row {i} is below threshold.")

    logger.info(f"Data completeness check passed (threshold: {threshold}).")
    return True

def check_metadata_matching(ai_metadata: List[Dict[str, Any]], human_metadata: List[Dict[str, Any]]) -> bool:
    """
    Check if AI and Human metadata match in key fields (pose, lighting).

    Args:
        ai_metadata: List of AI stimulus metadata.
        human_metadata: List of Human stimulus metadata.

    Returns:
        bool: True if metadata matches.

    Raises:
        DataValidationError: If metadata does not match.
    """
    if not ai_metadata or not human_metadata:
        raise DataValidationError("Metadata lists are empty.")

    if len(ai_metadata) != len(human_metadata):
        raise DataValidationError(f"Metadata count mismatch: AI={len(ai_metadata)}, Human={len(human_metadata)}")

    matching_fields = ['pose', 'lighting']
    for i, (ai_meta, human_meta) in enumerate(zip(ai_metadata, human_metadata)):
        for field in matching_fields:
            ai_val = ai_meta.get(field)
            human_val = human_meta.get(field)
            if ai_val != human_val:
                logger.error(f"Metadata mismatch at index {i} for field '{field}': AI={ai_val}, Human={human_val}")
                raise DataValidationError(f"Metadata mismatch: {field} differs between AI and Human sets.")

    logger.info("Metadata matching check passed (pose, lighting).")
    return True

def check_visual_indistinguishability(pretest_path: str = "data/pretest/results.json") -> bool:
    """
    Load and parse data/pretest/results.json to verify visual indistinguishability.
    Requires p_value > 0.05.

    Args:
        pretest_path: Path to the pre-test results JSON file.

    Returns:
        bool: True if p > 0.05.

    Raises:
        DataValidationError: If file missing, malformed, or p <= 0.05.
    """
    path = Path(pretest_path)
    if not path.exists():
        logger.error(f"Pre-test results file not found: {path}")
        raise DataValidationError(f"Pre-test results file not found: {path}")

    try:
        with open(path, 'r') as f:
            results = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {path}: {e}")
        raise DataValidationError(f"Invalid JSON in pre-test results: {e}")

    if "p_value" not in results:
        logger.error("Pre-test results missing 'p_value' key.")
        raise DataValidationError("Pre-test results missing 'p_value' key.")

    p_value = results["p_value"]
    logger.info(f"Pre-test p-value: {p_value}")

    if p_value <= 0.05:
        logger.error(f"Visual indistinguishability failed: p={p_value} <= 0.05")
        raise DataValidationError(f"Visual indistinguishability check failed: p={p_value} <= 0.05")

    logger.info("Visual indistinguishability check passed (p > 0.05).")
    return True

def run_all_validations() -> Dict[str, Any]:
    """
    Run all validation checks and return a summary.

    Returns:
        Dict containing validation results.
    """
    results = {
        "completeness": False,
        "metadata_matching": False,
        "visual_indistinguishability": False,
        "all_passed": False
    }

    try:
        # Load processed data for completeness check
        processed_dir = Path("data/processed")
        if processed_dir.exists():
            data_files = glob.glob(str(processed_dir / "*.jsonl"))
            if not data_files:
                logger.warning("No processed data files found for completeness check.")
            else:
                data = []
                for f_path in data_files:
                    with open(f_path, 'r') as f:
                        for line in f:
                            if line.strip():
                                data.append(json.loads(line))
                check_data_completeness(data)
                results["completeness"] = True
        else:
            logger.warning("Processed data directory not found. Skipping completeness check.")

        # Load metadata for matching check
        ai_meta = []
        human_meta = []
        ai_dir = Path("data/stimuli/ai")
        human_dir = Path("data/stimuli/human")

        if ai_dir.exists() and human_dir.exists():
            ai_files = sorted(ai_dir.glob("*.json"))
            human_files = sorted(human_dir.glob("*.json"))

            if ai_files and human_files:
                for f in ai_files:
                    with open(f, 'r') as file:
                        ai_meta.append(json.load(file))
                for f in human_files:
                    with open(f, 'r') as file:
                        human_meta.append(json.load(file))
                check_metadata_matching(ai_meta, human_meta)
                results["metadata_matching"] = True
        else:
            logger.warning("Stimuli directories not found. Skipping metadata matching check.")

        # Check visual indistinguishability
        check_visual_indistinguishability()
        results["visual_indistinguishability"] = True

        results["all_passed"] = all([
            results["completeness"],
            results["metadata_matching"],
            results["visual_indistinguishability"]
        ])

    except DataValidationError as e:
        logger.error(f"Validation failed: {e}")
        results["error"] = str(e)

    return results

def main():
    """Main entry point for data validation script."""
    import argparse

    parser = argparse.ArgumentParser(description="Run data validation checks.")
    parser.add_argument("--check-stimuli", action="store_true", help="Run metadata matching check.")
    parser.add_argument("--check-pretest", action="store_true", help="Run visual indistinguishability check.")
    parser.add_argument("--check-completeness", action="store_true", help="Run data completeness check.")
    parser.add_argument("--all", action="store_true", help="Run all checks.")
    args = parser.parse_args()

    if not any([args.check_stimuli, args.check_pretest, args.check_completeness, args.all]):
        args.all = True

    results = {}

    if args.all or args.check_completeness:
        try:
            processed_dir = Path("data/processed")
            if processed_dir.exists():
                data_files = glob.glob(str(processed_dir / "*.jsonl"))
                if data_files:
                    data = []
                    for f_path in data_files:
                        with open(f_path, 'r') as f:
                            for line in f:
                                if line.strip():
                                    data.append(json.loads(line))
                    check_data_completeness(data)
                    results["completeness"] = "PASSED"
                else:
                    results["completeness"] = "SKIPPED (No data)"
            else:
                results["completeness"] = "SKIPPED (Directory missing)"
        except DataValidationError as e:
            results["completeness"] = f"FAILED: {e}"

    if args.all or args.check_stimuli:
        try:
            ai_meta = []
            human_meta = []
            ai_dir = Path("data/stimuli/ai")
            human_dir = Path("data/stimuli/human")

            if ai_dir.exists() and human_dir.exists():
                ai_files = sorted(ai_dir.glob("*.json"))
                human_files = sorted(human_dir.glob("*.json"))

                if ai_files and human_files:
                    for f in ai_files:
                        with open(f, 'r') as file:
                            ai_meta.append(json.load(file))
                    for f in human_files:
                        with open(f, 'r') as file:
                            human_meta.append(json.load(file))
                    check_metadata_matching(ai_meta, human_meta)
                    results["metadata_matching"] = "PASSED"
                else:
                    results["metadata_matching"] = "SKIPPED (No metadata files)"
            else:
                results["metadata_matching"] = "SKIPPED (Directories missing)"
        except DataValidationError as e:
            results["metadata_matching"] = f"FAILED: {e}"

    if args.all or args.check_pretest:
        try:
            check_visual_indistinguishability()
            results["visual_indistinguishability"] = "PASSED"
        except DataValidationError as e:
            results["visual_indistinguishability"] = f"FAILED: {e}"

    print(json.dumps(results, indent=2))

    if any("FAILED" in v for v in results.values()):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
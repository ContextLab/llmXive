"""
Exclusion Logger for RULER Dataset Integrity.

This module provides functionality to detect and log samples in the RULER dataset
that are corrupted or missing the required "needle" strings.
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from utils.logger import get_logger_for_task

# Initialize logger for this module
logger = get_logger_for_task("exclusion_logger")


def validate_needle_presence(sample: Dict[str, Any], needle_patterns: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validates that a RULER dataset sample contains the required needle string.

    Args:
        sample: A dictionary representing a single RULER dataset entry.
        needle_patterns: Optional list of regex patterns or strings to search for.
                       If None, defaults to looking for 'needle' or 'target' keys.

    Returns:
        Tuple[bool, Optional[str]]:
            - True if needle is found (sample is valid).
            - False if needle is missing or corrupted (sample is invalid).
            - The second element is an error message if invalid, None otherwise.
    """
    # Default patterns if none provided
    if needle_patterns is None:
        # Common keys in RULER datasets that might hold the needle
        needle_patterns = ["needle", "target", "query", "answer"]

    # Check for the presence of the needle text
    # RULER datasets often have a 'needle' field containing the hidden string
    # or a 'question' field where the needle is embedded.
    text_content = ""
    for key in ["context", "text", "input", "prompt"]:
        if key in sample and isinstance(sample[key], str):
            text_content = sample[key]
            break

    if not text_content:
        # If we can't find text content, check if 'needle' is a separate field
        if "needle" in sample and isinstance(sample["needle"], str):
            text_content = sample["needle"]
        else:
            return False, "Missing text content and needle field in sample"

    # If specific patterns are provided, check against them
    if needle_patterns:
        for pattern in needle_patterns:
            # Try regex match first
            try:
                if re.search(pattern, text_content, re.IGNORECASE):
                    return True, None
            except re.error:
                # If not a valid regex, try simple string containment
                if pattern.lower() in text_content.lower():
                    return True, None
    
    # If we reach here, no needle was found
    return False, "Required needle string not found in sample content"


def log_exclusion(sample_id: Any, reason: str, sample_data: Optional[Dict[str, Any]] = None):
    """
    Logs the exclusion of a sample due to corruption or missing needle.

    Args:
        sample_id: The identifier of the excluded sample.
        reason: The reason for exclusion (e.g., "missing needle", "corrupted").
        sample_data: Optional snippet of the sample data for debugging.
    """
    log_entry = {
        "event": "sample_excluded",
        "sample_id": str(sample_id),
        "reason": reason,
        "timestamp": None  # Handled by logger
    }
    
    if sample_data:
        # Log a sanitized snippet (avoid logging massive context)
        snippet = {}
        for k, v in sample_data.items():
            if isinstance(v, str) and len(v) > 100:
                snippet[k] = v[:100] + "..."
            else:
                snippet[k] = v
        log_entry["sample_snippet"] = snippet
    
    logger.warning("Sample excluded", extra=log_entry)


def scan_dataset_for_exclusions(dataset: Any, needle_patterns: Optional[List[str]] = None, max_samples: Optional[int] = None) -> Dict[str, Any]:
    """
    Scans a dataset for samples that should be excluded due to corruption or missing needles.

    Args:
        dataset: A HuggingFace Dataset object or iterable.
        needle_patterns: Patterns to search for in the sample content.
        max_samples: Optional limit on the number of samples to scan.

    Returns:
        A dictionary containing:
            - total_scanned: Number of samples scanned.
            - excluded_count: Number of samples excluded.
            - exclusion_reasons: Dictionary mapping reasons to counts.
            - sample_ids_excluded: List of excluded sample IDs (if available).
    """
    results = {
        "total_scanned": 0,
        "excluded_count": 0,
        "exclusion_reasons": {},
        "sample_ids_excluded": []
    }

    logger.info("Starting dataset scan for exclusions", extra={"task": "scan_dataset"})

    try:
        # Determine if dataset has a length attribute (HuggingFace Dataset)
        if hasattr(dataset, "__len__"):
            total = len(dataset)
            logger.info(f"Dataset size: {total}")
        else:
            total = None
            logger.info("Dataset size unknown (streaming mode)")

        iterator = iter(dataset)
        if max_samples:
            import itertools
            iterator = itertools.islice(iterator, max_samples)

        for idx, sample in enumerate(iterator):
            results["total_scanned"] += 1

            # Get sample ID if available
            sample_id = sample.get("id", sample.get("index", idx))

            # Validate needle presence
            is_valid, error_msg = validate_needle_presence(sample, needle_patterns)

            if not is_valid:
                results["excluded_count"] += 1
                
                # Categorize reason
                reason = error_msg if error_msg else "unknown_corruption"
                results["exclusion_reasons"][reason] = results["exclusion_reasons"].get(reason, 0) + 1
                results["sample_ids_excluded"].append(str(sample_id))

                # Log the exclusion
                log_exclusion(sample_id, reason, sample)

            # Progress logging every 1000 samples
            if results["total_scanned"] % 1000 == 0:
                logger.info(f"Scanned {results['total_scanned']} samples, excluded {results['excluded_count']} so far.")

    except Exception as e:
        logger.error(f"Error during dataset scan: {str(e)}", exc_info=True)
        raise

    logger.info(
        "Dataset scan completed",
        extra={
            "task": "scan_dataset",
            "total_scanned": results["total_scanned"],
            "excluded_count": results["excluded_count"],
            "exclusion_rate": results["excluded_count"] / max(results["total_scanned"], 1)
        }
    )

    return results


def main():
    """
    Entry point for running the exclusion logger as a standalone script.
    This is useful for pre-processing checks before running the main experiment.
    """
    import argparse
    from data.ruler_loader import load_ruler_dataset

    parser = argparse.ArgumentParser(description="Scan RULER dataset for exclusions")
    parser.add_argument("--dataset_path", type=str, default="data/raw/ruler_dataset", help="Path to the RULER dataset")
    parser.add_argument("--max_samples", type=int, default=None, help="Maximum number of samples to scan")
    parser.add_argument("--needle_patterns", type=str, nargs="+", default=None, help="Patterns to search for as needles")
    args = parser.parse_args()

    # Load dataset
    try:
        dataset = load_ruler_dataset(args.dataset_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        return 1

    # Run scan
    results = scan_dataset_for_exclusions(
        dataset,
        needle_patterns=args.needle_patterns,
        max_samples=args.max_samples
    )

    # Print summary
    print("\n" + "="*50)
    print("EXCLUSION SCAN SUMMARY")
    print("="*50)
    print(f"Total samples scanned: {results['total_scanned']}")
    print(f"Samples excluded: {results['excluded_count']}")
    if results['total_scanned'] > 0:
        print(f"Exclusion rate: {results['excluded_count'] / results['total_scanned']:.2%}")
    
    if results['exclusion_reasons']:
        print("\nExclusion reasons:")
        for reason, count in results['exclusion_reasons'].items():
            print(f"  - {reason}: {count}")
    
    if results['sample_ids_excluded']:
        print(f"\nFirst 10 excluded sample IDs:")
        for sid in results['sample_ids_excluded'][:10]:
            print(f"  - {sid}")
    print("="*50)

    return 0 if results['excluded_count'] == 0 else 0  # Return 0 even if exclusions found, just logging


if __name__ == "__main__":
    import sys
    sys.exit(main())

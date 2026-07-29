import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from utils.logger import get_logger_for_task

def validate_needle_presence(sample: Dict[str, Any], needle_field: str = "needle", context_field: str = "context") -> Tuple[bool, str]:
    """
    Validates if the 'needle' string exists within the 'context' field of a dataset sample.
    
    Args:
        sample: A dictionary representing a single dataset sample.
        needle_field: The key in the sample dict containing the target string.
        context_field: The key in the sample dict containing the text to search.
        
    Returns:
        A tuple (is_valid, reason). 
        is_valid: True if needle is found, False otherwise.
        reason: A string describing the result (e.g., "Found", "Missing needle string", "Context empty").
    """
    if not isinstance(sample, dict):
        return False, "Sample is not a dictionary"

    needle = sample.get(needle_field)
    context = sample.get(context_field)

    if needle is None:
        return False, f"Missing '{needle_field}' key in sample"
    
    if context is None:
        return False, f"Missing '{context_field}' key in sample"

    if not isinstance(needle, str) or not isinstance(context, str):
        return False, f"Invalid types: needle={type(needle)}, context={type(context)}"

    if not needle:
        return False, "Needle string is empty"

    if not context:
        return False, "Context string is empty"

    if needle in context:
        return True, "Found"
    else:
        return False, "Needle string not found in context"

def log_exclusion(sample_id: str, reason: str, logger: logging.Logger, sample_preview: Optional[str] = None):
    """
    Logs a single exclusion event with structured details.
    
    Args:
        sample_id: Unique identifier for the sample (e.g., index or ID).
        reason: The reason for exclusion (from validate_needle_presence).
        logger: The logger instance to use.
        sample_preview: Optional preview of the sample content for debugging.
    """
    log_data = {
        "event": "sample_excluded",
        "sample_id": sample_id,
        "reason": reason,
        "task": "T025_exclusion_logging"
    }
    if sample_preview:
        log_data["preview"] = sample_preview[:200] + "..." if len(sample_preview) > 200 else sample_preview
    
    logger.warning(f"Excluding sample {sample_id}: {reason}", extra=log_data)

def scan_dataset_for_exclusions(dataset: List[Dict[str, Any]], logger: Optional[logging.Logger] = None, needle_field: str = "needle", context_field: str = "context") -> Dict[str, Any]:
    """
    Scans a dataset list for samples missing the needle string and logs exclusions.
    
    Args:
        dataset: List of sample dictionaries.
        logger: Logger instance. If None, a default logger is created.
        needle_field: Key for the needle string.
        context_field: Key for the context string.
        
    Returns:
        A dictionary containing exclusion statistics:
        {
            "total_samples": int,
            "excluded_count": int,
            "valid_count": int,
            "exclusion_reasons": Dict[str, int]
        }
    """
    if logger is None:
        logger = get_logger_for_task("T025")
        logger.setLevel(logging.WARNING)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)

    total_samples = len(dataset)
    excluded_count = 0
    exclusion_reasons: Dict[str, int] = {}

    logger.info(f"Scanning {total_samples} samples for needle integrity...")

    for idx, sample in enumerate(dataset):
        sample_id = sample.get("id", f"index_{idx}")
        is_valid, reason = validate_needle_presence(sample, needle_field, context_field)
        
        if not is_valid:
            excluded_count += 1
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            # Log the first few exclusions for debugging, then summarize
            if excluded_count <= 5:
                log_exclusion(sample_id, reason, logger, sample.get(context_field, ""))
            elif excluded_count == 6:
                logger.warning("Additional exclusions suppressed in logs. Check summary stats.")

    valid_count = total_samples - excluded_count

    logger.info(f"Scan complete. Total: {total_samples}, Excluded: {excluded_count}, Valid: {valid_count}")
    
    if excluded_count > 0:
        logger.warning(f"Exclusion Summary: {exclusion_reasons}")

    return {
        "total_samples": total_samples,
        "excluded_count": excluded_count,
        "valid_count": valid_count,
        "exclusion_reasons": exclusion_reasons
    }

def main():
    """
    Entry point for running the exclusion scan on a dataset.
    This function demonstrates the logging of exclusion counts.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from data.loader import download_and_verify_ruler
    from utils.logger import setup_logger
    
    logger = setup_logger("T025_ExclusionScan")
    
    # Download/Verify data first to ensure we have real data to scan
    # This assumes the standard RULER dataset structure
    try:
        # Attempt to load a small subset for demonstration or the full dataset if available
        # Using the loader's verify function which returns the dataset object
        dataset = download_and_verify_ruler()
        
        # Convert to list if it's a streaming dataset or map object for scanning
        # Note: For very large datasets, this might need chunking, but for T025 
        # we are focusing on the logging logic.
        if hasattr(dataset, 'to_list'):
            data_list = dataset.to_list()
        else:
            data_list = list(dataset)
            
        if not data_list:
            logger.error("Dataset is empty or could not be loaded.")
            return

        # Run the scan
        results = scan_dataset_for_exclusions(data_list, logger)
        
        # Print summary to stdout as well
        print(f"\n--- T025 Exclusion Scan Results ---")
        print(f"Total Samples: {results['total_samples']}")
        print(f"Excluded Count: {results['excluded_count']}")
        print(f"Valid Count: {results['valid_count']}")
        print(f"Reasons: {results['exclusion_reasons']}")
        print("-------------------------------------\n")
        
    except Exception as e:
        logger.critical(f"Failed to scan dataset: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

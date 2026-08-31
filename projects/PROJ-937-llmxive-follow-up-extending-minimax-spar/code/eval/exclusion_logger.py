import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from utils.logger import get_logger_for_task

def validate_needle_presence(sample: Dict[str, Any], needle_key: str = "needle") -> Tuple[bool, Optional[str]]:
    """
    Validate that a RULER dataset sample contains a valid needle string.
    
    Args:
        sample: A dictionary representing a dataset row.
        needle_key: The key name where the needle string is expected.
        
    Returns:
        Tuple of (is_valid, reason). 
        is_valid is True if needle exists and is non-empty.
        reason is None if valid, or a string explaining why it's invalid.
    """
    if needle_key not in sample:
        return False, f"Missing key '{needle_key}' in sample"
    
    needle = sample[needle_key]
    if needle is None:
        return False, f"Needle value is None"
    
    if not isinstance(needle, str):
        return False, f"Needle is not a string (type: {type(needle).__name__})"
    
    if len(needle.strip()) == 0:
        return False, "Needle string is empty or whitespace only"
    
    return True, None

def log_exclusion(sample_id: Any, reason: str, logger: logging.Logger) -> None:
    """
    Log a single exclusion event with structured context.
    
    Args:
        sample_id: The identifier of the excluded sample.
        reason: The reason for exclusion.
        logger: The logger instance to use.
    """
    logger.warning(
        "Sample excluded",
        extra={
            "event_type": "sample_exclusion",
            "sample_id": str(sample_id),
            "exclusion_reason": reason,
            "task_id": "T025"
        }
    )

def scan_dataset_for_exclusions(
    dataset: Any,
    logger: Optional[logging.Logger] = None,
    needle_key: str = "needle",
    corruption_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Scan the RULER dataset for corrupted samples or missing needles.
    
    This function iterates through the dataset, validates each sample,
    and logs exclusions. It returns a summary report of the scan.
    
    Args:
        dataset: The RULER dataset object (iterable of dicts).
        logger: Logger instance. If None, creates a temporary one.
        needle_key: Key name for the needle string.
        corruption_patterns: List of regex patterns that indicate corruption.
        
    Returns:
        A dictionary containing exclusion counts and reasons.
    """
    if logger is None:
        logger = get_logger_for_task("T025", level=logging.INFO)
    
    if corruption_patterns is None:
        corruption_patterns = [
            r"<corrupted>",
            r"<missing>",
            r"<error>",
            r"\[REDACTED\]"
        ]
    
    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in corruption_patterns]
    
    stats = {
        "total_samples": 0,
        "valid_samples": 0,
        "excluded_samples": 0,
        "exclusion_reasons": {
            "missing_needle_key": 0,
            "needle_is_none": 0,
            "needle_not_string": 0,
            "needle_empty": 0,
            "needle_corrupted": 0,
            "other_corruption": 0
        }
    }
    
    logger.info(f"Starting dataset scan for exclusions (needle_key='{needle_key}')")
    
    for idx, sample in enumerate(dataset):
        stats["total_samples"] += 1
        sample_id = sample.get("id", idx)
        
        # Check for missing or invalid needle
        is_valid, reason = validate_needle_presence(sample, needle_key)
        
        if not is_valid:
            stats["excluded_samples"] += 1
            log_exclusion(sample_id, reason, logger)
            
            # Categorize the reason
            if "Missing key" in reason:
                stats["exclusion_reasons"]["missing_needle_key"] += 1
            elif "is None" in reason:
                stats["exclusion_reasons"]["needle_is_none"] += 1
            elif "not a string" in reason:
                stats["exclusion_reasons"]["needle_not_string"] += 1
            elif "empty" in reason:
                stats["exclusion_reasons"]["needle_empty"] += 1
            else:
                stats["exclusion_reasons"]["other_corruption"] += 1
            continue
        
        # Check for corruption patterns in the needle
        needle = sample[needle_key]
        is_corrupted = False
        for pattern in compiled_patterns:
            if pattern.search(needle):
                is_corrupted = True
                break
        
        if is_corrupted:
            stats["excluded_samples"] += 1
            reason_str = f"Needle matches corruption pattern"
            log_exclusion(sample_id, reason_str, logger)
            stats["exclusion_reasons"]["needle_corrupted"] += 1
            continue
        
        stats["valid_samples"] += 1
        
        # Progress logging every 1000 samples
        if idx % 1000 == 0 and idx > 0:
            logger.info(f"Scanned {idx} samples: {stats['valid_samples']} valid, {stats['excluded_samples']} excluded")
    
    # Final summary
    exclusion_rate = (stats["excluded_samples"] / stats["total_samples"] * 100) if stats["total_samples"] > 0 else 0.0
    logger.info(
        f"Dataset scan complete: {stats['total_samples']} total, "
        f"{stats['valid_samples']} valid, {stats['excluded_samples']} excluded ({exclusion_rate:.2f}%)"
    )
    
    return stats

def main() -> None:
    """
    Entry point for running the exclusion scan on the RULER dataset.
    
    This function loads the RULER dataset, scans it for exclusions,
    and logs the results. It is designed to be run as a standalone script
    or called from the main pipeline.
    """
    from data.loader import download_and_verify_ruler
    from utils.logger import setup_logger
    
    # Setup logging
    logger = setup_logger("T025_ExclusionScan", level=logging.INFO)
    logger.info("Starting exclusion scan for RULER dataset")
    
    try:
        # Ensure dataset is downloaded
        data_path = Path("data/raw")
        if not data_path.exists():
            logger.info("Data directory not found. Downloading RULER dataset...")
            download_and_verify_ruler()
        
        # Load dataset (using the loader module)
        from data.ruler_loader import load_ruler_dataset
        dataset = load_ruler_dataset(data_path / "ruler_dataset.json")
        
        # Run scan
        results = scan_dataset_for_exclusions(dataset, logger=logger)
        
        # Log final report
        logger.info("Exclusion Scan Report:")
        logger.info(f"  Total Samples: {results['total_samples']}")
        logger.info(f"  Valid Samples: {results['valid_samples']}")
        logger.info(f"  Excluded Samples: {results['excluded_samples']}")
        logger.info("  Exclusion Reasons:")
        for reason, count in results['exclusion_reasons'].items():
            if count > 0:
                logger.info(f"    - {reason}: {count}")
                
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Exclusion scan failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    import json
    main()
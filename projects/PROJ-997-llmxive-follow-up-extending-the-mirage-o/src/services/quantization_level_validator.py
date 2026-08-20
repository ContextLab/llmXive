"""
Quantization Level Validator Module (T037).

This module verifies that the input dataset contains valid, non-empty logits
for all three quantization levels (INT4, INT8, FP8) before passing to T014 (gap_calculator).

It raises a specific MissingQuantizationLevelError if any level is missing or invalid.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class MissingQuantizationLevelError(Exception):
    """
    Raised when a sample is missing valid logits for a required quantization level.
    
    Attributes:
        sample_id: The ID of the problematic sample.
        missing_levels: List of quantization levels that are missing or invalid.
    """
    sample_id: str
    missing_levels: List[str]
    
    def __str__(self):
        return (f"Sample {self.sample_id} is missing valid logits for levels: "
                f"{', '.join(self.missing_levels)}. "
                "Cannot proceed with gap calculation.")

def validate_sample_logits(sample: Dict[str, Any]) -> None:
    """
    Validates a single sample for the presence and validity of logits 
    for INT4, INT8, and FP8 quantization levels.
    
    Args:
        sample: A dictionary representing a single training sample, expected 
                to contain a 'quantized_logits' key which is a dict mapping 
                quantization levels to logit lists/arrays.
                
    Raises:
        MissingQuantizationLevelError: If any required level is missing or invalid.
    """
    required_levels = ["INT4", "INT8", "FP8"]
    missing_levels = []
    
    quantized_logits = sample.get("quantized_logits")
    
    if not isinstance(quantized_logits, dict):
        # If the key exists but isn't a dict, or is missing entirely
        missing_levels = required_levels.copy()
    else:
        for level in required_levels:
            logits = quantized_logits.get(level)
            
            # Check if level key exists
            if logits is None:
                missing_levels.append(level)
                continue
            
            # Check if logits are empty or invalid
            if not isinstance(logits, (list, tuple)):
                missing_levels.append(level)
            elif len(logits) == 0:
                missing_levels.append(level)
            else:
                # Optional: Check if values are numeric (basic sanity check)
                # If logits are numpy arrays or torch tensors, convert to list or check shape
                try:
                    # Attempt to check length if it's an array-like object
                    if hasattr(logits, '__len__') and len(logits) == 0:
                        missing_levels.append(level)
                except (TypeError, AttributeError):
                    # If we can't check length, assume it's invalid if not a list/tuple
                    if not isinstance(logits, (list, tuple)):
                        missing_levels.append(level)

    if missing_levels:
        sample_id = sample.get("input_id", "unknown_id")
        raise MissingQuantizationLevelError(sample_id=sample_id, missing_levels=missing_levels)

def validate_dataset_batch(batch: List[Dict[str, Any]], logger: Optional[logging.Logger] = None) -> List[str]:
    """
    Validates a batch of samples and returns a list of sample IDs that failed validation.
    
    This function does NOT raise an exception for individual failures but collects them
    to allow T015 to skip specific bad samples while continuing the pipeline, 
    unless the batch is entirely invalid (handled by T015 logic).
    
    Args:
        batch: List of sample dictionaries.
        logger: Optional logger instance.
                
    Returns:
        List of sample IDs that failed validation.
    """
    failed_ids = []
    if logger is None:
        logger = logging.getLogger(__name__)
        
    for sample in batch:
        try:
            validate_sample_logits(sample)
        except MissingQuantizationLevelError as e:
            failed_ids.append(e.sample_id)
            logger.warning(f"Validation failed for sample {e.sample_id}: {e}")
            
    return failed_ids

def verify_level_coverage(batch: List[Dict[str, Any]], required_levels: List[str] = None) -> Dict[str, int]:
    """
    Verifies that a batch contains at least one valid sample for each required level.
    This is used to ensure T015's "FAIL LOUDLY if any level has ZERO samples" constraint.
    
    Args:
        batch: List of sample dictionaries.
        required_levels: List of levels to check (default: INT4, INT8, FP8).
        
    Returns:
        Dictionary mapping level to count of valid samples.
        
    Raises:
        MissingQuantizationLevelError: If any level has zero valid samples in the batch.
    """
    if required_levels is None:
        required_levels = ["INT4", "INT8", "FP8"]
        
    level_counts = {level: 0 for level in required_levels}
    
    for sample in batch:
        try:
            validate_sample_logits(sample)
            # If validation passes, count the levels present in this sample
            q_logits = sample.get("quantized_logits", {})
            for level in required_levels:
                if level in q_logits and q_logits[level]:
                    level_counts[level] += 1
        except MissingQuantizationLevelError:
            # Sample failed individual validation, skip counting
            continue
            
    missing_levels = [level for level, count in level_counts.items() if count == 0]
    
    if missing_levels:
        raise MissingQuantizationLevelError(
            sample_id="BATCH_TOTAL",
            missing_levels=missing_levels
        )
        
    return level_counts

def main():
    """
    Entry point for CLI execution (if needed for standalone testing).
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Example usage for testing
    test_sample_valid = {
        "input_id": "test_001",
        "quantized_logits": {
            "INT4": [0.1, 0.2, 0.3],
            "INT8": [0.1, 0.2, 0.3],
            "FP8": [0.1, 0.2, 0.3]
        }
    }
    
    test_sample_invalid = {
        "input_id": "test_002",
        "quantized_logits": {
            "INT4": [0.1, 0.2],
            "INT8": [],  # Empty
            "FP8": [0.1, 0.2]
        }
    }
    
    logger.info("Testing valid sample...")
    try:
        validate_sample_logits(test_sample_valid)
        logger.info("Valid sample passed.")
    except MissingQuantizationLevelError as e:
        logger.error(f"Unexpected failure: {e}")
        
    logger.info("Testing invalid sample...")
    try:
        validate_sample_logits(test_sample_invalid)
        logger.error("Invalid sample should have failed!")
    except MissingQuantizationLevelError as e:
        logger.info(f"Expected failure caught: {e}")

if __name__ == "__main__":
    main()

"""
Fetch Loop Implementation for US1.
Implements the logic to fetch noise segments one by one, inject, and validate
until >=12 valid events with complete spin metadata are found or max_attempts is reached.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.utils.logging import get_logger, log_metric, log_event_processed
from src.utils.config import ensure_dir
from src.data.download import fetch_gw_noise_segment
from src.data.inject import inject_synthetic_signal
from src.data.validate import validate_file

def process_single_attempt(
    attempt_num: int,
    output_dir: Path,
    logger: logging.Logger
) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Perform a single attempt: fetch noise -> inject -> validate.
    
    Returns:
        Tuple of (event_data_dict or None, is_valid)
    """
    logger.info(f"Attempt {attempt_num}: Fetching noise segment...")
    
    # 1. Fetch noise
    try:
        noise_file_path = fetch_gw_noise_segment(
            output_dir=output_dir / "raw",
            detector="LIGO",
            segment_duration=4.0  # seconds
        )
        if noise_file_path is None:
            logger.warning(f"Attempt {attempt_num}: Failed to fetch noise segment.")
            return None, False
    except Exception as e:
        logger.error(f"Attempt {attempt_num}: Error fetching noise: {e}")
        return None, False
    
    # 2. Inject synthetic signal
    logger.info(f"Attempt {attempt_num}: Injecting synthetic CBC signal...")
    try:
        injected_file_path, true_params = inject_synthetic_signal(
            noise_file_path=noise_file_path,
            output_dir=output_dir / "injected"
        )
        if injected_file_path is None or true_params is None:
            logger.warning(f"Attempt {attempt_num}: Injection failed.")
            return None, False
    except Exception as e:
        logger.error(f"Attempt {attempt_num}: Error during injection: {e}")
        return None, False
    
    # 3. Validate
    logger.info(f"Attempt {attempt_num}: Validating injected event...")
    try:
        is_valid, validation_report = validate_file(str(injected_file_path))
        
        if is_valid:
            # Extract event data for the return list
            event_data = {
                "file_path": str(injected_file_path),
                "true_parameters": true_params,
                "validation_report": validation_report
            }
            log_event_processed("US1_Injection", event_id=f"event_{attempt_num}")
            logger.info(f"Attempt {attempt_num}: Valid event created.")
            return event_data, True
        else:
            logger.warning(f"Attempt {attempt_num}: Validation failed. Report: {validation_report}")
            return None, False
            
    except Exception as e:
        logger.error(f"Attempt {attempt_num}: Error during validation: {e}")
        return None, False

def run_fetch_loop(
    target_count: int,
    max_attempts: int,
    timeout_seconds: int,
    output_dir: Path
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Main loop for fetching, injecting, and validating events.
    
    Args:
        target_count: Number of valid events required (e.g., 12 or 15)
        max_attempts: Maximum number of API calls/attempts
        timeout_seconds: Total timeout for the process
        output_dir: Directory to store intermediate and final data
    
    Returns:
        Tuple of (list_of_valid_events, stats_dict)
    
    Raises:
        RuntimeError: If target_count is not reached after max_attempts
    """
    logger = get_logger(__name__)
    
    # Ensure output directories exist
    ensure_dir(output_dir / "raw")
    ensure_dir(output_dir / "injected")
    
    valid_events: List[Dict[str, Any]] = []
    start_time = time.time()
    
    stats = {
        "total_attempts": 0,
        "successful_injections": 0,
        "valid_events": 0,
        "failed_attempts": 0,
        "duration_seconds": 0.0
    }
    
    attempt = 0
    while len(valid_events) < target_count and attempt < max_attempts:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.error(f"Timeout reached after {elapsed:.1f}s. Stopping loop.")
            break
        
        attempt += 1
        stats["total_attempts"] = attempt
        
        event_data, is_valid = process_single_attempt(attempt, output_dir, logger)
        
        if is_valid and event_data:
            valid_events.append(event_data)
            stats["successful_injections"] += 1
            stats["valid_events"] = len(valid_events)
            log_metric("US1_Valid_Count", len(valid_events))
        else:
            stats["failed_attempts"] += 1
        
        # Small delay to avoid hammering API
        time.sleep(0.5)
    
    stats["duration_seconds"] = time.time() - start_time
    
    # Post-loop validation
    if len(valid_events) < target_count:
        raise RuntimeError(
            f"Insufficient valid events found after {attempt} attempts. "
            f"Found {len(valid_events)}, required {target_count}. "
            f"Process stopped due to max_attempts or timeout."
        )
    
    logger.info(f"Loop complete. Found {len(valid_events)} valid events in {stats['duration_seconds']:.1f}s.")
    return valid_events, stats

def main():
    """CLI entry point for testing the fetch loop."""
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "data" / "processed"
    
    try:
        events, stats = run_fetch_loop(
            target_count=12,
            max_attempts=20, # Reduced for testing
            timeout_seconds=300,
            output_dir=output_dir
        )
        logger.info(f"Success! {len(events)} events found.")
    except RuntimeError as e:
        logger.error(f"Loop failed: {e}")
        raise

if __name__ == "__main__":
    main()
"""
Batch Processor for Data Acquisition (US1).

Implements the logic for T015:
- Fetches noise segments in batches.
- Injects synthetic signals.
- Validates events.
- Loops until >= min_valid_events are found or max_attempts is reached.
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Import from sibling modules
from src.data.inject import inject_synthetic_signal, generate_true_parameters
from src.data.validate import validate_file, check_true_parameters_exist
from src.data.download import fetch_gw_noise_segment  # Assuming this exists based on API surface
from src.utils.config import get_seed

# Constants
MAX_ATTEMPTS_DEFAULT = 20
MIN_VALID_EVENTS_DEFAULT = 12
SNR_THRESHOLD = 8.0

def process_batch(
    noise_files: List[Path],
    output_dir: Path,
    logger: logging.Logger
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process a batch of noise files: inject signals and validate.
    
    Returns:
        Tuple of (valid_events, invalid_events)
    """
    valid_events = []
    invalid_events = []
    
    for noise_path in noise_files:
        event_id = noise_path.stem
        logger.info(f"Processing event: {event_id}")
        
        try:
            # 1. Inject synthetic signal
            injected_path = output_dir / f"{event_id}_injected.h5"
            true_params = generate_true_parameters(seed=get_seed(event_id))
            
            inject_synthetic_signal(
                noise_path=noise_path,
                output_path=injected_path,
                true_params=true_params,
                logger=logger
            )
            
            # 2. Validate the injected file
            is_valid, validation_details = validate_file(injected_path)
            
            if is_valid:
                # Check for specific metadata requirements (spin, true params)
                has_true_params = check_true_parameters_exist(injected_path)
                
                if has_true_params:
                    event_data = {
                        "event_id": event_id,
                        "file_path": str(injected_path),
                        "true_parameters": true_params,
                        "validation_details": validation_details
                    }
                    valid_events.append(event_data)
                    logger.info(f"Event {event_id} is VALID.")
                else:
                    invalid_events.append({"event_id": event_id, "reason": "Missing true parameters"})
                    logger.warning(f"Event {event_id} is INVALID: Missing true parameters.")
            else:
                invalid_events.append({"event_id": event_id, "reason": str(validation_details)})
                logger.warning(f"Event {event_id} is INVALID: {validation_details}")
                
        except Exception as e:
            logger.error(f"Failed to process event {event_id}: {str(e)}", exc_info=True)
            invalid_events.append({"event_id": event_id, "reason": str(e)})
    
    return valid_events, invalid_events

def run_injection_campaign(
    target_events: int,
    min_valid_events: int = MIN_VALID_EVENTS_DEFAULT,
    max_attempts: int = MAX_ATTEMPTS_DEFAULT,
    output_dir: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
    """
    Main loop for the injection campaign (T015 logic).
    
    Implements: while valid_count < min_valid_events and attempts < max_attempts
    
    Args:
        target_events: Target number of events to attempt (FR-001 says >=15, but loop stops at min_valid)
        min_valid_events: Minimum valid events required to stop successfully.
        max_attempts: Maximum number of fetch/inject attempts before failing.
        output_dir: Directory to save intermediate files.
        logger: Logger instance.
        
    Returns:
        Tuple of (valid_events_list, total_attempts, summary_stats)
        
    Raises:
        RuntimeError: If max_attempts is reached and min_valid_events not met.
    """
    if logger is None:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
    if output_dir is None:
        output_dir = Path("data/interim/injected")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    valid_events = []
    attempts = 0
    batch_size = 1  # Fetch one by one to control the loop precisely
    
    logger.info(f"Starting injection campaign. Target: {target_events}, Min Valid: {min_valid_events}, Max Attempts: {max_attempts}")
    
    while len(valid_events) < min_valid_events and attempts < max_attempts:
        attempts += 1
        logger.info(f"--- Attempt {attempts} ---")
        
        # Simulate fetching a noise segment (In real impl, this calls GWOSC API)
        # For now, we assume fetch_gw_noise_segment returns a Path to a noise file
        # or raises an error if it fails.
        try:
            # Generate a pseudo-random event ID for this attempt
            event_id = f"GW_{attempts:04d}"
            
            # Fetch noise
            noise_path = fetch_gw_noise_segment(event_id=event_id, output_dir=output_dir)
            
            if noise_path is None or not noise_path.exists():
                logger.warning(f"Attempt {attempts}: Failed to fetch noise for {event_id}")
                continue
                
            # Process this single event
            batch_valid, batch_invalid = process_batch([noise_path], output_dir, logger)
            valid_events.extend(batch_valid)
            
        except Exception as e:
            logger.error(f"Attempt {attempts} failed with exception: {str(e)}")
            continue
    
    summary = {
        "total_attempts": attempts,
        "valid_count": len(valid_events),
        "target_met": len(valid_events) >= min_valid_events,
        "failure_reason": None if len(valid_events) >= min_valid_events else "Max attempts reached"
    }
    
    if len(valid_events) < min_valid_events:
        logger.error(f"Campaign failed. Found {len(valid_events)} valid events after {attempts} attempts. Required: {min_valid_events}.")
        raise RuntimeError(f"Failed to find {min_valid_events} valid events after {max_attempts} attempts.")
        
    logger.info(f"Campaign successful. Found {len(valid_events)} valid events.")
    return valid_events, attempts, summary

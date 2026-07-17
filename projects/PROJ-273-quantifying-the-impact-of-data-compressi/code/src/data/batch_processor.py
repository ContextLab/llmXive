"""
Batch processing module for fetching noise, injecting signals, and validating events.
Implements the loop logic to find >=12 valid events with complete spin metadata.
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.data.download import fetch_gw_noise_segment
from src.data.inject import inject_synthetic_signal, generate_true_parameters
from src.data.validate import validate_file, check_true_parameters_exist

# Configuration constants
MIN_VALID_EVENTS = 12
MAX_ATTEMPTS = 20
TIMEOUT_SECONDS = 300
DETECTORS = ["H1", "L1"]  # LIGO Hanford and Livingston

logger = logging.getLogger(__name__)


def process_batch(
    batch_size: int,
    output_dir: Path,
    start_time: float
) -> List[Dict[str, Any]]:
    """
    Process a batch of noise segments: fetch, inject, and validate.
    
    Args:
        batch_size: Number of events to attempt in this batch.
        output_dir: Directory to save injected data.
        start_time: Timestamp when the overall process started.
        
    Returns:
        List of valid event metadata dictionaries.
        
    Raises:
        TimeoutError: If the timeout is exceeded.
    """
    valid_events = []
    attempts = 0
    
    while len(valid_events) < MIN_VALID_EVENTS and attempts < MAX_ATTEMPTS:
        # Check timeout
        if time.time() - start_time > TIMEOUT_SECONDS:
            raise TimeoutError(
                f"Timeout exceeded ({TIMEOUT_SECONDS}s) before finding {MIN_VALID_EVENTS} valid events."
            )
        
        # Prepare parameters for this attempt
        event_id = f"evt_{attempts:04d}"
        detector = DETECTORS[attempts % len(DETECTORS)]
        true_params = generate_true_parameters(detector=detector)
        
        try:
            # 1. Fetch noise
            noise_file = fetch_gw_noise_segment(detector=detector, output_dir=output_dir)
            if not noise_file:
                logger.warning(f"Attempt {attempts}: Failed to fetch noise for {detector}. Skipping.")
                attempts += 1
                continue
            
            # 2. Inject signal
            injected_file = inject_synthetic_signal(
                noise_file=noise_file,
                true_params=true_params,
                output_dir=output_dir,
                event_id=event_id
            )
            if not injected_file:
                logger.warning(f"Attempt {attempts}: Failed to inject signal for {event_id}. Skipping.")
                attempts += 1
                continue
            
            # 3. Validate
            is_valid, metadata = validate_file(injected_file)
            
            if is_valid:
                # Additional check for spin metadata completeness
                if check_true_parameters_exist(metadata):
                    valid_events.append(metadata)
                    logger.info(f"Attempt {attempts}: Valid event found. Total valid: {len(valid_events)}/{MIN_VALID_EVENTS}")
                else:
                    logger.warning(f"Attempt {attempts}: Event {event_id} missing spin metadata. Skipping.")
            else:
                logger.warning(f"Attempt {attempts}: Validation failed for {event_id}. Skipping.")
            
            attempts += 1
            
        except Exception as e:
            logger.error(f"Attempt {attempts}: Unexpected error processing {event_id}: {e}")
            attempts += 1
            continue
    
    return valid_events


def run_injection_campaign(
    target_events: int = MIN_VALID_EVENTS,
    output_dir: Optional[Path] = None,
    max_attempts: int = MAX_ATTEMPTS,
    timeout: int = TIMEOUT_SECONDS
) -> List[Dict[str, Any]]:
    """
    Orchestrate the full campaign to find the target number of valid events.
    
    This function implements the core logic for T015:
    - Fetches additional noise segments in batches.
    - Injects synthetic signals.
    - Validates for complete spin metadata.
    - Stops when >=12 valid events are found OR max_attempts/timeout is reached.
    
    Args:
        target_events: Target number of valid events (default 12).
        output_dir: Directory for output files. Defaults to project data/interim.
        max_attempts: Maximum number of injection attempts allowed.
        timeout: Maximum time in seconds to run the campaign.
        
    Returns:
        List of valid event metadata dictionaries.
        
    Raises:
        RuntimeError: If the campaign fails to find the target number of events
                      after exhausting attempts or time.
    """
    if output_dir is None:
        output_dir = Path("data/interin")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting injection campaign. Target: {target_events}, Max attempts: {max_attempts}, Timeout: {timeout}s")
    start_time = time.time()
    
    valid_events = []
    total_attempts = 0
    
    while len(valid_events) < target_events and total_attempts < max_attempts:
        # Check timeout
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Timeout exceeded ({timeout}s) before finding {target_events} valid events. "
                f"Found {len(valid_events)} so far."
            )
        
        # Process a batch (or single event loop)
        # We process one by one to respect the attempt limit strictly
        detector = DETECTORS[total_attempts % len(DETECTORS)]
        event_id = f"evt_{total_attempts:04d}"
        true_params = generate_true_parameters(detector=detector)
        
        try:
            # 1. Fetch noise
            noise_file = fetch_gw_noise_segment(detector=detector, output_dir=output_dir)
            if not noise_file:
                logger.warning(f"Attempt {total_attempts}: Failed to fetch noise for {detector}.")
                total_attempts += 1
                continue
            
            # 2. Inject
            injected_file = inject_synthetic_signal(
                noise_file=noise_file,
                true_params=true_params,
                output_dir=output_dir,
                event_id=event_id
            )
            if not injected_file:
                logger.warning(f"Attempt {total_attempts}: Failed to inject signal for {event_id}.")
                total_attempts += 1
                continue
            
            # 3. Validate
            is_valid, metadata = validate_file(injected_file)
            
            if is_valid and check_true_parameters_exist(metadata):
                valid_events.append(metadata)
                logger.info(f"Attempt {total_attempts}: Valid event {event_id} added. Total: {len(valid_events)}/{target_events}")
            else:
                reason = "Validation failed" if not is_valid else "Missing spin metadata"
                logger.warning(f"Attempt {total_attempts}: {event_id} rejected. Reason: {reason}")
            
            total_attempts += 1
            
        except Exception as e:
            logger.error(f"Attempt {total_attempts}: Critical error in loop: {e}")
            total_attempts += 1
            # Continue to next attempt rather than failing immediately, 
            # unless it's a persistent infrastructure failure (handled by timeout)
    
    # Final check
    if len(valid_events) < target_events:
        error_msg = (
            f"Campaign failed to find {target_events} valid events. "
            f"Found {len(valid_events)} after {total_attempts} attempts."
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"Campaign successful. Found {len(valid_events)} valid events.")
    return valid_events

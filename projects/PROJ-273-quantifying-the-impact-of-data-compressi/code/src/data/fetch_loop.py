"""
Fetch Loop Module for GW Injection Pipeline (T019.1)

Implements the logic to fetch noise segments one by one, inject synthetic signals,
validate metadata, and stop when >=12 valid events with complete spin metadata
are found or max_attempts=20 is reached.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error, log_metric
from src.utils.config import get_path, ensure_dir
from src.data.download import fetch_gw_noise_segment
from src.data.inject import inject_synthetic_signal, generate_true_parameters
from src.data.validate import validate_file, check_true_parameters_exist

logger = get_logger(__name__)

# Constants for the fetch loop (Amended FR-001)
TARGET_VALID_EVENTS = 12
MAX_ATTEMPTS = 20
TIMEOUT_PER_ATTEMPT = 300  # seconds

def process_single_attempt(
    attempt_num: int,
    output_dir: Path,
    noise_dir: Path,
    injection_dir: Path
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Perform a single fetch-inject-validate attempt.

    Returns:
        Tuple[success (bool), event_metadata (dict or None)]
    """
    log_step_start(logger, f"Attempt {attempt_num}/{MAX_ATTEMPTS}")

    try:
        # 1. Fetch noise segment
        noise_file = fetch_gw_noise_segment(
            detector="L1",  # Default to L1 for now, could be randomized
            output_dir=noise_dir
        )

        if not noise_file or not noise_file.exists():
            logger.warning(f"Attempt {attempt_num}: Failed to fetch noise segment.")
            return False, None

        # 2. Generate true parameters (ground truth)
        true_params = generate_true_parameters()

        # 3. Inject synthetic signal
        injection_result = inject_synthetic_signal(
            noise_file=noise_file,
            true_parameters=true_params,
            output_dir=injection_dir
        )

        if not injection_result or not injection_result.get("success"):
            logger.warning(f"Attempt {attempt_num}: Injection failed.")
            return False, None

        injected_file = Path(injection_result["output_file"])

        # 4. Validate the injected file
        is_valid, metadata = validate_file(injected_file)

        if not is_valid:
            logger.warning(f"Attempt {attempt_num}: Validation failed for {injected_file.name}")
            return False, None

        # 5. Check for complete spin metadata (FR-009)
        has_spin = check_true_parameters_exist(metadata)

        if not has_spin:
            logger.warning(f"Attempt {attempt_num}: Missing complete spin metadata.")
            return False, None

        log_step_complete(logger, f"Attempt {attempt_num}: Valid event generated.")
        log_metric(logger, "valid_event_count", 1)

        return True, metadata

    except Exception as e:
        log_step_error(logger, f"Attempt {attempt_num} failed with error: {str(e)}")
        logger.exception(e)
        return False, None

def run_fetch_loop(
    target_events: int = TARGET_VALID_EVENTS,
    max_attempts: int = MAX_ATTEMPTS,
    timeout_per_attempt: int = TIMEOUT_PER_ATTEMPT
) -> List[Dict[str, Any]]:
    """
    Main loop to fetch, inject, and validate events until target is met or max attempts reached.

    Args:
        target_events: Number of valid events to collect (default 12).
        max_attempts: Maximum number of fetch attempts (default 20).
        timeout_per_attempt: Timeout in seconds per attempt.

    Returns:
        List of metadata dictionaries for valid events.
    """
    logger.info(f"Starting fetch loop: target={target_events}, max_attempts={max_attempts}")

    # Ensure directories exist
    noise_dir = get_path("data", "raw", "noise")
    injection_dir = get_path("data", "interim", "injections")
    ensure_dir(noise_dir)
    ensure_dir(injection_dir)

    valid_events = []
    attempts = 0

    while len(valid_events) < target_events and attempts < max_attempts:
        attempts += 1
        start_time = time.time()

        success, metadata = process_single_attempt(
            attempt_num=attempts,
            output_dir=get_path("data"),
            noise_dir=noise_dir,
            injection_dir=injection_dir
        )

        elapsed = time.time() - start_time
        if elapsed < timeout_per_attempt:
            time.sleep(timeout_per_attempt - elapsed)  # Enforce minimum attempt duration if needed

        if success and metadata:
            valid_events.append(metadata)
            logger.info(f"Current valid event count: {len(valid_events)}/{target_events}")

    # Post-loop validation and warning
    if len(valid_events) < target_events:
        logger.warning(
            f"Fetch loop terminated with {len(valid_events)} valid events "
            f"(target: {target_events}). Proceeding with available events."
        )
        log_metric(logger, "final_valid_event_count", len(valid_events))
        log_metric(logger, "total_attempts", attempts)
    else:
        logger.info(f"Fetch loop completed successfully with {len(valid_events)} valid events.")

    return valid_events

def main():
    """Entry point for the fetch loop script."""
    valid_events = run_fetch_loop()

    # Save the list of valid event metadata to a JSON file
    output_file = get_path("data", "processed", "valid_events_metadata.json")
    ensure_dir(output_file.parent)

    with open(output_file, "w") as f:
        json.dump(valid_events, f, indent=2)

    logger.info(f"Saved {len(valid_events)} valid event metadata to {output_file}")
    return valid_events

if __name__ == "__main__":
    main()

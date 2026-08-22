"""
Fetch Loop Implementation (T019.1).

Implements the logic to fetch noise segments one by one, inject signals,
and validate metadata until >= 12 valid events (with complete spin metadata)
are found or max_attempts is reached.

Per Amended FR-001 and FR-009:
- Fetches noise one by one (batch_size=1).
- Validates for complete spin metadata (tilt angles).
- Fails loudly if < 12 valid events found after max_attempts.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure code directory is in path
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.download import fetch_gw_noise_segment
from src.data.inject import inject_synthetic_signal, generate_true_parameters
from src.data.validate import validate_file, check_true_parameters_exist
from src.utils.logging import get_logger, log_event_processed
from src.utils.config import set_seed

logger = get_logger(__name__)

# Constants
MIN_VALID_EVENTS = 12
MAX_ATTEMPTS = 100
TIMEOUT_SECONDS = 300

def process_single_attempt(attempt_num: int, output_dir: Path) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Process a single fetch-inject-validate attempt.
    
    Returns:
        Tuple[success: bool, event_metadata: Optional[Dict]]
        If successful and valid, returns metadata. Otherwise returns (False, None).
    """
    logger.info(f"Processing attempt {attempt_num}/{MAX_ATTEMPTS}")
    
    try:
        # 1. Fetch Noise (Batch size 1)
        # We use a generic event ID placeholder or a rotating list if needed.
        # For GWOSC, we can try fetching a segment around a known time or a random valid time.
        # To ensure we get data, we might try a few known O3/O4 times if the random one fails.
        # For this implementation, we attempt to fetch a segment.
        # Note: fetch_gw_noise_segment handles the actual API call.
        
        # Generate a unique ID for this attempt to avoid collisions
        attempt_id = f"attempt_{attempt_num}"
        
        noise_file_path = fetch_gw_noise_segment(
            output_dir=output_dir,
            event_id=attempt_id,
            detector="H1", # Default to LIGO Hanford
            duration=4.0   # 4 seconds standard
        )

        if not noise_file_path or not noise_file_path.exists():
            logger.warning(f"Attempt {attempt_num}: Noise fetch failed or returned no file.")
            return False, None

        # 2. Generate True Parameters (Synthetic Injection)
        # We generate random but physical parameters for the injection
        true_params = generate_true_parameters(seed=attempt_num)
        
        # 3. Inject Signal
        injected_file_path = inject_synthetic_signal(
            noise_path=noise_file_path,
            true_params=true_params,
            output_dir=output_dir,
            event_id=attempt_id
        )

        if not injected_file_path or not injected_file_path.exists():
            logger.warning(f"Attempt {attempt_num}: Injection failed.")
            return False, None

        # 4. Validate File
        # Check for strain, detector, timestamp, AND known true parameters + spin metadata
        is_valid, metadata = validate_file(str(injected_file_path))

        if not is_valid:
            logger.warning(f"Attempt {attempt_num}: Validation failed. Metadata: {metadata}")
            return False, None

        # 5. Check Spin Metadata (Tilt Angles) - Critical for FR-009
        # The metadata should contain 'true_parameters' which includes spin/tilt info
        if not check_true_parameters_exist(metadata):
            logger.warning(f"Attempt {attempt_num}: Missing true parameters in metadata.")
            return False, None

        # Check specifically for tilt angles if they are expected in the structure
        # Assuming true_params structure includes spin1_tilt, spin2_tilt or similar
        tp = metadata.get("true_parameters", {})
        has_tilt = "spin1_tilt" in tp and "spin2_tilt" in tp # Adjust key names based on inject.py implementation
        
        if not has_tilt:
            logger.warning(f"Attempt {attempt_num}: Missing spin tilt metadata.")
            return False, None

        logger.info(f"Attempt {attempt_num}: Valid event found. SNR: {metadata.get('snr', 'N/A')}")
        log_event_processed(attempt_id, "valid_injection")

        return True, metadata

    except Exception as e:
        logger.error(f"Attempt {attempt_num}: Exception during processing: {e}")
        return False, None

def run_fetch_loop(target_count: int, max_attempts: int, timeout_seconds: int, output_dir: Path) -> Dict[str, Any]:
    """
    Run the fetch-inject-validate loop.
    
    Args:
        target_count: Number of valid events to find (>= 12 for analysis, >= 15 for target).
        max_attempts: Maximum number of attempts to try.
        timeout_seconds: Total timeout for the loop.
        output_dir: Directory to save intermediate files.
        
    Returns:
        Dictionary with 'valid_events', 'total_attempts', 'failed_attempts'.
        
    Raises:
        RuntimeError: If valid events found < MIN_VALID_EVENTS (12) after max_attempts.
    """
    start_time = time.time()
    valid_events = []
    total_attempts = 0
    failed_attempts = 0

    logger.info(f"Starting fetch loop. Target: {target_count}, Max Attempts: {max_attempts}")

    while len(valid_events) < target_count and total_attempts < max_attempts:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.error(f"Timeout reached after {elapsed:.2f}s. Found {len(valid_events)} events.")
            break

        total_attempts += 1
        success, metadata = process_single_attempt(total_attempts, output_dir)

        if success and metadata:
            valid_events.append(metadata)
        else:
            failed_attempts += 1

        # Log progress
        if total_attempts % 10 == 0:
            logger.info(f"Progress: {len(valid_events)}/{target_count} valid events after {total_attempts} attempts.")

    # Post-loop validation
    logger.info(f"Loop finished. Found {len(valid_events)} valid events.")
    
    if len(valid_events) < MIN_VALID_EVENTS:
        error_msg = f"Insufficient valid events found after {total_attempts} attempts. Found {len(valid_events)}, required {MIN_VALID_EVENTS}."
        logger.error(error_msg)
        # Fail loudly as per constraint
        raise RuntimeError(error_msg)

    return {
        "valid_events": valid_events,
        "total_attempts": total_attempts,
        "failed_attempts": failed_attempts,
        "elapsed_seconds": time.time() - start_time
    }

def main():
    """Entry point for direct execution."""
    import sys
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / "data" / "interim" / "injections"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        results = run_fetch_loop(
            target_count=MIN_VALID_EVENTS, # Run until we have enough for analysis
            max_attempts=MAX_ATTEMPTS,
            timeout_seconds=TIMEOUT_SECONDS,
            output_dir=output_dir
        )
        logger.info(f"Final Results: {results['valid_event_count']} valid events found.")
    except RuntimeError as e:
        logger.critical(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()

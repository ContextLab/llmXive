"""
Orchestration loop for the data acquisition pipeline.
Implements T019.1 Step 3: fetch -> inject -> validate loop.

Logic:
- Loop until >=5 valid events found OR max_attempts (50) reached.
- If loop ends with <5 valid events, raise RuntimeError.
- Save valid event IDs to data/interim/valid_events.json.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir
from src.data.fetch_logic import fetch_noise_segment, inject_and_save
from src.data.validation_logic import validate_injection

logger = get_logger(__name__)

def process_single_attempt(attempt_id: int, output_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Execute a single fetch-inject-validate attempt.
    
    Args:
        attempt_id: Unique ID for this attempt.
        output_dir: Directory to store intermediate files.
        
    Returns:
        Dictionary with event details if valid, None otherwise.
    """
    event_id = f"evt_{attempt_id}_{int(time.time())}"
    logger.info(f"--- Attempt {attempt_id}: {event_id} ---")
    
    try:
        # 1. Fetch Noise
        # We fetch a segment. To ensure we get real data, we use the fetch_logic.
        # We pass a unique event name to avoid overwriting.
        noise_path = fetch_noise_segment(event_id, output_dir)
        
        # 2. Inject Signal
        injected_path, metadata = inject_and_save(noise_path, event_id, output_dir)
        
        # 3. Validate
        injection_data = {
            'injected_path': str(injected_path),
            'metadata_path': str(output_dir / f"{event_id}_metadata.json")
        }
        
        is_valid, reason = validate_injection(injection_data)
        
        if is_valid:
            logger.info(f"Attempt {attempt_id} VALID: {reason}")
            return {
                'event_id': event_id,
                'injected_path': str(injected_path),
                'metadata_path': injection_data['metadata_path'],
                'true_parameters': metadata.get('true_parameters', {}),
                'snr': metadata.get('snr', 0)
            }
        else:
            logger.warning(f"Attempt {attempt_id} INVALID: {reason}")
            return None
            
    except Exception as e:
        logger.error(f"Attempt {attempt_id} FAILED with exception: {e}")
        # Log error but continue to next attempt
        return None

def run_fetch_loop(target_count: int = 5, max_attempts: int = 50, output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Run the fetch-inject-validate loop.
    
    Args:
        target_count: Number of valid events to find.
        max_attempts: Maximum number of attempts before failing.
        output_dir: Directory to save intermediate files.
        
    Returns:
        List of valid event dictionaries.
        
    Raises:
        RuntimeError: If target_count is not met after max_attempts.
    """
    if output_dir is None:
        output_dir = get_project_root() / "data" / "interim"
    ensure_dir(output_dir)
    
    valid_events = []
    attempt = 0
    
    log_step_start("Fetch Loop", {"target": target_count, "max_attempts": max_attempts})
    
    while len(valid_events) < target_count and attempt < max_attempts:
        attempt += 1
        
        result = process_single_attempt(attempt, output_dir)
        
        if result:
            valid_events.append(result)
            logger.info(f"Valid events found: {len(valid_events)}/{target_count}")
            
        # Small delay to avoid rate limiting (if any)
        time.sleep(0.1)
        
    if len(valid_events) < target_count:
        error_msg = f"Failed to generate {target_count} valid events after {max_attempts} attempts. Found {len(valid_events)}."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    log_step_complete("Fetch Loop", {"valid_events_count": len(valid_events)})
    return valid_events

def main():
    """
    Entry point for the fetch loop script.
    """
    try:
        valid_events = run_fetch_loop(target_count=5, max_attempts=50)
        logger.info(f"Successfully found {len(valid_events)} valid events.")
        return 0
    except RuntimeError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
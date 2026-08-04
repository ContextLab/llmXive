"""
Main orchestration script for the Download-Inject-Validate pipeline.

This script implements the logic required by Amended FR-001:
- Fetches real GW noise segments from GWOSC.
- Injects synthetic CBC signals using LALSimulation with known ground truth.
- Validates metadata completeness (mass, distance, spin/tilt).
- Iterates until >= 12 valid events are found (max 20 attempts).
- Produces the final validated dataset in data/processed/.

Dependencies:
- src.data.download (fetch_gw_noise_segment)
- src.data.inject (inject_synthetic_signal)
- src.data.validate (validate_file)
- src.utils.logging (log_step_*)
- src.utils.config (get_path, ensure_dir)
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add code root to path to ensure imports work in various environments
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.download import fetch_gw_noise_segment
from src.data.inject import inject_synthetic_signal
from src.data.validate import validate_file
from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error, log_event_processed
from src.utils.config import get_path, ensure_dir, set_seed

# Constants
TARGET_VALID_EVENTS = 12  # Per Amended FR-001 (>=12 valid events)
MAX_ATTEMPTS = 20         # Per Amended FR-001
MIN_SNR_THRESHOLD = 8.0   # Minimum SNR for an event to be considered valid

def run_injection_campaign():
    """
    Orchestrates the full download-inject-validate pipeline.
    
    Returns:
        Dict: Summary statistics of the campaign run.
    """
    logger = get_logger(__name__)
    set_seed(42)  # Pin random seed for reproducibility
    
    log_step_start("Injection Campaign", "Starting pipeline to fetch, inject, and validate GW events.")
    
    # Setup output directories
    processed_dir = get_path("data", "processed")
    ensure_dir(processed_dir)
    
    valid_events: List[Dict[str, Any]] = []
    attempts = 0
    start_time = datetime.now()
    
    # Target events list (using a subset of known O3 events for the pilot)
    # In a real run, this could be expanded or randomized.
    # We use a list of event names that are known to exist in GWOSC.
    target_events = [
        "GW190425", "GW190814", "GW200105", "GW200115", "GW200220",
        "GW200311", "GW200412", "GW200501", "GW200614", "GW200704",
        "GW200815", "GW200923", "GW201005", "GW201112", "GW201225"
    ]
    
    # We will iterate through target_events, but also fetch additional noise
    # if we don't hit the target count.
    event_idx = 0
    
    while len(valid_events) < TARGET_VALID_EVENTS and attempts < MAX_ATTEMPTS:
        attempts += 1
        logger.info(f"Attempt {attempts}/{MAX_ATTEMPTS}: Current valid count: {len(valid_events)}")
        
        # Determine which event name to use
        # If we have exhausted our predefined list, we generate a synthetic event name
        # or cycle through. For this implementation, we rely on the predefined list
        # and potentially fetch generic noise segments if needed, but the task
        # implies using known events.
        if event_idx < len(target_events):
            event_name = target_events[event_idx]
            event_idx += 1
        else:
            # Fallback: try to fetch a generic segment or raise if no more names
            # For robustness, we'll try to fetch a segment with a generated ID
            # but since GWOSC requires specific event names or time ranges,
            # we'll stick to the list. If list exhausted, we break or retry logic.
            # Given the constraint of real data, we assume the list is sufficient
            # or we stop.
            logger.warning(f"Predefined event list exhausted. Attempting to fetch generic segment...")
            # In a real scenario, we might fetch based on GPS time.
            # Here we simulate a "generic" attempt by using a placeholder name
            # that might fail, or we could try to fetch a known segment not in the list.
            # To strictly follow "Real Data Only", we must use valid GWOSC event names.
            # We will break if we run out of known events to avoid infinite loops.
            if event_idx >= len(target_events):
                logger.error("No more known event names available in the target list.")
                break
            event_name = target_events[event_idx % len(target_events)]
            event_idx += 1
        
        # 1. Download Noise
        try:
            noise_file = fetch_gw_noise_segment(event_name, output_dir=get_path("data", "raw"))
            if not noise_file or not noise_file.exists():
                logger.warning(f"Failed to download noise for {event_name}. Skipping.")
                continue
        except Exception as e:
            logger.error(f"Error downloading noise for {event_name}: {e}")
            continue
        
        # 2. Inject Signal
        try:
            injected_file = inject_synthetic_signal(noise_file, output_dir=get_path("data", "raw"))
            if not injected_file or not injected_file.exists():
                logger.warning(f"Failed to inject signal for {event_name}. Skipping.")
                continue
        except Exception as e:
            logger.error(f"Error injecting signal for {event_name}: {e}")
            continue
        
        # 3. Validate
        try:
            is_valid, metadata = validate_file(injected_file)
            
            if is_valid:
                # Check SNR threshold
                snr = metadata.get("snr", 0.0)
                if snr >= MIN_SNR_THRESHOLD:
                    valid_events.append({
                        "event_id": metadata.get("event_id", event_name),
                        "file_path": str(injected_file),
                        "snr": snr,
                        "metadata": metadata
                    })
                    log_event_processed("Valid Event", {"event_id": event_name, "snr": snr})
                    logger.info(f"Valid event found: {event_name} (SNR={snr:.2f})")
                else:
                    logger.warning(f"Event {event_name} has SNR {snr:.2f} < {MIN_SNR_THRESHOLD}. Skipping.")
            else:
                logger.warning(f"Validation failed for {event_name}: {metadata.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error validating file {injected_file}: {e}")
            continue
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Final Report
    summary = {
        "status": "completed" if len(valid_events) >= TARGET_VALID_EVENTS else "incomplete",
        "total_attempts": attempts,
        "valid_events_found": len(valid_events),
        "target_valid_events": TARGET_VALID_EVENTS,
        "duration_seconds": duration,
        "events": [
            {
                "event_id": ev["event_id"],
                "file_path": ev["file_path"],
                "snr": ev["snr"]
            }
            for ev in valid_events
        ]
    }
    
    # Save summary to data/processed/
    summary_path = get_path("data", "processed", "injection_campaign_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Pipeline complete. Found {len(valid_events)} valid events in {duration:.2f}s.")
    log_step_complete("Injection Campaign", f"Found {len(valid_events)} valid events.")
    
    if len(valid_events) < TARGET_VALID_EVENTS:
        logger.error(f"Failed to find {TARGET_VALID_EVENTS} valid events after {attempts} attempts.")
        # Per FR-001: "If a sufficient number of valid events are not found ... the system MUST raise a RuntimeError"
        raise RuntimeError(f"Failed to find {TARGET_VALID_EVENTS} valid events after {attempts} attempts.")
        
    return summary

def main():
    """Entry point for the pipeline."""
    try:
        run_injection_campaign()
    except RuntimeError as e:
        log_step_error("Injection Campaign", str(e))
        sys.exit(1)
    except Exception as e:
        log_step_error("Injection Campaign", f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
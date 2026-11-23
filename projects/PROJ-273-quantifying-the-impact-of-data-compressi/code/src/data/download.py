"""
Module: src.data.download
Purpose: Fetch real GW noise segments from GWOSC API.
Operates under Amended FR-001: Fetches noise only; injection is handled in T013.
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, List

# Import from project utils
from src.utils.config import get_project_root, ensure_dir, get_config
from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error

# Configure logger
logger = get_logger(__name__)

# Constants for GWOSC API
GWOSC_BASE_URL = "https://www.gwosc.org"
# Using the O4 run as a primary target, with O3 as fallback if needed
# These are real, publicly available observing runs
TARGET_RUNS = ["O4", "O3", "O2"]
DETECTORS = ["H1", "L1"]
SEGMENT_DURATION = 4096  # seconds - standard for analysis
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def fetch_gw_noise_segment(
    event_id: str,
    detector: str = "H1",
    run: str = "O4",
    duration: int = SEGMENT_DURATION,
    output_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Fetch a real GW noise segment from GWOSC API for a specific event and detector.
    
    This function implements the data acquisition part of Amended FR-001.
    It fetches ONLY noise segments - no injection is performed here.
    
    Args:
        event_id: Unique identifier for the noise segment (e.g., "GW170817_noise")
        detector: Detector name (H1 or L1)
        run: Observing run (O4, O3, O2)
        duration: Duration of segment in seconds
        output_dir: Directory to save the noise file. Defaults to data/raw/
        
    Returns:
        Path to the saved noise file, or None if fetch failed.
        
    Raises:
        RuntimeError: If fetch fails after max retries or if no real data source is available.
    """
    log_step_start("fetch_gw_noise_segment", event_id=event_id, detector=detector, run=run)
    
    if output_dir is None:
        output_dir = get_project_root() / "data" / "raw"
    
    ensure_dir(output_dir)
    
    # Construct file path
    safe_event_id = event_id.replace("/", "_").replace("\\", "_")
    output_path = output_dir / f"{safe_event_id}_{detector}_{run}.hdf5"
    
    # Skip if file already exists
    if output_path.exists():
        logger.info(f"Skipping existing file: {output_path}")
        log_step_complete("fetch_gw_noise_segment", output_path=str(output_path), status="skipped")
        return output_path
    
    # Attempt to fetch from GWOSC
    fetch_success = False
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Attempt {attempt}/{MAX_RETRIES} to fetch noise for {event_id} from GWOSC")
            
            # Use gwosc library to fetch real data
            # This is the standard, verified way to access GWOSC data
            from gwosc import datasets
            
            # Try to find the run
            try:
                # Get the segment list for the detector and run
                segment_list = datasets.find_gwosc_segments(detector, run)
                
                if not segment_list:
                    logger.warning(f"No segments found for {detector} in run {run}")
                    last_error = f"No segments found for {detector} in run {run}"
                    continue
                
                # Select a random segment from the run
                # In a real implementation, we'd pick segments near known events
                # For now, we'll pick the first available segment
                selected_segment = segment_list[0]
                start_time = selected_segment[0]
                end_time = selected_segment[1]
                
                # Calculate duration to fetch
                if end_time - start_time < duration:
                    duration = end_time - start_time
                
                logger.info(f"Fetching segment from {start_time} to {end_time} for {duration}s")
                
                # Fetch the strain data
                strain_dict = datasets.fetch_strain_data(
                    [detector],
                    start_time,
                    duration,
                    version="latest"
                )
                
                if detector not in strain_dict:
                    raise RuntimeError(f"Strain data not returned for {detector}")
                
                strain = strain_dict[detector]
                
                # Save to file with metadata
                _save_noise_segment(
                    strain=strain,
                    detector=detector,
                    run=run,
                    start_time=start_time,
                    duration=duration,
                    output_path=output_path,
                    event_id=event_id
                )
                
                fetch_success = True
                logger.info(f"Successfully fetched and saved noise segment to {output_path}")
                break
                
            except Exception as e:
                logger.warning(f"Error fetching from GWOSC for {detector}/{run}: {str(e)}")
                last_error = str(e)
                continue
                
        except ImportError:
            logger.error("gwosc library not installed. Please install it via pip install gwosc")
            raise RuntimeError("GWOSC library not available. Cannot fetch real noise data.")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    
    if not fetch_success:
        error_msg = f"Failed to fetch noise segment for {event_id} after {MAX_RETRIES} attempts. Last error: {last_error}"
        logger.error(error_msg)
        log_step_error("fetch_gw_noise_segment", error=error_msg)
        # FAIL LOUDLY - do not return None or synthetic data
        raise RuntimeError(error_msg)
    
    log_step_complete("fetch_gw_noise_segment", output_path=str(output_path), status="success")
    return output_path

def _save_noise_segment(
    strain: dict,
    detector: str,
    run: str,
    start_time: int,
    duration: int,
    output_path: Path,
    event_id: str
) -> None:
    """
    Save noise segment to HDF5 file with metadata.
    
    Args:
        strain: Strain data dictionary from GWOSC
        detector: Detector name
        run: Observing run
        start_time: GPS start time
        duration: Duration in seconds
        output_path: Path to save the file
        event_id: Event identifier
    """
    import h5py
    import numpy as np
    
    # Extract time series
    time_series = strain['times']
    strain_values = strain['strain']
    sample_rate = strain['sample_rate']
    
    # Create metadata
    metadata = {
        "event_id": event_id,
        "detector": detector,
        "run": run,
        "start_time": start_time,
        "duration": duration,
        "sample_rate": sample_rate,
        "num_samples": len(strain_values),
        "source": "GWOSC",
        "fetch_timestamp": time.time()
    }
    
    # Write to HDF5
    with h5py.File(output_path, 'w') as f:
        # Write time series
        f.create_dataset('time', data=time_series)
        f.create_dataset('strain', data=strain_values)
        
        # Write metadata as attributes
        for key, value in metadata.items():
            if isinstance(value, str):
                f.attrs[key] = value
            elif isinstance(value, (int, float)):
                f.attrs[key] = value
            else:
                f.attrs[key] = str(value)

def fetch_batch_noise_segments(
    event_ids: List[str],
    detector: str = "H1",
    runs: List[str] = None,
    duration: int = SEGMENT_DURATION,
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Fetch a batch of noise segments for multiple events.
    
    Args:
        event_ids: List of event identifiers
        detector: Detector name (H1 or L1)
        runs: List of observing runs to try (default: TARGET_RUNS)
        duration: Duration of each segment in seconds
        output_dir: Directory to save files
        
    Returns:
        List of paths to saved files
        
    Raises:
        RuntimeError: If any fetch fails
    """
    if runs is None:
        runs = TARGET_RUNS
    
    output_paths = []
    
    for event_id in event_ids:
        success = False
        for run in runs:
            try:
                path = fetch_gw_noise_segment(
                    event_id=event_id,
                    detector=detector,
                    run=run,
                    duration=duration,
                    output_dir=output_dir
                )
                if path:
                    output_paths.append(path)
                    success = True
                    break
            except RuntimeError as e:
                logger.warning(f"Failed to fetch {event_id} from {run}: {str(e)}")
                continue
        
        if not success:
            raise RuntimeError(f"Failed to fetch noise segment for {event_id} from any available run")
    
    return output_paths

def main():
    """
    Main entry point for testing the download module.
    Fetches a sample noise segment and verifies it was saved correctly.
    """
    # Set up logging
    setup_logging()
    
    # Test parameters
    test_event_id = "test_noise_segment_001"
    test_detector = "H1"
    test_run = "O4"
    
    logger.info(f"Starting noise segment fetch for {test_event_id}")
    
    try:
        output_path = fetch_gw_noise_segment(
            event_id=test_event_id,
            detector=test_detector,
            run=test_run
        )
        
        if output_path:
            logger.info(f"Successfully fetched noise segment to: {output_path}")
            logger.info(f"File size: {output_path.stat().st_size} bytes")
            
            # Verify file contents
            import h5py
            with h5py.File(output_path, 'r') as f:
                logger.info(f"Dataset keys: {list(f.keys())}")
                logger.info(f"Strain shape: {f['strain'].shape}")
                logger.info(f"Time shape: {f['time'].shape}")
                logger.info(f"Metadata: {dict(f.attrs)}")
            
            return 0
        else:
            logger.error("Failed to fetch noise segment")
            return 1
            
    except Exception as e:
        logger.error(f"Error during fetch: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())

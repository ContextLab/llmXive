"""
Module for fetching gravitational wave strain data from GWOSC.

Implements:
- Fetching high-SNR events (SNR >= 20) from GWOSC catalogs
- Detecting missing data segments and logging warnings with segment IDs
- Downloading and saving strain time series data
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from gwpy.timeseries import TimeSeries
from gwpy.table import EventTable
from gwpy.segments import SegmentList, Segment
from gwpy.timeseries import TimeSeries
import requests
import json
from datetime import datetime

# Import project utilities
from code.config import DATA_DIR
from code.utils.logging_config import get_derivation_logger, log_derivation_params
from code.utils.seeds import set_global_seed

logger = logging.getLogger(__name__)
derivation_logger = get_derivation_logger(__name__)

# Default parameters
DEFAULT_SNR_THRESHOLD = 20.0
DEFAULT_EVENT_NAME = "GW150914"
DEFAULT_CATALOG_VERSION = "O1"
DEFAULT_TIME_STR = "1126259462"
DEFAULT_DURATION = 2.0  # seconds

def fetch_high_snr_events(
    snr_threshold: float = DEFAULT_SNR_THRESHOLD,
    catalog_version: str = DEFAULT_CATALOG_VERSION,
    event_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch high-SNR gravitational wave events from GWOSC catalogs.
    
    Args:
        snr_threshold: Minimum SNR to include events (default: 20.0)
        catalog_version: GWOSC catalog version (e.g., "O1", "O2", "O3")
        event_name: Optional specific event name to filter for
        
    Returns:
        List of event dictionaries containing metadata including SNR
        
    Raises:
        RuntimeError: If no high-SNR events are found
        ConnectionError: If GWOSC API is unreachable
    """
    set_global_seed(42)  # Ensure reproducibility for any random operations
    
    derivation_logger.info(f"Fetching high-SNR events with threshold {snr_threshold} from catalog {catalog_version}")
    log_derivation_params(
        "fetch_high_snr_events",
        {
            "snr_threshold": snr_threshold,
            "catalog_version": catalog_version,
            "event_name": event_name
        }
    )
    
    try:
        # Use gwpy to fetch the event table from GWOSC
        # The 'catalog' module in gwpy provides access to GWOSC event tables
        from gwpy.table import EventTable
        
        # Construct the URL for the GWOSC event table
        # For O1 catalog, we use the standard GWOSC URL
        if catalog_version == "O1":
            url = "https://gwosc.org/eventapi/json/events/O1/"
        elif catalog_version == "O2":
            url = "https://gwosc.org/eventapi/json/events/O2/"
        elif catalog_version == "O3":
            url = "https://gwosc.org/eventapi/json/events/O3/"
        else:
            # Try to fetch from the general catalog
            url = f"https://gwosc.org/eventapi/json/events/{catalog_version}/"
        
        logger.info(f"Connecting to GWOSC API at {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        events_data = response.json()
        
        if "events" not in events_data:
            raise ValueError("Invalid response format from GWOSC API: missing 'events' key")
        
        high_snr_events = []
        
        for event in events_data["events"]:
            # Extract SNR from the event metadata
            # GWOSC events typically have 'snr' or 'combined_snr' in their metadata
            snr = None
            
            # Try common SNR field names
            if "snr" in event:
                snr = event["snr"]
            elif "combined_snr" in event:
                snr = event["combined_snr"]
            elif "optimal_snr" in event:
                snr = event["optimal_snr"]
            else:
                # Try to find SNR in nested metadata
                metadata = event.get("metadata", {})
                if "snr" in metadata:
                    snr = metadata["snr"]
            
            # Skip if SNR is not available
            if snr is None:
                logger.warning(f"Event {event.get('name', 'unknown')} has no SNR field, skipping")
                continue
            
            # Filter by SNR threshold
            if snr >= snr_threshold:
                event_info = {
                    "name": event.get("name", DEFAULT_EVENT_NAME),
                    "snr": float(snr),
                    "time": float(event.get("time", DEFAULT_TIME_STR)),
                    "duration": float(event.get("duration", DEFAULT_DURATION)),
                    "catalog": catalog_version,
                    "source": event.get("source", "GWOSC"),
                    "metadata": event
                }
                
                # Filter by specific event name if provided
                if event_name is not None and event_info["name"] != event_name:
                    continue
                
                high_snr_events.append(event_info)
                logger.info(f"Found high-SNR event: {event_info['name']} with SNR={snr:.2f}")
        
        if not high_snr_events:
            raise RuntimeError(f"No events with SNR >= {snr_threshold} found in catalog {catalog_version}")
        
        derivation_logger.info(f"Successfully fetched {len(high_snr_events)} high-SNR events")
        return high_snr_events
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to GWOSC API: {e}")
        raise ConnectionError(f"GWOSC API unreachable: {e}")
    except Exception as e:
        logger.error(f"Error fetching high-SNR events: {e}")
        raise RuntimeError(f"Failed to fetch high-SNR events: {e}")

def check_data_availability(
    event_info: Dict[str, Any],
    detectors: Optional[List[str]] = None
) -> Tuple[bool, List[Segment]]:
    """
    Check data availability for an event and detect missing segments.
    
    Args:
        event_info: Event dictionary from fetch_high_snr_events
        detectors: List of detectors to check (default: ["H1", "L1"])
        
    Returns:
        Tuple of (all_available, missing_segments)
        - all_available: True if all required data is available
        - missing_segments: List of Segment objects representing missing data
        
    Raises:
        ValueError: If event_info is invalid
    """
    if not event_info or "name" not in event_info:
        raise ValueError("Invalid event_info: missing 'name' field")
    
    event_name = event_info["name"]
    event_time = event_info["time"]
    duration = event_info.get("duration", DEFAULT_DURATION)
    
    if detectors is None:
        detectors = ["H1", "L1"]
    
    derivation_logger.info(f"Checking data availability for {event_name} at time {event_time}")
    log_derivation_params(
        "check_data_availability",
        {
            "event_name": event_name,
            "event_time": event_time,
            "duration": duration,
            "detectors": detectors
        }
    )
    
    missing_segments = []
    all_available = True
    
    try:
        from gwpy.segments import SegmentList
        
        for detector in detectors:
            # Define the time interval for this detector
            start_time = event_time - duration / 2
            end_time = event_time + duration / 2
            target_segment = Segment(start_time, end_time)
            
            logger.info(f"Checking data availability for {detector} in segment {target_segment}")
            
            try:
                # Use gwpy to check if data is available
                # We try to fetch a small sample of data to verify availability
                from gwpy.timeseries import TimeSeries
                
                # Attempt to fetch a short segment to verify availability
                # This will raise an error if data is not available
                test_duration = min(1.0, duration)
                sample_start = start_time
                sample_end = sample_start + test_duration
                
                # Try to fetch data - this will fail if not available
                try:
                    # Use gwpy's fetch method which handles availability checks
                    test_data = TimeSeries.fetch(
                        detector,
                        sample_start,
                        sample_end,
                        verbose=False
                    )
                    
                    # If we get here, data is available
                    logger.info(f"Data available for {detector} in {target_segment}")
                    
                except (ValueError, OSError) as e:
                    # Data not available or segment missing
                    logger.warning(f"Data not available for {detector} in {target_segment}: {e}")
                    missing_segments.append(target_segment)
                    all_available = False
                    
            except Exception as e:
                logger.warning(f"Error checking availability for {detector}: {e}")
                # Assume missing if we can't check
                missing_segments.append(target_segment)
                all_available = False
    
    except Exception as e:
        logger.error(f"Error in data availability check: {e}")
        # If we can't check, assume missing
        for detector in detectors:
            start_time = event_time - duration / 2
            end_time = event_time + duration / 2
            missing_segments.append(Segment(start_time, end_time))
        all_available = False
    
    # Log warnings for missing segments as required by US-1 Scenario 3
    if missing_segments:
        for seg in missing_segments:
            segment_id = f"{seg.start}-{seg.end}"
            warning_msg = f"Missing data segment detected: {segment_id}"
            logger.warning(warning_msg)
            derivation_logger.warning(warning_msg)
            log_derivation_params(
                "missing_segment",
                {
                    "segment_id": segment_id,
                    "start": seg.start,
                    "end": seg.end
                }
            )
    
    return all_available, missing_segments

def download_strain_data(
    event_info: Dict[str, Any],
    output_dir: Optional[Path] = None,
    detectors: Optional[List[str]] = None,
    sample_rate: int = 16384,
    duration: Optional[float] = None
) -> Dict[str, Path]:
    """
    Download strain time series data for an event.
    
    Args:
        event_info: Event dictionary from fetch_high_snr_events
        output_dir: Directory to save downloaded data (default: DATA_DIR/raw)
        detectors: List of detectors to download (default: ["H1", "L1"])
        sample_rate: Sample rate in Hz (default: 16384)
        duration: Duration of data to download in seconds (default: from event_info)
        
    Returns:
        Dictionary mapping detector names to paths of downloaded files
        
    Raises:
        RuntimeError: If data download fails
        ValueError: If event_info is invalid
    """
    if not event_info or "name" not in event_info:
        raise ValueError("Invalid event_info: missing 'name' field")
    
    event_name = event_info["name"]
    event_time = event_info["time"]
    event_duration = event_info.get("duration", DEFAULT_DURATION)
    
    if detectors is None:
        detectors = ["H1", "L1"]
        
    if duration is None:
        duration = event_duration
        
    if output_dir is None:
        output_dir = DATA_DIR / "raw"
        
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    derivation_logger.info(f"Downloading strain data for {event_name}")
    log_derivation_params(
        "download_strain_data",
        {
            "event_name": event_name,
            "event_time": event_time,
            "duration": duration,
            "sample_rate": sample_rate,
            "detectors": detectors
        }
    )
    
    downloaded_files = {}
    
    try:
        for detector in detectors:
            start_time = event_time - duration / 2
            end_time = event_time + duration / 2
            
            logger.info(f"Downloading {detector} data from {start_time} to {end_time}")
            
            try:
                # Download the time series data using gwpy
                # gwpy automatically handles the GWOSC API connection
                ts = TimeSeries.fetch(
                    detector,
                    start_time,
                    end_time,
                    sample_rate=sample_rate,
                    verbose=False
                )
                
                # Define output filename
                filename = f"{event_name}_{detector}_{int(start_time)}.hdf5"
                filepath = output_dir / filename
                
                # Save the time series
                ts.write(filepath)
                
                logger.info(f"Saved {detector} data to {filepath}")
                downloaded_files[detector] = filepath
                
            except Exception as e:
                logger.error(f"Failed to download {detector} data: {e}")
                # Continue with other detectors
                continue
        
        if not downloaded_files:
            raise RuntimeError(f"Failed to download data for any detector for event {event_name}")
        
        derivation_logger.info(f"Successfully downloaded {len(downloaded_files)} strain data files")
        return downloaded_files
        
    except Exception as e:
        logger.error(f"Error downloading strain data: {e}")
        raise RuntimeError(f"Failed to download strain data: {e}")

def save_strain_data(
    time_series: TimeSeries,
    event_name: str,
    detector: str,
    output_dir: Optional[Path] = None,
    format: str = "hdf5"
) -> Path:
    """
    Save strain time series data to disk.
    
    Args:
        time_series: gwpy TimeSeries object
        event_name: Name of the event
        detector: Detector name (e.g., "H1", "L1")
        output_dir: Directory to save file (default: DATA_DIR/raw)
        format: File format for saving (default: "hdf5")
        
    Returns:
        Path to the saved file
        
    Raises:
        ValueError: If time_series is invalid
    """
    if time_series is None:
        raise ValueError("time_series cannot be None")
        
    if output_dir is None:
        output_dir = DATA_DIR / "raw"
        
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    start_time = int(time_series.fstart)
    filename = f"{event_name}_{detector}_{start_time}.{format}"
    filepath = output_dir / filename
    
    logger.info(f"Saving strain data to {filepath}")
    time_series.write(filepath)
    
    derivation_logger.info(f"Saved strain data to {filepath}")
    log_derivation_params(
        "save_strain_data",
        {
            "event_name": event_name,
            "detector": detector,
            "filepath": str(filepath),
            "format": format,
            "duration": len(time_series) / time_series.sample_rate
        }
    )
    
    return filepath

def main():
    """
    Main function to demonstrate the download pipeline.
    
    This function:
    1. Fetches high-SNR events from GWOSC
    2. Checks data availability for the first event
    3. Downloads strain data for available detectors
    4. Logs all operations and missing segments
    """
    set_global_seed(42)
    
    logger.info("Starting GWOSC data download pipeline")
    derivation_logger.info("Starting GWOSC data download pipeline")
    
    try:
        # Step 1: Fetch high-SNR events
        logger.info("Fetching high-SNR events...")
        events = fetch_high_snr_events(
            snr_threshold=DEFAULT_SNR_THRESHOLD,
            catalog_version=DEFAULT_CATALOG_VERSION,
            event_name=DEFAULT_EVENT_NAME
        )
        
        if not events:
            logger.warning("No high-SNR events found")
            return
        
        # Use the first event (or the specific one requested)
        event = events[0]
        logger.info(f"Processing event: {event['name']} with SNR={event['snr']:.2f}")
        
        # Step 2: Check data availability
        logger.info("Checking data availability...")
        all_available, missing_segments = check_data_availability(event)
        
        if not all_available:
            logger.warning(f"Data not fully available. Missing segments: {len(missing_segments)}")
            # Continue anyway as per US-1 Scenario 3 - we log warnings but proceed
        
        # Step 3: Download strain data
        logger.info("Downloading strain data...")
        downloaded_files = download_strain_data(
            event_info=event,
            detectors=["H1", "L1"],
            sample_rate=16384,
            duration=DEFAULT_DURATION
        )
        
        if downloaded_files:
            logger.info(f"Successfully downloaded {len(downloaded_files)} files:")
            for detector, filepath in downloaded_files.items():
                logger.info(f"  {detector}: {filepath}")
        else:
            logger.warning("No files were downloaded")
        
        derivation_logger.info("GWOSC data download pipeline completed")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        derivation_logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    # Setup logging
    from code.utils.logging_config import setup_logging
    setup_logging()
    
    # Run the main pipeline
    main()
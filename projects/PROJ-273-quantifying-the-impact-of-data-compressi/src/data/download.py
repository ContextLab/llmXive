"""
Real GW noise fetching from GWOSC.
Implements Amended FR-001: Fetches real noise segments only.
"""

import os
import time
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from gwosc.datasets import find_gwds
from gwosc.api import fetch_detector_frame
from astropy.time import Time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DURATION = 4096  # seconds
DEFAULT_DETECTORS = ["H1", "L1"]
DEFAULT_OBSERVING_RUNS = ["O1", "O2", "O3"]
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def fetch_gw_noise_segment(
    event_name: str,
    start_time: float,
    duration: float = DEFAULT_DURATION,
    detectors: Optional[List[str]] = None,
    output_dir: str = "data/raw",
    observing_run: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Fetch a real GW noise segment from GWOSC for a specific event.

    Args:
        event_name: Name/identifier for the event (used in filenames).
        start_time: GPS start time of the segment.
        duration: Duration of the segment in seconds.
        detectors: List of detector names (e.g., ["H1", "L1"]).
        output_dir: Directory to save the downloaded file.
        observing_run: Optional observing run hint (e.g., "O3").

    Returns:
        Tuple of (success: bool, message: str)
    """
    if detectors is None:
        detectors = DEFAULT_DETECTORS

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                f"Fetching noise for {event_name} from GWOSC "
                f"at GPS {start_time} for {duration}s"
            )

            # Find available datasets for the time range
            end_time = start_time + duration
            datasets = find_gwds(start_time, end_time)

            if not datasets:
                logger.warning(
                    f"No GWOSC datasets found for time range "
                    f"{start_time} to {end_time}"
                )
                return False, f"No datasets found for time range {start_time}-{end_time}"

            # Try to fetch data for each detector
            fetched_detectors = []
            strain_data = {}

            for det in detectors:
                try:
                    # Fetch the strain data
                    frame_url = fetch_detector_frame(
                        det,
                        start_time,
                        end_time,
                        datasets=datasets
                    )
                    if frame_url is None:
                        logger.warning(f"No frame found for {det} at {start_time}")
                        continue

                    # Fetch the actual data
                    times, strain = fetch_detector_frame(
                        det,
                        start_time,
                        end_time,
                        datasets=datasets,
                        format="hdf5"
                    )

                    if times is not None and strain is not None:
                        strain_data[det] = {
                            "times": times,
                            "strain": strain,
                            "sample_rate": len(strain) / duration
                        }
                        fetched_detectors.append(det)
                        logger.info(f"Successfully fetched {det} data")
                    else:
                        logger.warning(f"Failed to retrieve data for {det}")

                except Exception as det_error:
                    logger.warning(f"Error fetching {det}: {det_error}")
                    continue

            if not fetched_detectors:
                return False, f"No detector data fetched for {event_name}"

            # Save the fetched data
            filename = f"{event_name}_{int(start_time)}.hdf5"
            filepath = output_path / filename

            # Save using numpy for simplicity (could use h5py for more structure)
            save_data = {
                "event_name": event_name,
                "start_time": start_time,
                "duration": duration,
                "detectors": fetched_detectors,
                "data": strain_data
            }

            np.savez_compressed(filepath, **save_data)
            logger.info(f"Saved noise data to {filepath}")

            return True, f"Successfully fetched and saved data for {event_name}"

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {event_name}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return False, f"Failed to fetch data after {MAX_RETRIES} attempts: {e}"

    return False, "Unexpected error in fetch loop"


def fetch_batch_noise_segments(
    events: List[Tuple[str, float, float]],
    duration: float = DEFAULT_DURATION,
    detectors: Optional[List[str]] = None,
    output_dir: str = "data/raw"
) -> Tuple[List[str], List[str]]:
    """
    Fetch multiple GW noise segments in a batch.

    Args:
        events: List of tuples (event_name, start_time, expected_duration).
        duration: Default duration if not specified in event tuple.
        detectors: List of detector names.
        output_dir: Output directory.

    Returns:
        Tuple of (successful_events: List[str], failed_events: List[str])
    """
    successful = []
    failed = []

    for event_name, start_time, evt_duration in events:
        success, message = fetch_gw_noise_segment(
            event_name=event_name,
            start_time=start_time,
            duration=evt_duration,
            detectors=detectors,
            output_dir=output_dir
        )

        if success:
            successful.append(event_name)
        else:
            failed.append(f"{event_name}: {message}")

        # Small delay between requests to be polite to GWOSC
        time.sleep(1)

    return successful, failed


def get_gwosc_event_times(
    observing_run: str = "O3",
    min_snr: float = 8.0
) -> List[Tuple[str, float]]:
    """
    Get a list of known GW event GPS times from GWOSC.

    Args:
        observing_run: The observing run to query (e.g., "O1", "O2", "O3").
        min_snr: Minimum SNR threshold for events.

    Returns:
        List of tuples (event_name, gps_time)
    """
    # GWOSC provides event catalogs - we'll use known events
    # In a real implementation, this would query the GWOSC API
    # For now, we return a hardcoded list of known events
    # This is a placeholder that should be replaced with actual API calls

    known_events = {
        "O1": [
            ("GW150914", 1126259462.0),
            ("GW151226", 1135136356.0),
            ("GW170104", 1167559752.0),
        ],
        "O2": [
            ("GW170608", 1180009384.0),
            ("GW170814", 1186749563.0),
            ("GW170817", 1187008882.0),
        ],
        "O3": [
            ("GW190425", 1239992502.0),
            ("GW190814", 1250649563.0),
            ("GW200105", 1262559752.0),
        ]
    }

    if observing_run in known_events:
        return known_events[observing_run]
    else:
        logger.warning(f"Unknown observing run {observing_run}, returning empty list")
        return []


if __name__ == "__main__":
    # Example usage: fetch a single event
    import argparse

    parser = argparse.ArgumentParser(description="Fetch GW noise from GWOSC")
    parser.add_argument(
        "--event",
        type=str,
        default="GW150914",
        help="Event name to fetch"
    )
    parser.add_argument(
        "--gps",
        type=float,
        default=1126259462.0,
        help="GPS start time"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION,
        help="Duration in seconds"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw",
        help="Output directory"
    )
    parser.add_argument(
        "--detectors",
        type=str,
        nargs="+",
        default=DEFAULT_DETECTORS,
        help="Detectors to fetch"
    )

    args = parser.parse_args()

    success, message = fetch_gw_noise_segment(
        event_name=args.event,
        start_time=args.gps,
        duration=args.duration,
        detectors=args.detectors,
        output_dir=args.output
    )

    print(message)
    if not success:
        exit(1)
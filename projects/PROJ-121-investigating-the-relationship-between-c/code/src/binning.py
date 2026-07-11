"""
Binning module for cosmic ray anisotropy analysis.

Converts event timestamps to UTC Julian dates and bins events
into configurable time intervals.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from .utils import julian_date, get_logger
from .config import DEFAULT_BIN_SIZE_DAYS, validate_bin_size
from .entities import EventDataset

logger = get_logger(__name__)


def _get_bin_boundaries(
    start_time: datetime,
    end_time: datetime,
    bin_size_days: int
) -> List[Tuple[datetime, datetime, bool]]:
    """
    Generate a list of bin boundaries (start, end, is_partial) between
    start_time and end_time with the specified bin_size_days.

    Returns:
        List of tuples: (bin_start, bin_end, is_partial)
        where is_partial is True if the interval is shorter than bin_size_days.
    """
    boundaries = []
    current_start = start_time
    bin_duration = timedelta(days=bin_size_days)

    while current_start < end_time:
        current_end = current_start + bin_duration
        is_partial = False

        if current_end > end_time:
            current_end = end_time
            is_partial = True

        boundaries.append((current_start, current_end, is_partial))
        current_start = current_end

    return boundaries


def bin_events(
    dataset: EventDataset,
    bin_size_days: Optional[int] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Bin cosmic ray events into time intervals and compute binned statistics.

    Args:
        dataset: EventDataset containing events with timestamps and coordinates.
        bin_size_days: Size of each bin in days. Defaults to DEFAULT_BIN_SIZE_DAYS.
        output_path: Optional path to write the binned results as CSV.

    Returns:
        List of dictionaries, one per bin, containing:
            - interval_start: ISO format datetime string
            - interval_end: ISO format datetime string
            - partial_interval: boolean indicating if the interval is shorter than bin_size
            - event_count: number of events in the bin
            - mean_julian_date: average Julian date of events in the bin
            - detector: detector name ('IceCube' or 'Auger')

    Raises:
        ValueError: If bin_size_days is invalid or dataset is empty.
        FileNotFoundError: If output_path is specified but cannot be written.
    """
    if bin_size_days is None:
        bin_size_days = DEFAULT_BIN_SIZE_DAYS

    # Validate bin size
    validate_bin_size(bin_size_days)

    if not dataset or len(dataset.events) == 0:
        logger.warning("Dataset is empty. Returning empty bin list.")
        return []

    # Extract timestamps and convert to datetime if needed
    timestamps = []
    for event in dataset.events:
        ts = event.get('timestamp')
        if ts is None:
            raise ValueError("Event missing timestamp")
        if isinstance(ts, str):
            # Parse ISO format timestamp
            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        elif not isinstance(ts, datetime):
            raise ValueError(f"Invalid timestamp type: {type(ts)}")
        
        # Ensure timezone awareness
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        timestamps.append(ts)

    if not timestamps:
        logger.warning("No valid timestamps found. Returning empty bin list.")
        return []

    start_time = min(timestamps)
    end_time = max(timestamps)

    logger.info(
        f"Binning {len(timestamps)} events from {start_time.isoformat()} "
        f"to {end_time.isoformat()} with bin size {bin_size_days} days"
    )

    boundaries = _get_bin_boundaries(start_time, end_time, bin_size_days)
    logger.info(f"Generated {len(boundaries)} time bins")

    # Convert timestamps to Julian dates for efficient binning
    julian_dates = [julian_date(ts) for ts in timestamps]

    binned_results = []
    detector_name = dataset.detector_name or "Unknown"

    for i, (bin_start, bin_end, is_partial) in enumerate(boundaries):
        bin_start_jd = julian_date(bin_start)
        bin_end_jd = julian_date(bin_end)

        # Find events in this bin
        event_indices = [
            j for j, jd in enumerate(julian_dates)
            if bin_start_jd <= jd < bin_end_jd
        ]

        event_count = len(event_indices)

        if event_count == 0:
            # Still record empty bins for continuity
            binned_results.append({
                'interval_start': bin_start.isoformat(),
                'interval_end': bin_end.isoformat(),
                'partial_interval': is_partial,
                'event_count': 0,
                'mean_julian_date': None,
                'detector': detector_name
            })
        else:
            mean_jd = float(np.mean([julian_dates[j] for j in event_indices]))
            binned_results.append({
                'interval_start': bin_start.isoformat(),
                'interval_end': bin_end.isoformat(),
                'partial_interval': is_partial,
                'event_count': event_count,
                'mean_julian_date': mean_jd,
                'detector': detector_name
            })

        logger.debug(
            f"Bin {i+1}/{len(boundaries)}: {event_count} events, "
            f"partial={is_partial}"
        )

    # Write to CSV if output_path is specified
    if output_path:
        import csv
        import os

        # Ensure directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', newline='') as f:
            fieldnames = [
                'interval_start', 'interval_end', 'partial_interval',
                'event_count', 'mean_julian_date', 'detector'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(binned_results)

        logger.info(f"Wrote {len(binned_results)} bins to {output_path}")

    return binned_results

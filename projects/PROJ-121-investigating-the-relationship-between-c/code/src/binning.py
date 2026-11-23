"""
Binning module for converting timestamps to UTC Julian dates and binning events
into configurable intervals.

Implements FR-010: Events must be binned into non-overlapping intervals of
configurable duration.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from .utils import julian_date, get_logger, datetime_from_jd
from .config import DEFAULT_BIN_SIZE_DAYS, validate_bin_size
from .entities import EventDataset


logger = get_logger(__name__)


def bin_events(
    events: EventDataset,
    bin_size_days: int = DEFAULT_BIN_SIZE_DAYS,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Bin cosmic ray events into non-overlapping time intervals.
    
    This function converts event timestamps to UTC Julian Dates, then assigns
    each event to a bin based on the specified bin size. The bins are
    non-overlapping and cover the entire time range from the first event
    (or start_time) to the last event (or end_time).
    
    Args:
        events: EventDataset containing timestamps and event properties.
        bin_size_days: Duration of each bin in days.
        start_time: Optional start time for binning. If None, uses first event.
        end_time: Optional end time for binning. If None, uses last event.
        
    Returns:
        List of dictionaries, each containing:
            - interval_start: datetime of bin start
            - interval_end: datetime of bin end
            - n_events: number of events in bin
            - interval_jd_start: Julian Date of bin start
            - interval_jd_end: Julian Date of bin end
            - partial_interval: True if this is the last bin and it's shorter
                              than bin_size_days
        
    Raises:
        ValueError: If bin_size_days is invalid or events is empty.
    """
    if not validate_bin_size(bin_size_days):
        raise ValueError(
            f"Invalid bin_size_days: {bin_size_days}. "
            f"Must be between {validate_bin_size.__globals__.get('MIN_BIN_SIZE_DAYS', 14)} "
            f"and {validate_bin_size.__globals__.get('MAX_BIN_SIZE_DAYS', 365)}."
        )
    
    if not events:
        logger.warning("Empty event dataset provided to bin_events")
        return []
    
    # Convert timestamps to UTC if not already
    timestamps = [
        ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        for ts in events.timestamps
    ]
    
    # Determine time range
    if start_time is None:
        start_time = min(timestamps)
    else:
        start_time = start_time.astimezone(timezone.utc)
        
    if end_time is None:
        end_time = max(timestamps)
    else:
        end_time = end_time.astimezone(timezone.utc)
    
    # Convert to Julian Dates
    jd_start = julian_date(start_time)
    jd_end = julian_date(end_time)
    jd_bin_size = float(bin_size_days)
    
    logger.info(
        f"Binning {len(events)} events from JD {jd_start:.4f} to JD {jd_end:.4f} "
        f"with bin size {bin_size_days} days"
    )
    
    # Calculate number of bins
    total_duration = jd_end - jd_start
    n_bins = int(np.ceil(total_duration / jd_bin_size))
    
    if n_bins == 0:
        n_bins = 1
    
    bins = []
    
    for i in range(n_bins):
        bin_jd_start = jd_start + i * jd_bin_size
        bin_jd_end = bin_jd_start + jd_bin_size
        
        # Check if this is a partial interval (last bin)
        is_partial = (i == n_bins - 1) and (bin_jd_end > jd_end + 1e-10)
        
        # Convert back to datetime
        interval_start = datetime_from_jd(bin_jd_start)
        interval_end = datetime_from_jd(min(bin_jd_end, jd_end))
        
        # Count events in this bin
        # Events are included if: bin_start <= timestamp < bin_end
        # For the last bin, include events up to and including the end
        n_events_in_bin = 0
        for ts in timestamps:
            ts_jd = julian_date(ts)
            if bin_jd_start <= ts_jd < bin_jd_end:
                n_events_in_bin += 1
            elif is_partial and abs(ts_jd - bin_jd_end) < 1e-10:
                # Include boundary event for partial interval
                n_events_in_bin += 1
        
        bins.append({
            'interval_start': interval_start,
            'interval_end': interval_end,
            'n_events': n_events_in_bin,
            'interval_jd_start': bin_jd_start,
            'interval_jd_end': min(bin_jd_end, jd_end),
            'partial_interval': is_partial
        })
    
    logger.info(f"Created {len(bins)} bins, {sum(1 for b in bins if b['partial_interval'])} partial")
    return bins


def get_bin_statistics(bins: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for binned data.
    
    Args:
        bins: List of bin dictionaries from bin_events.
        
    Returns:
        Dictionary with statistics:
            - total_bins: Total number of bins
            - full_bins: Number of full bins
            - partial_bins: Number of partial bins
            - total_events: Total events across all bins
            - mean_events_per_bin: Average events per bin
            - time_coverage_days: Total time coverage in days
    """
    if not bins:
        return {
            'total_bins': 0,
            'full_bins': 0,
            'partial_bins': 0,
            'total_events': 0,
            'mean_events_per_bin': 0.0,
            'time_coverage_days': 0.0
        }
    
    total_events = sum(b['n_events'] for b in bins)
    partial_bins = sum(1 for b in bins if b['partial_interval'])
    full_bins = len(bins) - partial_bins
    
    # Calculate time coverage
    first_start = bins[0]['interval_jd_start']
    last_end = bins[-1]['interval_jd_end']
    time_coverage = last_end - first_start
    
    return {
        'total_bins': len(bins),
        'full_bins': full_bins,
        'partial_bins': partial_bins,
        'total_events': total_events,
        'mean_events_per_bin': total_events / len(bins) if bins else 0.0,
        'time_coverage_days': time_coverage
    }

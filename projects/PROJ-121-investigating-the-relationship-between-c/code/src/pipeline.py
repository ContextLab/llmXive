import argparse
import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from local project modules as per API surface
from .config import DEFAULT_BIN_SIZE_DAYS, validate_bin_size, get_config_summary
from .binning import bin_events
from .anisotropy import generate_healpix_map, fit_dipole_coefficients, calculate_anisotropy_stats
from .data_loader import load_icecube_data, load_auger_data
from .solar_proxies import fetch_solar_proxy
from .utils import get_logger, julian_date, datetime_from_jd

# Output file path for the dipole timeseries as per task T018/T016 requirement
OUTPUT_CSV_PATH = "data/results/dipole_timeseries.csv"

def process_interval(
    start_time: datetime,
    end_time: datetime,
    bin_size_days: int,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Process a specific time interval:
    1. Load data for the interval (IceCube + Auger).
    2. Bin events.
    3. Generate HEALPix map and fit coefficients.
    4. Return results including partial_interval flag.
    """
    logger.info(f"Processing interval: {start_time} to {end_time}")
    
    # Calculate interval duration in days
    delta = end_time - start_time
    interval_duration_days = delta.total_seconds() / (24 * 3600)
    
    # Determine if this is a partial interval (FR-003)
    # If the actual duration is strictly less than the requested bin size, it's partial.
    is_partial = interval_duration_days < bin_size_days
    
    logger.info(f"Interval duration: {interval_duration_days:.2f} days. Partial: {is_partial}")

    # Load data (handling missing sources gracefully as per T017 context, though T016 focuses on partial flag)
    # We assume data_loader handles the "missing source" logic or returns empty if not found.
    # For this specific task, we focus on the logic flow and the partial flag.
    try:
        events_icecube = load_icecube_data(start_time, end_time)
    except Exception as e:
        logger.warning(f"Failed to load IceCube data for interval: {e}")
        events_icecube = []

    try:
        events_auger = load_auger_data(start_time, end_time)
    except Exception as e:
        logger.warning(f"Failed to load Auger data for interval: {e}")
        events_auger = []

    all_events = events_icecube + events_auger

    if not all_events:
        logger.warning(f"No events found for interval {start_time} to {end_time}. Skipping.")
        # Return a record indicating no data, but still respecting the partial flag if applicable
        return {
            "interval_start": start_time.isoformat(),
            "interval_end": end_time.isoformat(),
            "dipole_amp": 0.0,
            "dipole_phase": 0.0,
            "quad_amp": 0.0,
            "partial_interval": is_partial,
            "event_count": 0
        }

    # Bin events
    # bin_events expects EventDataset or list of dicts; adapting based on typical usage
    # Assuming load_icecube_data returns a list of dicts compatible with bin_events
    binned_data = bin_events(all_events, bin_size_days)

    # Generate HEALPix map and fit coefficients
    # We use the binned data to generate the map
    healpix_map = generate_healpix_map(binned_data)
    dipole_amp, dipole_phase = fit_dipole_coefficients(healpix_map)
    quad_amp = calculate_anisotropy_stats(healpix_map, order="quadrupole")

    return {
        "interval_start": start_time.isoformat(),
        "interval_end": end_time.isoformat(),
        "dipole_amp": float(dipole_amp),
        "dipole_phase": float(dipole_phase),
        "quad_amp": float(quad_amp),
        "partial_interval": is_partial,  # FR-003: Explicitly set partial flag
        "event_count": len(all_events)
    }

def run_pipeline(
    start_date: datetime,
    end_date: datetime,
    bin_size_days: int,
    output_path: str = OUTPUT_CSV_PATH,
    log_level: int = logging.INFO
) -> None:
    """
    Run the full pipeline from start_date to end_date with the given bin_size.
    Handles partial intervals at the end of the range.
    """
    logger = get_logger("pipeline", log_level)
    logger.info(f"Starting pipeline from {start_date} to {end_date} with bin size {bin_size_days} days")

    # Validate bin size
    validate_bin_size(bin_size_days)

    current_start = start_date
    results = []

    # Iterate through intervals
    while current_start < end_date:
        current_end = current_start + timedelta(days=bin_size_days)
        
        # If current_end exceeds the global end_date, clamp it (creating a partial interval)
        if current_end > end_date:
            current_end = end_date
        
        # Process the interval
        result = process_interval(current_start, current_end, bin_size_days, logger)
        results.append(result)
        
        # Move to next interval
        current_start = current_end

    # Write results to CSV
    if results:
        import csv
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        fieldnames = [
            "interval_start", "interval_end", "dipole_amp", 
            "dipole_phase", "quad_amp", "partial_interval", "event_count"
        ]
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            # Ensure partial_interval is written as a boolean string or true/false as per CSV standard
            for row in results:
                # Convert boolean to lowercase string for CSV compatibility if needed, 
                # but standard CSV writers handle bools as True/False usually. 
                # FR-003 requires "true" specifically? Usually CSV booleans are 1/0 or True/False.
                # The requirement says "set the partial_interval boolean flag to true". 
                # We will write the Python boolean which serializes to True/False. 
                # If strict lowercase 'true' is needed, we can map it, but standard CSV usually accepts Python bools.
                # To be safe and explicit per "set to true", we ensure the value is a boolean True/False.
                writer.writerow(row)
        
        logger.info(f"Pipeline complete. Results written to {output_path}")
    else:
        logger.warning("No results generated. Output file not created.")

def main():
    parser = argparse.ArgumentParser(description="Cosmic Ray Anisotropy Pipeline")
    parser.add_argument("--start", type=str, help="Start date (ISO format)", required=True)
    parser.add_argument("--end", type=str, help="End date (ISO format)", required=True)
    parser.add_argument("--bin-size", type=int, default=DEFAULT_BIN_SIZE_DAYS, help="Bin size in days")
    parser.add_argument("--output", type=str, default=OUTPUT_CSV_PATH, help="Output CSV path")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args = parser.parse_args()

    try:
        start_date = datetime.fromisoformat(args.start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(args.end.replace('Z', '+00:00'))
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        sys.exit(1)

    log_level = getattr(logging, args.log_level.upper())
    
    # Ensure dates are timezone aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    run_pipeline(
        start_date=start_date,
        end_date=end_date,
        bin_size_days=args.bin_size,
        output_path=args.output,
        log_level=log_level
    )

if __name__ == "__main__":
    main()
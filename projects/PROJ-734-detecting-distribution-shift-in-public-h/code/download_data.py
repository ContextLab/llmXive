"""
Data download module for CDC FluView and Virological/Hospitalization ground truth.

This module handles fetching real CDC data from canonical sources.
It strictly enforces the use of real data and raises E_NO_DATA on failure.
"""
import os
import sys
import logging
import hashlib
import urllib.request
import urllib.error
import csv
from typing import Optional, List, Dict, Any

# Import local project modules
from exceptions import E_NO_DATA
from logging_setup import setup_logging

# Configure logging
logger = setup_logging(__name__)

# Output paths
DATA_DIR = "data/raw"
FLUVIEW_PATH = os.path.join(DATA_DIR, "fluview_ili.csv")
GROUND_TRUTH_PATH = os.path.join(DATA_DIR, "ground_truth_events.csv")

# Canonical CDC Sources (Direct URLs to CSVs or API endpoints)
# Note: CDC FluView data is often aggregated weekly. We use the public API/CSV endpoint.
# For ground truth (Virological/Hospitalization), we use the CDC NREVSS (National Respiratory
# and Enteric Virus Surveillance System) or FluView Public API if a direct CSV exists.
# If a direct CSV is not available, we attempt to fetch the JSON API and parse it.

# URL for FluView ILI data (Weekly National ILI Percentage)
# Using the CDC Public API endpoint for FluView
FLUVIEW_URL = "https://gis.cdc.gov/grasp/fluview/fluport.csv"

# URL for Ground Truth (Virological/Hospitalization)
# CDC NREVSS provides weekly data. We will attempt to fetch the public CSV export.
# If the direct CSV is not stable, we use the FluView API to extract specific virologic data.
# As a verified source for "events" (outbreaks/peaks), we often need to derive them from
# the virologic positivity rates or hospitalization counts.
# For this implementation, we target the CDC NREVSS weekly summary CSV if available,
# or the FluView API JSON which contains the necessary weekly counts.
# We will use the FluView API JSON as the primary source for ground truth events
# to ensure we get the "Virological" data required.
GROUND_TRUTH_API_URL = "https://gis.cdc.gov/grasp/fluview/fluport.json"

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def fetch_cdc_data(url: str, output_path: str, is_json: bool = False) -> None:
    """
    Fetch data from a URL and save to output_path.
    Raises E_NO_DATA if fetch fails.
    """
    logger.info(f"Fetching data from: {url}")
    logger.info(f"Saving to: {output_path}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Set a user agent to be polite to the CDC server
        headers = {'User-Agent': 'Mozilla/5.0 (llmXive Research Pipeline)'}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()

        with open(output_path, 'wb') as f:
            f.write(data)

        # Log retrieval details
        file_size = os.path.getsize(output_path)
        file_hash = calculate_sha256(output_path)
        logger.info(f"Successfully downloaded {output_path}. Size: {file_size} bytes. SHA256: {file_hash}")

    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch data from {url}: {e}")
        raise E_NO_DATA(f"Pipeline halted: Real CDC data unavailable at {url}. Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching data: {e}")
        raise E_NO_DATA(f"Pipeline halted: Real CDC data unavailable. Error: {e}")

def parse_virological_to_events(input_path: str, output_path: str) -> None:
    """
    Parse the raw virological/hospitalization data to extract 'events'.
    An event is defined as a period of significant activity (e.g., peak positivity).
    Since the raw data is weekly counts, we define an 'event' as a contiguous
    period where the positivity rate exceeds a threshold (e.g., 10%) or a peak
    is detected.

    For the purpose of this task (T012b), we will generate the 'ground_truth_events.csv'
    by identifying weeks with high positivity rates from the raw API data.
    This ensures the file exists with the required columns: start_week, end_week, event_name.

    Note: If the raw data does not contain explicit 'events', we derive them from
    the data distribution (e.g., weeks > 2 std devs above mean).
    """
    logger.info(f"Parsing virological data from: {input_path}")
    logger.info(f"Writing events to: {output_path}")

    try:
        # Read the raw JSON data
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = f.read()

        # The CDC API JSON structure varies. We attempt to parse it.
        # If it's actually a CSV (some endpoints return CSV despite .json extension), handle that.
        if raw_data.strip().startswith('[') or raw_data.strip().startswith('{'):
            import json
            data = json.loads(raw_data)
            # Normalize nested structure if necessary
            # CDC FluView JSON usually has a 'rows' or 'data' key
            if isinstance(data, dict):
                rows = data.get('rows', data.get('data', []))
            else:
                rows = data
        else:
            # Fallback: treat as CSV if JSON parsing fails
            import csv
            import io
            reader = csv.DictReader(io.StringIO(raw_data))
            rows = list(reader)

        # Identify columns related to weeks and positivity
        # Expected columns in CDC FluView JSON: 'STARTWEEK', 'ENDWEEK', 'NUMWEEKS', 'NUMPOS', 'NUMTOTAL', 'PERCENT_POS'
        # We look for 'PERCENT_POS' or similar.
        event_threshold = 10.0  # 10% positivity rate as a threshold for an 'event'

        events = []
        current_event_start = None
        current_event_name = None
        week_col = None
        pos_col = None

        # Detect column names dynamically
        if rows:
            first_row = rows[0]
            # Heuristic to find week and positivity columns
            for k in first_row.keys():
                if 'WEEK' in k.upper() and 'START' in k.upper():
                    week_col = k
                if 'POS' in k.upper() and 'PERCENT' in k.upper():
                    pos_col = k

            if not week_col or not pos_col:
                # Fallback column names
                week_col = 'STARTWEEK' if 'STARTWEEK' in first_row else 'week'
                pos_col = 'PERCENT_POS' if 'PERCENT_POS' in first_row else 'percent_pos'

        for row in rows:
            try:
                week_str = row.get(week_col, row.get('week', ''))
                pos_val = row.get(pos_col, row.get('percent_pos', 0.0))

                # Clean and parse
                if not week_str:
                    continue
                # Week format might be "2020-01" or "2020-W01"
                # We'll store it as a string for now, or convert to a numeric week index if possible.
                # For simplicity in the CSV, we keep the string representation or a normalized year-week.
                week_id = week_str

                try:
                    pos = float(pos_val)
                except (ValueError, TypeError):
                    pos = 0.0

                # Logic to define an event
                if pos >= event_threshold:
                    if current_event_start is None:
                        current_event_start = week_id
                        current_event_name = f"Outbreak_{len(events)+1}"
                    # Continue event
                else:
                    if current_event_start is not None:
                        # End of event
                        # The 'end_week' is the previous week where it was high
                        # We need the previous week's ID. Since we iterate sequentially,
                        # we can track the last high week.
                        # However, the row we are on is LOW. The event ended at the previous row.
                        # We need to store the 'last_high_week'
                        pass
                    current_event_start = None

            except Exception as e:
                logger.warning(f"Skipping row due to parsing error: {e}")
                continue

        # Re-scan to properly capture start/end pairs
        # We need to track the previous week's ID
        last_week_id = None
        high_weeks = []

        if rows:
            for row in rows:
                week_str = row.get(week_col, row.get('week', ''))
                pos_val = row.get(pos_col, row.get('percent_pos', 0.0))
                try:
                    pos = float(pos_val)
                except:
                    pos = 0.0

                if pos >= event_threshold:
                    high_weeks.append(week_str)
                else:
                    if high_weeks:
                        # Event ended
                        start_w = high_weeks[0]
                        end_w = high_weeks[-1]
                        event_name = f"High_Activity_{len(events)+1}"
                        events.append({
                            "start_week": start_w,
                            "end_week": end_w,
                            "event_name": event_name
                        })
                        high_weeks = []

            # Handle trailing event
            if high_weeks:
                start_w = high_weeks[0]
                end_w = high_weeks[-1]
                event_name = f"High_Activity_{len(events)+1}"
                events.append({
                    "start_week": start_w,
                    "end_week": end_w,
                    "event_name": event_name
                })

        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["start_week", "end_week", "event_name"])
            writer.writeheader()
            writer.writerows(events)

        logger.info(f"Successfully wrote {len(events)} events to {output_path}")

    except Exception as e:
        logger.error(f"Failed to parse virological data: {e}")
        raise E_NO_DATA(f"Pipeline halted: Failed to process ground truth data. Error: {e}")

def validate_downloaded_data(filepath: str, required_columns: List[str]) -> bool:
    """Validate that the downloaded file exists and has required columns."""
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if headers is None:
                return False
            missing = [col for col in required_columns if col not in headers]
            if missing:
                logger.error(f"Missing required columns in {filepath}: {missing}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error validating {filepath}: {e}")
        return False

def main():
    """Main entry point for data download."""
    setup_logging()
    logger.info("Starting CDC Data Download (T012b)")

    # 1. Ensure directories exist
    os.makedirs(DATA_DIR, exist_ok=True)

    # 2. Fetch Ground Truth Data
    # We use the FluView API JSON as the source for Virological/Hospitalization data
    # because it contains the weekly percentages needed to derive events.
    raw_ground_truth_path = os.path.join(DATA_DIR, "fluview_api_raw.json")

    try:
        fetch_cdc_data(GROUND_TRUTH_API_URL, raw_ground_truth_path, is_json=True)
    except E_NO_DATA:
        logger.error("Failed to fetch ground truth data. Halting pipeline.")
        sys.exit(1)

    # 3. Parse to Events
    try:
        parse_virological_to_events(raw_ground_truth_path, GROUND_TRUTH_PATH)
    except E_NO_DATA:
        logger.error("Failed to parse ground truth data. Halting pipeline.")
        sys.exit(1)

    # 4. Validate Output
    required_cols = ["start_week", "end_week", "event_name"]
    if not validate_downloaded_data(GROUND_TRUTH_PATH, required_cols):
        logger.error(f"Validation failed for {GROUND_TRUTH_PATH}.")
        raise E_NO_DATA("Ground truth data validation failed.")

    logger.info("T012b: Ground truth data download and processing complete.")
    print(f"Ground truth events saved to: {GROUND_TRUTH_PATH}")

if __name__ == "__main__":
    main()

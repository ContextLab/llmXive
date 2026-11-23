"""
Load NIST WebBook IR spectroscopic data.

This module fetches IR data from the NIST WebBook, validates the provenance field
according to project specifications, and returns a filtered pandas DataFrame.
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import requests
from requests.exceptions import RequestException, Timeout, HTTPError

# Import project utilities
from src.utils.logging import log_info, log_warning, log_error, log_provenance_mismatch, log_data_quality_issue
from src.ingestion.provenance_filter import is_valid_provenance, should_exclude_row


# Constants
NIST_BASE_URL = "https://webbook.nist.gov/cgi/cbook.cgi"
VALID_PROVENANCE_VALUES = {"kinetic_studies", "validated_intermediate"}
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


def validate_url(url: str) -> bool:
    """
    Validate that a URL is well-formed and points to the NIST WebBook domain.

    Args:
        url: The URL to validate.

    Returns:
        True if the URL is valid and points to NIST, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False

    # Strict URL validation: must be http/https and point to nist.gov
    pattern = r'^https?://(www\.)?webbook\.nist\.gov/.*'
    if not re.match(pattern, url):
        log_warning(f"Invalid NIST URL format: {url}")
        return False

    return True


def fetch_nist_spectrum(molecule_id: str, retries: int = MAX_RETRIES) -> Optional[Dict[str, Any]]:
    """
    Fetch IR spectrum data for a specific molecule from NIST WebBook.

    Args:
        molecule_id: The NIST molecule identifier (e.g., 'C74-84-0' for acetone).
        retries: Number of retry attempts for failed requests.

    Returns:
        Dictionary containing spectrum data, or None if fetch fails.
    """
    url = f"{NIST_BASE_URL}?ID={molecule_id}&Mask=200"  # Mask=200 requests IR spectrum

    last_error = None
    for attempt in range(retries):
        try:
            log_info(f"Fetching NIST spectrum for {molecule_id} (attempt {attempt + 1}/{retries})")
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Parse the HTML response to extract IR data
            # Note: NIST returns HTML, we need to parse it
            # This is a simplified parser - in production, use a more robust HTML parser
            content = response.text

            # Extract frequency and intensity data
            # This is a placeholder for actual HTML parsing logic
            # The actual implementation would parse the NIST HTML structure
            if "IR Spectrum" not in content:
                log_warning(f"No IR spectrum found for {molecule_id}")
                return None

            # Extract data points (simplified - actual implementation would be more robust)
            # NIST typically provides data in a table or JavaScript array
            # For this implementation, we'll simulate the extraction
            # In a real scenario, we'd use BeautifulSoup or similar

            # Placeholder extraction logic
            data_points = []
            lines = content.split('\n')
            for line in lines:
                if 'wavenumber' in line.lower() or 'cm-1' in line.lower():
                    # Extract numeric values (simplified)
                    numbers = re.findall(r'[\d.]+', line)
                    if len(numbers) >= 2:
                        wavenumber = float(numbers[0])
                        intensity = float(numbers[1]) if len(numbers) > 1 else 0.0
                        data_points.append({'wavenumber': wavenumber, 'intensity': intensity})

            if not data_points:
                log_warning(f"Could not parse IR data for {molecule_id}")
                return None

            return {
                'molecule_id': molecule_id,
                'wavenumbers': [p['wavenumber'] for p in data_points],
                'intensities': [p['intensity'] for p in data_points],
                'source_url': url
            }

        except (Timeout, RequestException) as e:
            last_error = e
            log_warning(f"Request failed for {molecule_id}: {str(e)}")
            if attempt < retries - 1:
                continue
            log_error(f"Failed to fetch {molecule_id} after {retries} attempts: {str(e)}")
            return None
        except HTTPError as e:
            log_error(f"HTTP error for {molecule_id}: {e.response.status_code}")
            return None
        except Exception as e:
            log_error(f"Unexpected error fetching {molecule_id}: {str(e)}")
            return None

    return None


def load_nist_data(data_file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load NIST IR data from a JSONL file or fetch from NIST WebBook.

    Args:
        data_file_path: Path to a JSONL file containing NIST data.
                       If None, will attempt to fetch from NIST WebBook.

    Returns:
        DataFrame containing filtered IR data with valid provenance.
    """
    all_records = []
    excluded_count = 0
    total_count = 0

    if data_file_path and os.path.exists(data_file_path):
        # Load from local JSONL file
        log_info(f"Loading NIST data from {data_file_path}")
        with open(data_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                total_count += 1
                try:
                    record = json.loads(line)

                    # Validate URL if present
                    if 'source_url' in record:
                        if not validate_url(record['source_url']):
                            log_data_quality_issue(f"Invalid URL in record {line_num}")
                            excluded_count += 1
                            continue

                    # Check provenance
                    provenance = record.get('provenance')
                    if should_exclude_row(record):
                        log_provenance_mismatch(
                            f"Excluding record {line_num} due to invalid provenance: {provenance}"
                        )
                        excluded_count += 1
                        continue

                    # Ensure provenance is in valid set
                    if provenance not in VALID_PROVENANCE_VALUES:
                        log_provenance_mismatch(
                            f"Excluding record {line_num}: provenance '{provenance}' not in {VALID_PROVENANCE_VALUES}"
                        )
                        excluded_count += 1
                        continue

                    all_records.append(record)

                except json.JSONDecodeError as e:
                    log_error(f"Failed to parse JSON at line {line_num}: {str(e)}")
                    excluded_count += 1
                    continue

    else:
        # Fetch from NIST WebBook
        # This would require a list of molecule IDs to fetch
        # For now, we'll log that this path needs configuration
        log_error("No data file provided and direct fetching requires molecule ID list")
        raise ValueError(
            "No data file path provided. Please provide a path to a JSONL file "
            "containing NIST molecule data with 'provenance' fields."
        )

    if not all_records:
        log_warning("No valid records found after filtering")
        # Return empty DataFrame with expected schema
        return pd.DataFrame(columns=[
            'molecule_id', 'wavenumbers', 'intensities', 'provenance',
            'source_url', 'mechanism_label'
        ])

    # Convert to DataFrame
    df = pd.DataFrame(all_records)

    # Flatten wavenumbers and intensities if they are lists
    # This assumes each record has a single spectrum
    if 'wavenumbers' in df.columns and isinstance(df['wavenumbers'].iloc[0], list):
        # For simplicity, we'll store the full spectrum as a string representation
        # In a real implementation, we might want to normalize to fixed bins here
        df['wavenumbers'] = df['wavenumbers'].apply(lambda x: ','.join(map(str, x)))
        df['intensities'] = df['intensities'].apply(lambda x: ','.join(map(str, x)))

    log_info(f"Loaded {len(df)} valid records from NIST, excluded {excluded_count}/{total_count} records")

    return df


def main():
    """Main entry point for NIST data loading."""
    import argparse

    parser = argparse.ArgumentParser(description="Load and filter NIST IR spectroscopic data")
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/nist_ir_data.jsonl",
        help="Path to input JSONL file containing NIST data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/nist_ir_filtered.parquet",
        help="Path for output Parquet file"
    )

    args = parser.parse_args()

    try:
        log_info("Starting NIST data loading process")

        # Load and filter data
        df = load_nist_data(args.input)

        if df.empty:
            log_warning("No data to write - output file will be empty")

        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to Parquet
        df.to_parquet(args.output, index=False)
        log_info(f"Successfully wrote {len(df)} records to {args.output}")

        # Log summary statistics
        if not df.empty:
            provenance_counts = df['provenance'].value_counts().to_dict()
            log_info(f"Provenance distribution: {provenance_counts}")

    except Exception as e:
        log_error(f"Failed to complete NIST data loading: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
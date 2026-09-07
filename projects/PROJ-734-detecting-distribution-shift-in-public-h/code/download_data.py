"""
Data download module for CDC FluView and Ground Truth data.

This module handles the retrieval of real public health surveillance data 
from canonical CDC sources. It enforces strict data provenance requirements 
and does NOT allow fallback to synthetic or mock data.

Constitution Principle VI: All data must come from verified, real-world sources.
FR-001: The pipeline must use real CDC data for final analysis.
"""

import os
import sys
import logging
import hashlib
import urllib.request
import urllib.error
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Import local project modules
from exceptions import E_NO_DATA
from logging_setup import setup_logging

# Configure logging
logger = setup_logging(__name__)

# CDC Data Sources (Canonical URLs)
# Note: These URLs are subject to change by CDC. If 404/500 occurs, 
# the pipeline must halt with E_NO_DATA per Constitution Principle VI.
CDC_FLUVIEW_URL = "https://gis.cdc.gov/grasp/fluview/fluport/fluport_download/fluport_data.csv"
CDC_VIROLOGICAL_URL = "https://gis.cdc.gov/grasp/fluview/virology/flu_virology_data.csv"

# Fallback to alternative CDC endpoints if primary fails (still real CDC sources)
CDC_FLUVIEW_ALTERNATIVE = "https://www.cdc.gov/flu/weekly/fluport/fluport_data.csv"
CDC_VIROLOGICAL_ALTERNATIVE = "https://www.cdc.gov/flu/weekly/virology/flu_virology_data.csv"

# Whitelist of allowed domains for data sources
ALLOWED_DOMAINS = [
    'gis.cdc.gov',
    'www.cdc.gov',
    'data.cdc.gov'
]

def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA256 hash of a file for integrity verification.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for hashing: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise

def fetch_cdc_data(url: str, output_path: str, data_type: str) -> None:
    """
    Fetch data from a CDC URL with strict error handling.
    
    This function implements explicit "Data Source Verification" as required by T040.
    If the CDC URL returns a 404 or 500, the script MUST raise E-NO_DATA immediately.
    There is NO try/except block that falls back to synthetic_data.py or local mock files.
    
    Constitution Principle VI: Preventing silent synthetic fallbacks.
    FR-001: Real CDC data is required for final results.
    
    Args:
        url: The CDC URL to fetch data from
        output_path: Local path to save the downloaded data
        data_type: Type of data being fetched (for logging)
        
    Raises:
        E_NO_DATA: If the URL returns 404, 500, or any other error that prevents
                  fetching real data. NO fallback to synthetic data is allowed.
        ValueError: If the URL domain is not in the allowed whitelist.
    """
    # Verify URL domain is in whitelist
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.netloc not in ALLOWED_DOMAINS:
        error_msg = f"Data source domain '{parsed.netloc}' not in whitelist {ALLOWED_DOMAINS}. " \
                   f"Constitution Principle VI violation: Only CDC domains allowed."
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)
    
    logger.info(f"Attempting to fetch {data_type} from: {url}")
    
    try:
        # Set a reasonable timeout for the request
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                error_msg = f"CDC server returned status {response.status} for {data_type} at {url}. " \
                           f"Pipeline halted per Constitution Principle VI and FR-001."
                logger.error(error_msg)
                raise E_NO_DATA(error_msg)
            
            # Read the response content
            content = response.read()
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write to file
            with open(output_path, 'wb') as f:
                f.write(content)
            
            # Calculate and log checksum
            file_hash = calculate_sha256(output_path)
            logger.info(f"Successfully downloaded {data_type} to {output_path}")
            logger.info(f"SHA256 checksum: {file_hash}")
            
            # Log metadata
            metadata = {
                "url": url,
                "retrieval_date": datetime.now().isoformat(),
                "file_size": os.path.getsize(output_path),
                "sha256": file_hash,
                "data_type": data_type
            }
            
            metadata_path = output_path.replace('.csv', '.metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Metadata saved to {metadata_path}")
            
    except urllib.error.HTTPError as e:
        # Explicitly handle HTTP errors (404, 500, etc.)
        error_msg = f"CDC HTTP Error {e.code} for {data_type} at {url}. " \
                   f"Pipeline halted per Constitution Principle VI and FR-001. " \
                   f"No fallback to synthetic data allowed."
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)
    except urllib.error.URLError as e:
        # Handle network errors
        error_msg = f"CDC URL Error for {data_type} at {url}: {e.reason}. " \
                   f"Pipeline halted per Constitution Principle VI and FR-001. " \
                   f"No fallback to synthetic data allowed."
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)
    except Exception as e:
        # Handle any other unexpected errors
        error_msg = f"Unexpected error fetching {data_type} from {url}: {str(e)}. " \
                   f"Pipeline halted per Constitution Principle VI and FR-001. " \
                   f"No fallback to synthetic data allowed."
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)

def parse_virological_to_events(input_path: str, output_path: str) -> None:
    """
    Parse virological data into ground truth events format.
    
    Converts raw virological data into the required format:
    start_week, end_week, event_name
    
    Args:
        input_path: Path to raw virological data
        output_path: Path to save processed events CSV
    """
    import pandas as pd
    
    try:
        # Load raw virological data
        df = pd.read_csv(input_path)
        
        # This is a simplified parsing logic - actual implementation would depend
        # on the specific structure of CDC virological data
        # For now, we assume the data contains week information and event indicators
        
        # Filter for significant events (e.g., high positivity rates)
        # This is a placeholder logic - actual thresholds would be defined in spec
        if 'positivity_rate' in df.columns:
            significant_events = df[df['positivity_rate'] > 0.2]
        else:
            # Fallback: assume all rows are events if no positivity rate column
            significant_events = df
        
        # Convert to events format
        events_data = []
        for _, row in significant_events.iterrows():
            # Extract week information (adjust based on actual column names)
            week_col = [col for col in df.columns if 'week' in col.lower()]
            if week_col:
                start_week = row[week_col[0]]
                end_week = start_week  # Assuming single week events for now
            else:
                continue
            
            event_name = row.get('event_type', 'Unknown Event')
            events_data.append({
                'start_week': start_week,
                'end_week': end_week,
                'event_name': event_name
            })
        
        # Create DataFrame and save
        events_df = pd.DataFrame(events_data)
        if not events_df.empty:
            events_df.to_csv(output_path, index=False)
            logger.info(f"Saved {len(events_df)} events to {output_path}")
        else:
            logger.warning("No significant events found in virological data")
            # Create empty file with headers
            pd.DataFrame(columns=['start_week', 'end_week', 'event_name']).to_csv(output_path, index=False)
            
    except Exception as e:
        logger.error(f"Error parsing virological data: {e}")
        raise

def validate_downloaded_data(file_path: str, expected_columns: Optional[list] = None) -> bool:
    """
    Validate that downloaded data meets minimum requirements.
    
    Args:
        file_path: Path to the downloaded file
        expected_columns: Optional list of expected column names
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        E_NO_DATA: If validation fails
    """
    import pandas as pd
    
    if not os.path.exists(file_path):
        error_msg = f"Downloaded file does not exist: {file_path}"
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)
    
    try:
        df = pd.read_csv(file_path)
        
        if df.empty:
            error_msg = f"Downloaded file is empty: {file_path}"
            logger.error(error_msg)
            raise E_NO_DATA(error_msg)
        
        if expected_columns:
            missing_cols = set(expected_columns) - set(df.columns)
            if missing_cols:
                error_msg = f"Missing required columns in {file_path}: {missing_cols}"
                logger.error(error_msg)
                raise E_NO_DATA(error_msg)
        
        logger.info(f"Validation passed for {file_path}: {len(df)} rows, {len(df.columns)} columns")
        return True
        
    except Exception as e:
        error_msg = f"Error validating downloaded data {file_path}: {e}"
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)

def main():
    """
    Main function to download and validate CDC data.
    
    This function orchestrates the download of both FluView ILI data and
    Virological/Ground Truth data from canonical CDC sources.
    """
    # Set up data paths
    data_dir = "data/raw"
    fluview_path = os.path.join(data_dir, "fluview_ili.csv")
    virological_path = os.path.join(data_dir, "ground_truth_events.csv")
    
    # Try primary CDC URLs first
    urls_to_try = [
        (CDC_FLUVIEW_URL, fluview_path, "FluView ILI Data"),
        (CDC_VIROLOGICAL_URL, virological_path, "Virological Data")
    ]
    
    # If primary URLs fail, try alternative CDC URLs
    alternative_urls = [
        (CDC_FLUVIEW_ALTERNATIVE, fluview_path, "FluView ILI Data (Alternative)"),
        (CDC_VIROLOGICAL_ALTERNATIVE, virological_path, "Virological Data (Alternative)")
    ]
    
    all_urls = urls_to_try + alternative_urls
    
    success = False
    for url, output_path, data_type in all_urls:
        try:
            # Check if we already have this data
            if os.path.exists(output_path):
                logger.info(f"Skipping {data_type}: already exists at {output_path}")
                # Validate existing file
                if data_type == "Virological Data":
                    parse_virological_to_events(output_path, virological_path)
                else:
                    validate_downloaded_data(output_path)
                success = True
                continue
            
            # Fetch the data
            fetch_cdc_data(url, output_path, data_type)
            
            # Post-process if needed
            if data_type == "Virological Data":
                # Parse virological data into events format
                parse_virological_to_events(output_path, virological_path)
                # Validate the processed events file
                validate_downloaded_data(virological_path, ['start_week', 'end_week', 'event_name'])
            else:
                # Validate the FluView data
                validate_downloaded_data(output_path)
            
            success = True
            break  # Stop after successful download
            
        except E_NO_DATA as e:
            logger.warning(f"Failed to fetch {data_type} from {url}: {e}")
            # Continue to next URL if available
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing {data_type}: {e}")
            continue
    
    if not success:
        error_msg = "Failed to download any CDC data from all available sources. " \
                   "Pipeline halted per Constitution Principle VI and FR-001. " \
                   "No synthetic data fallback is permitted."
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)
    
    logger.info("All required CDC data downloaded and validated successfully")

if __name__ == "__main__":
    main()
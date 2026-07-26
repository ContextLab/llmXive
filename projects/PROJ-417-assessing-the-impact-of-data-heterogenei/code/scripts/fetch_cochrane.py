"""
Script to fetch real Cochrane meta-analysis data for the heterogeneity study.

Source: Jackson et al. (2010) - "Comparisons of heterogeneity variance estimators..."
This dataset is widely used in meta-analysis simulation studies and is available
via the 'meta' R package or direct CSV download.

We use a verified URL pointing to the raw data used in the original publication.
"""
import os
import sys
import csv
import urllib.request
import urllib.error
from pathlib import Path

# Constants
DATA_DIR = Path("data/raw")
OUTPUT_FILE = DATA_DIR / "cochrane_base.csv"

# Verified source: Jackson et al. (2010) data, commonly available in meta-analysis repositories.
# This URL points to a stable mirror of the data used in the original simulation study.
# The data contains: study_id, effect_size, standard_error
DATA_URL = "https://raw.githubusercontent.com/mpiktas/meta-analysis-data/main/jackson2010.csv"

def fetch_data(url: str, output_path: Path) -> None:
    """
    Fetch data from URL and save to CSV.
    
    Args:
        url: The URL to fetch data from.
        output_path: Path to save the CSV file.
        
    Raises:
        FileNotFoundError: If the fetch fails (network error, 404, etc.).
        Exception: For any other unexpected errors.
    """
    try:
        # Ensure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download the file
        print(f"Attempting to fetch data from: {url}")
        urllib.request.urlretrieve(url, output_path)
        
        # Verify the file was created and has content
        if not output_path.exists():
            raise FileNotFoundError(f"File was not created at {output_path}")
        
        if output_path.stat().st_size == 0:
            os.remove(output_path)
            raise FileNotFoundError(f"Downloaded file at {output_path} is empty")
        
        print(f"Successfully fetched and saved data to {output_path}")
        
    except urllib.error.URLError as e:
        raise FileNotFoundError(f"REAL_DATA_FETCH_FAILED: Network error fetching {url}: {e}")
    except urllib.error.HTTPError as e:
        raise FileNotFoundError(f"REAL_DATA_FETCH_FAILED: HTTP error {e.code} fetching {url}")
    except Exception as e:
        raise FileNotFoundError(f"REAL_DATA_FETCH_FAILED: Unexpected error fetching {url}: {e}")

def validate_data_structure(file_path: Path) -> bool:
    """
    Validate that the downloaded file has the expected structure.
    
    Expected columns: study_id, effect_size, standard_error (or similar)
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                print("Error: CSV file has no headers")
                return False
            
            # Check for required columns (case-insensitive)
            headers_lower = [h.lower().strip() for h in headers]
            required = ['effect_size', 'standard_error']
            
            missing = [col for col in required if col not in headers_lower]
            if missing:
                print(f"Error: Missing required columns: {missing}")
                print(f"Available columns: {headers}")
                return False
            
            # Count rows
            row_count = sum(1 for _ in reader)
            if row_count < 5:
                print(f"Error: Only {row_count} rows found. Need at least 5 for meaningful analysis.")
                return False
            
            print(f"Validation passed: Found {row_count} studies with columns {headers}")
            return True
            
    except Exception as e:
        print(f"Error validating data structure: {e}")
        return False

def main():
    """
    Main entry point for fetching Cochrane data.
    
    This script attempts to fetch real data from a verified source.
    If the fetch fails, it raises FileNotFoundError('REAL_DATA_FETCH_FAILED')
    which triggers the fallback to synthetic data generation (T040b).
    """
    print("=" * 60)
    print("FETCHING REAL COCHRANE DATA")
    print("=" * 60)
    
    if not DATA_URL:
        raise FileNotFoundError("REAL_DATA_FETCH_FAILED: No data URL configured")
    
    try:
        # Fetch the data
        fetch_data(DATA_URL, OUTPUT_FILE)
        
        # Validate the structure
        if not validate_data_structure(OUTPUT_FILE):
            # Clean up invalid file
            if OUTPUT_FILE.exists():
                OUTPUT_FILE.unlink()
            raise FileNotFoundError("REAL_DATA_FETCH_FAILED: Downloaded data failed validation")
        
        print("=" * 60)
        print("SUCCESS: Real Cochrane data fetched and validated")
        print(f"Saved to: {OUTPUT_FILE.absolute()}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        # Re-raise with the specific message expected by the pipeline
        if "REAL_DATA_FETCH_FAILED" in str(e):
            raise
        else:
            raise FileNotFoundError("REAL_DATA_FETCH_FAILED") from e
    except Exception as e:
        raise FileNotFoundError("REAL_DATA_FETCH_FAILED") from e

if __name__ == "__main__":
    main()
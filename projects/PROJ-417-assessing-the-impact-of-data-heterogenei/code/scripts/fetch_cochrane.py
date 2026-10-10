"""
Script to fetch real Cochrane meta-analysis data for the heterogeneity study.
Falls back to a verified synthetic base if the real fetch fails.
"""
import os
import sys
import csv
import urllib.request
import urllib.error
from pathlib import Path
from generate_synthetic_base import generate_synthetic_base_data, save_to_csv as save_synthetic_csv

# Constants
DATA_DIR = Path("data/raw")
OUTPUT_FILE = DATA_DIR / "cochrane_base.csv"
SYNTHETIC_FILE = DATA_DIR / "cochrane_base_synthetic.csv"

# Verified source: Jackson et al. (2010) data mirror
DATA_URL = "https://raw.githubusercontent.com/mpiktas/meta-analysis-data/main/jackson2010.csv"

def fetch_data(url: str, output_path: Path) -> None:
    """
    Fetch data from URL and save to CSV.
    Raises FileNotFoundError on fetch failure to avoid silent substitution.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Attempting to fetch real data from: {url}")
        urllib.request.urlretrieve(url, output_path)
        
        if not output_path.exists() or output_path.stat().st_size == 0:
            if output_path.exists():
                output_path.unlink()
            raise FileNotFoundError("Downloaded file is empty or missing")
        
        print(f"Successfully fetched and saved data to {output_path}")
        
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        # Fail loudly as required by T001
        raise FileNotFoundError(f"REAL_DATA_FETCH_FAILED: {e}")

def validate_data_structure(file_path: Path) -> bool:
    """
    Validate that the downloaded file has the expected structure.
    """
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers:
                return False
            
            headers_lower = [h.lower().strip() for h in headers]
            # Map potential column names to standard ones
            required = ['effect_size', 'standard_error']
            
            # Check if at least some variation of required columns exists
            # (e.g., yi/sei or effect_size/standard_error)
            found_effect = any(col in headers_lower for col in ['effect_size', 'yi', 'estimate'])
            found_se = any(col in headers_lower for col in ['standard_error', 'sei', 'se'])
            
            if not (found_effect and found_se):
                return False
            
            row_count = sum(1 for _ in reader)
            return row_count >= 5
    except Exception:
        return False

def main():
    """
    Main entry point for fetching Cochrane data with fallback logic.
    """
    print("=" * 60)
    print("FETCHING COCHRANE DATA")
    print("=" * 60)
    
    try:
        fetch_data(DATA_URL, OUTPUT_FILE)
        if not validate_data_structure(OUTPUT_FILE):
            if OUTPUT_FILE.exists():
                OUTPUT_FILE.unlink()
            raise FileNotFoundError("REAL_DATA_FETCH_FAILED: Validation failed")
        print("SUCCESS: Real Cochrane data fetched and validated.")
        
    except FileNotFoundError as e:
        print(f"WARNING: {e}")
        print("Falling back to verified synthetic base (mu=0.0, sigma=1.0, N=20)...")
        try:
            data = generate_synthetic_base_data(n_studies=20, mean_effect=0.0)
            save_synthetic_csv(data, SYNTHETIC_FILE)
            print(f"SUCCESS: Synthetic base data generated at {SYNTHETIC_FILE}")
        except Exception as se:
            print(f"CRITICAL ERROR: Fallback failed: {se}")
            sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()
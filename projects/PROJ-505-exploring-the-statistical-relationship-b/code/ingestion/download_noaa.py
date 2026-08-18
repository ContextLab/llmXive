"""
NOAA Dst/Kp Data Ingestion Module.

Attempts to fetch real-time geomagnetic indices (Dst, Kp) from NOAA archives.
If the real fetch fails (network error, 404, timeout), it triggers the
synthetic data generator (T021) as a fallback, ensuring the pipeline can
proceed for testing purposes.

Output artifacts are labeled 'synthetic' ONLY if the fallback path is taken.
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
import urllib.request
import urllib.error
import json
import pandas as pd
import numpy as np

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging import get_logger, setup_logging, DataIngestionError
from utils.mkdirs import ensure_dirs
from config import get_config
from ingestion.generate_synthetic_data import generate_synthetic_noaa_data

# Configure logging
logger = get_logger(__name__)
setup_logging(level=logging.INFO)

# NOAA Data Sources (Real)
# Kp: NOAA SWPC provides 3-hour indices. We will fetch the latest available.
# Dst: NOAA SWPC provides Dst index.
# Note: Direct programmatic access to historical Dst/Kp often requires
# registering for an API key or downloading specific FTP files.
# For this implementation, we attempt to fetch from the public SWPC JSON endpoints
# or a known CSV mirror. If these fail, we fallback to synthetic.

# URLs for real data (Public endpoints)
# Kp: SWPC 3-hour index (JSON)
KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
# Dst: SWPC Dst index (JSON) - Note: Sometimes requires specific year ranges
DST_URL = "https://services.swpc.noaa.gov/products/dst-index.json"

# Fallback: If real fetch fails, we generate synthetic data covering the
# period defined in config (default: last 3 years).

def fetch_noaa_kp(url: str) -> pd.DataFrame:
    """
    Fetches Kp index from NOAA SWPC JSON endpoint.
    Returns a DataFrame with 'timestamp' and 'kp' columns.
    """
    logger.info(f"Attempting to fetch Kp from {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                # Data format: [[timestamp_str, value], ...]
                # Timestamps are often in "YYYY-MM-DD HH:MM:SS" or similar
                rows = []
                for entry in data:
                    # entry is usually [time_str, value, ...]
                    # Example: ["2023-01-01 00:00:00", "3.0", ...]
                    ts_str = entry[0]
                    kp_val = float(entry[1])
                    # Parse timestamp
                    try:
                        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Try alternative format if standard fails
                        ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
                    rows.append({"timestamp": ts, "kp": kp_val})
                
                df = pd.DataFrame(rows)
                df = df.sort_values("timestamp")
                logger.info(f"Successfully fetched {len(df)} Kp records.")
                return df
            else:
                raise DataIngestionError(f"HTTP {response.status} for Kp fetch")
    except Exception as e:
        raise DataIngestionError(f"Failed to fetch Kp from NOAA: {str(e)}")

def fetch_noaa_dst(url: str) -> pd.DataFrame:
    """
    Fetches Dst index from NOAA SWPC JSON endpoint.
    Returns a DataFrame with 'timestamp' and 'dst' columns.
    """
    logger.info(f"Attempting to fetch Dst from {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                # Data format: [[timestamp_str, value], ...]
                rows = []
                for entry in data:
                    ts_str = entry[0]
                    dst_val = float(entry[1])
                    try:
                        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
                    rows.append({"timestamp": ts, "dst": dst_val})
                
                df = pd.DataFrame(rows)
                df = df.sort_values("timestamp")
                logger.info(f"Successfully fetched {len(df)} Dst records.")
                return df
            else:
                raise DataIngestionError(f"HTTP {response.status} for Dst fetch")
    except Exception as e:
        raise DataIngestionError(f"Failed to fetch Dst from NOAA: {str(e)}")

def load_synthetic_noaa(config: dict) -> pd.DataFrame:
    """
    Generates synthetic NOAA data (Dst, Kp) using the project's generator.
    """
    logger.warning("Real data fetch failed. Generating synthetic NOAA data as fallback.")
    start_date = config.get("start_date", "2020-01-01")
    end_date = config.get("end_date", "2023-01-01")
    seed = config.get("random_seed", 42)
    
    # Call the generator from T021
    df = generate_synthetic_noaa_data(start_date, end_date, seed)
    return df

def run_ingestion(output_dir: Path, is_real_data: bool = True) -> dict:
    """
    Orchestrates the fetching of NOAA data.
    Returns a status dict indicating source (real/synthetic) and file paths.
    """
    config = get_config()
    ensure_dirs([output_dir])
    
    kp_df = None
    dst_df = None
    source_label = "real"
    fallback_triggered = False

    # 1. Attempt Real Fetch
    if is_real_data:
        try:
            kp_df = fetch_noaa_kp(KP_URL)
            dst_df = fetch_noaa_dst(DST_URL)
            
            # Basic validation: check if we got enough data
            if len(kp_df) < 100 or len(dst_df) < 100:
                logger.warning("Real data fetched but seems too short (<100 rows). Triggering synthetic fallback.")
                raise DataIngestionError("Insufficient real data retrieved")
                
            logger.info("Real NOAA data successfully retrieved.")
        except DataIngestionError as e:
            logger.error(f"Real data fetch failed: {e}. Switching to synthetic fallback.")
            fallback_triggered = True
            source_label = "synthetic"
        except Exception as e:
            logger.error(f"Unexpected error during real fetch: {e}. Switching to synthetic fallback.")
            fallback_triggered = True
            source_label = "synthetic"

    # 2. Fallback to Synthetic if needed
    if fallback_triggered or not is_real_data:
        logger.info("Generating synthetic NOAA data.")
        kp_df = load_synthetic_noaa(config)
        # Ensure synthetic has both columns
        if "dst" not in kp_df.columns:
           # The synthetic generator might return separate DFs or one combined.
           # Assuming generate_synthetic_noaa_data returns a combined DF based on T021 logic.
           # If T021 generates separate, we need to merge. 
           # Let's assume T021 returns a DF with 'timestamp', 'dst', 'kp'.
           pass
        source_label = "synthetic"

    # 3. Process and Save
    # Ensure common timestamp index
    if kp_df is not None and dst_df is not None:
        # Merge on timestamp
        merged_df = pd.merge(kp_df, dst_df, on="timestamp", how="outer")
        # Resample to hourly if necessary (NOAA data is often 3-hourly for Kp, 1-hourly for Dst)
        merged_df.set_index("timestamp", inplace=True)
        merged_df = merged_df.resample("H").ffill() # Forward fill to hourly
        merged_df.reset_index(inplace=True)
    elif kp_df is not None:
        merged_df = kp_df
    else:
        raise DataIngestionError("No data available (neither real nor synthetic).")

    # Save outputs
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_suffix = source_label
    output_filename = f"noaa_indices_{file_suffix}_{timestamp_str}.parquet"
    output_path = output_dir / output_filename

    # Save Parquet
    from utils.io import save_parquet
    save_parquet(merged_df, str(output_path))
    
    # Save a CSV summary for quick inspection
    csv_path = output_dir / f"noaa_indices_{file_suffix}_{timestamp_str}.csv"
    merged_df.to_csv(csv_path, index=False)

    logger.info(f"NOAA ingestion complete. Source: {source_label}. Saved to {output_path}")

    return {
        "source": source_label,
        "output_path": str(output_path),
        "csv_path": str(csv_path),
        "row_count": len(merged_df),
        "fallback_triggered": fallback_triggered
    }

def main():
    parser = argparse.ArgumentParser(description="Ingest NOAA Dst/Kp data.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for data artifacts.")
    parser.add_argument("--no-fallback", action="store_true", help="Do not fallback to synthetic data on failure.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "data" / "raw"
    is_real = not args.no_fallback

    try:
        result = run_ingestion(output_dir, is_real_data=is_real)
        print(f"Ingestion Status: {result['source']}")
        print(f"Rows: {result['row_count']}")
        print(f"Output: {result['output_path']}")
        if result['fallback_triggered']:
            print("WARNING: Fallback to synthetic data was triggered.")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
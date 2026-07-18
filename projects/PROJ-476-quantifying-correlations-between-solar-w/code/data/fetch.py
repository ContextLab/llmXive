"""
Data fetching module for ACE and NOAA solar wind data.

This module implements the fetching of raw data from verified NASA/NOAA sources.
It strictly adheres to the constraint of NEVER falling back to synthetic data.
"""
import os
import ftplib
import pandas as pd
from datetime import datetime
from typing import Tuple
from io import StringIO
from code import logger
from code.config import ACE_URL, NOAA_URL

def fetch_ace(start_date: str, end_date: str) -> str:
    """
    Fetch ACE Level 2 (SWEPAM/SWICS) data from NASA SPDF.

    Downloads data for the specified date range, validates columns, and saves to CSV.
    Raises an error if the fetch fails or data is invalid.

    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)

    Returns:
        str: Path to the output CSV file

    Raises:
        ConnectionError: If the FTP connection fails
        FileNotFoundError: If data for the requested range is not found
        ValueError: If required columns are missing
    """
    logger.info(f"Fetching ACE data from {ACE_URL} for range {start_date} to {end_date}")
    
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ace_raw.csv")

    try:
        # Connect to NASA SPDF FTP
        ftp = ftplib.FTP('spdf.gsfc.nasa.gov')
        ftp.login()
        
        # Navigate to ACE data directory
        base_path = "pub/data/ace/"
        ftp.cwd(base_path)
        
        # We need to find files covering the date range. 
        # ACE data is typically organized by year.
        start_year = int(start_date.split('-')[0])
        end_year = int(end_date.split('-')[0])
        
        all_data = []
        found_data = False

        for year in range(start_year, end_year + 1):
            # ACE SWEPAM Level 2 files are typically named like: 
            # 1998/1998/ace_swepam_l2_19980101_v01.cdf (but we need CSV or parseable format)
            # Since direct FTP listing of CDFs is complex without specialized libraries,
            # and the spec requires CSV output, we attempt to fetch available CSVs or 
            # use the provided URL structure if it points to a downloadable text file.
            # 
            # NOTE: NASA SPDF often provides CDF files. For this pipeline to run 
            # without external CDF libraries (like cdflib) which might not be in requirements,
            # we check if a pre-converted CSV or text file exists, or if we can 
            # retrieve a specific file.
            # 
            # However, the task requires a REAL fetch. The most robust way without 
            # heavy dependencies is to try fetching a known text-based archive 
            # if available, or fail loudly if only CDFs are present and we lack tools.
            # 
            # Given the constraint "NEVER fall back to synthetic", and the lack of 
            # cdflib in requirements, we will attempt to fetch the data using a 
            # direct HTTP/FTP link to a text representation if available, 
            # or raise a clear error if the source only offers CDFs.
            #
            # REAL SOURCE STRATEGY: The NASA CDAWeb often provides a "Browse" or "Text" 
            # view. We will try to fetch a specific file path pattern that is known 
            # to exist for ACE SWEPAM. 
            # Pattern: ftp://spdf.gsfc.nasa.gov/pub/data/ace/ascii/ace_swepam_l2_YYYY.txt
            # If these don't exist, we must fail.
            
            year_str = str(year)
            # Try to find a text file for this year
            # Common pattern for ACE ASCII data (if available)
            possible_files = [
                f"ascii/ace_swepam_l2_{year_str}.txt",
                f"ascii/ace_swepam_l2_{year_str}*.txt" # Wildcard not supported in FTP cwd directly easily
            ]
            
            # Since FTP globbing is tricky, we list the directory
            try:
                files = ftp.nlst(f"ascii/")
                # Filter for our year
                year_files = [f for f in files if year_str in f and f.endswith('.txt')]
                
                if not year_files:
                    logger.warning(f"No ASCII text files found for ACE SWEPAM year {year}. "
                                 "ACE data at SPDF is typically in CDF format. "
                                 "The pipeline requires CDF parsing capabilities or pre-converted text. "
                                 "This fetch will fail as per 'real data only' constraint if no text source exists.")
                    # We do NOT generate synthetic data. We fail.
                    raise FileNotFoundError(f"No ASCII text data found for ACE year {year} at {ACE_URL}. "
                                          "The pipeline is configured for real data only and cannot proceed without valid input.")

                for fname in year_files:
                    if year_str in fname:
                        try:
                            logger.info(f"Downloading ACE file: {fname}")
                            # Read file content
                            content = StringIO()
                            ftp.retrlines(f'RETR {fname}', content.write)
                            content.seek(0)
                            
                            df = pd.read_csv(content, delim_whitespace=True, comment='#')
                            all_data.append(df)
                            found_data = True
                        except Exception as e:
                            logger.warning(f"Could not read {fname}: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Could not list or fetch ASCII files for {year}: {e}")

        ftp.quit()

        if not found_data or not all_data:
            raise FileNotFoundError("No valid ACE data found in the specified date range. "
                                  "The pipeline requires real data and cannot proceed.")

        # Combine and save
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Parse dates if they exist as columns (ACE format varies, checking for common ones)
        # Typical ACE SWEPAM columns: SC_Time, N_p, T_p, He2+_ratio
        if 'SC_Time' in combined_df.columns:
            combined_df['timestamp'] = pd.to_datetime(combined_df['SC_Time'], errors='coerce')
            combined_df = combined_df.dropna(subset=['timestamp'])
        
        # Validate columns (SC-002)
        required_cols = ['N_p', 'T_p', 'He2+_ratio']
        for col in required_cols:
            if col not in combined_df.columns:
                raise ValueError(f"Missing required variable: {col} in fetched ACE data. "
                               f"Available columns: {list(combined_df.columns)}")

        # Filter by date range (in case we fetched whole years)
        if 'timestamp' in combined_df.columns:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            combined_df = combined_df[(combined_df['timestamp'] >= start_dt) & 
                                    (combined_df['timestamp'] <= end_dt)]

        combined_df.to_csv(output_path, index=False)
        logger.info(f"ACE data saved to {output_path} with {len(combined_df)} rows")
        return output_path

    except ftplib.all_errors as e:
        logger.error(f"FTP connection failed: {e}")
        raise ConnectionError(f"Failed to connect to NASA SPDF FTP: {e}")
    except Exception as e:
        logger.error(f"Failed to fetch ACE data: {e}")
        raise

def fetch_noaa(start_date: str, end_date: str) -> str:
    """
    Fetch NOAA Kp/Dst geomagnetic indices.

    Downloads hourly Kp/Dst data from the verified NOAA URL.
    Raises an error if the fetch fails.

    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)

    Returns:
        str: Path to the output CSV file

    Raises:
        ConnectionError: If the download fails
        FileNotFoundError: If data is not found
    """
    logger.info(f"Fetching NOAA data from {NOAA_URL} for range {start_date} to {end_date}")
    
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "noaa_raw.csv")

    # NOAA data is often available via a specific FTP or HTTP endpoint.
    # The config defines NOAA_URL. We assume it points to a text/CSV file or a directory.
    # Standard NOAA SWPC data for Kp/Dst is often in: 
    # ftp://ftp.swpc.noaa.gov/pub/lists/geomagnetic/
    # or similar.
    # We will attempt to fetch a consolidated file if the URL points to one, 
    # or construct a request for the specific range.
    
    # For robustness, we try to fetch a known file pattern from the base URL.
    # If the URL is a directory, we list it. If it's a file, we download it.
    
    try:
        # Attempt to use the URL directly if it's a file
        # If NOAA_URL is a directory, we might need to construct a specific file path.
        # Given the constraints, we assume the URL in config is the direct download link 
        # or a base that allows standard file retrieval.
        
        # Since we don't have 'requests' explicitly imported in this file (though in requirements),
        # we use urllib for standard library compliance if requests isn't forced, 
        # but 'requests' is in requirements.txt so we use it for better error handling.
        import requests
        
        # If the URL in config is a directory, we might need to guess the file.
        # Common NOAA file: 19980101-20201231_kp.txt (example)
        # We will try to fetch a generic "all" file if the URL is a directory,
        # or the URL itself if it's a file.
        
        # Check if URL ends with a file extension
        if not NOAA_URL.endswith(('.txt', '.csv', '.dat')):
            # Assume it's a base URL for geomagnetic data
            # Try to fetch a consolidated file for the range if available, 
            # or the latest available file.
            # For this implementation, we try to fetch a specific known file 
            # that covers the range if the URL is a base.
            # Example: https://www.ngdc.noaa.gov/stp/space-weather/...
            # But the task says use the URL in config.
            # Let's try to fetch the URL as is first.
            pass

        # Attempt download
        # Note: If the URL is a directory listing, this will fail with 404 or 403, 
        # which is a "fail loudly" scenario as required.
        response = requests.get(NOAA_URL, timeout=30)
        
        if response.status_code != 200:
            raise FileNotFoundError(f"NOAA data not found at {NOAA_URL} (Status: {response.status_code})")
        
        # Parse the content
        # NOAA formats vary. Often space-separated or fixed width.
        # We try to read as whitespace-separated.
        df = pd.read_csv(StringIO(response.text), delim_whitespace=True, comment='#', header=None)
        
        # If the file has no headers, we need to assign them based on NOAA standard
        # Typical columns: Year, Month, Day, Hour, Kp, Dst (if combined)
        # Or separate files. Assuming a combined format for this implementation 
        # or a format that can be parsed.
        # If the fetch returns a raw file that doesn't match, we raise an error.
        
        # Standard NOAA Kp/Dst combined file often has:
        # YYYY MM DD HH Kp Dst
        if df.shape[1] >= 6:
            df.columns = ['year', 'month', 'day', 'hour', 'Kp', 'Dst']
            df['timestamp'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
            df = df[['timestamp', 'Kp', 'Dst']]
            
            # Filter by range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]
            
            # Validate columns
            if 'Kp' not in df.columns or 'Dst' not in df.columns:
                raise ValueError("Missing required NOAA variables: Kp or Dst")
            
            df.to_csv(output_path, index=False)
            logger.info(f"NOAA data saved to {output_path} with {len(df)} rows")
            return output_path
        else:
            raise ValueError(f"Unexpected NOAA data format. Expected at least 6 columns, got {df.shape[1]}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download NOAA data: {e}")
        raise ConnectionError(f"Failed to fetch NOAA data from {NOAA_URL}: {e}")
    except Exception as e:
        logger.error(f"Failed to process NOAA data: {e}")
        raise
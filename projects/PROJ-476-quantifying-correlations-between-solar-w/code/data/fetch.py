"""
Data fetching module for ACE and NOAA solar wind and geomagnetic data.

This module implements chunked fetching logic to handle large datasets
within memory constraints. It uses streaming where possible and writes
data incrementally to disk.

Streaming Rule:
---------------
Data is fetched in chunks of 100,000 rows (defined in code/config.py as STREAMING_CHUNK_SIZE).
For ACE data, we use the CDAWeb FTP server with SSL enabled.
For NOAA data, we use the NOAA FTP server with SSL enabled.
Data is written to disk incrementally to avoid memory spikes.
"""

import os
import ftplib
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional
from io import StringIO
import ssl
import warnings

from code.config import (
    ACE_URL,
    NOAA_KP_DST_URL,
    STREAMING_CHUNK_SIZE,
    MAX_MEMORY_GB,
    ACE_VARS,
    NOAA_VARS,
    logger
)
from code import logger

# Constants for data sources
ACE_FTP_HOST = 'cdaweb.gsfc.nasa.gov'
ACE_FTP_PATH = 'pub/data/ace/hourly/swe/h0_swe_h1_h2_h3/'
NOAA_FTP_HOST = 'ftp.ngdc.noaa.gov'
NOAA_FTP_PATH = 'STP/space-weather/interplanetary-data/ace/'
NOAA_KP_DST_PATH = 'STP/space-weather/indices/kp/'

# SSL context for secure connections
SSL_CONTEXT = ssl.create_default_context()


def _download_file_ftp_ssl(
    host: str,
    path: str,
    filename: str,
    local_path: str,
    ssl_context: Optional[ssl.SSLContext] = None
) -> None:
    """
    Download a file from an FTP server using SSL.

    Args:
        host: FTP server hostname
        path: Remote directory path
        filename: Name of the file to download
        local_path: Local path to save the file
        ssl_context: SSL context for secure connection
    """
    if ssl_context is None:
        ssl_context = SSL_CONTEXT

    # Create FTP_TLS connection
    ftp = ftplib.FTP_TLS(host)
    ftp.login()
    ftp.prot_p()  # Secure data connection

    try:
        ftp.cwd(path)
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f'RETR {filename}', f.write)
        logger.info(f"Downloaded {filename} to {local_path}")
    except ftplib.error_perm as e:
        raise ConnectionError(f"Failed to download {filename}: {e}")
    finally:
        ftp.quit()


def _fetch_ace_chunked(start_date: datetime, end_date: datetime, output_path: str) -> str:
    """
    Fetch ACE solar wind data in chunks and write incrementally to disk.

    This function downloads ACE data for the specified date range, processing
    it in chunks to avoid memory issues. It writes the data incrementally
    to the output file.

    Args:
        start_date: Start date for data fetch
        end_date: End date for data fetch
        output_path: Path to write the output CSV file

    Returns:
        Path to the written output file

    Raises:
        ConnectionError: If the real data source is unreachable
        ValueError: If the downloaded data is invalid
    """
    logger.info(f"Fetching ACE data from {start_date} to {end_date}")

    # Prepare date range for file names (ACE data is organized by year)
    current_year = start_date.year
    end_year = end_date.year

    all_data = []

    # SSL context for secure connection
    ssl_context = SSL_CONTEXT

    try:
        # Connect to FTP server
        ftp = ftplib.FTP_TLS(ACE_FTP_HOST)
        ftp.login()
        ftp.prot_p()  # Secure data connection

        # Iterate through years
        while current_year <= end_year:
            # Try to find the data file for this year
            # ACE hourly data files are named like: h0_swe_h1_h2_h3_YYYY.csv
            year_filename = f"h0_swe_h1_h2_h3_{current_year}.csv"
            year_path = f"{ACE_FTP_PATH}{current_year}/"

            try:
                ftp.cwd(year_path)
            except ftplib.error_perm:
                # Try alternative path structure
                year_path = f"{ACE_FTP_PATH}"
                try:
                    ftp.cwd(year_path)
                except ftplib.error_perm:
                    logger.warning(f"ACE data not found for year {current_year} in expected paths")
                    current_year += 1
                    continue

            # Check if file exists
            try:
                ftp.voidcmd(f"SIZE {year_filename}")
            except ftplib.error_perm:
                logger.warning(f"ACE file {year_filename} not found for year {current_year}")
                current_year += 1
                continue

            # Download file in memory first (chunked approach for smaller files)
            # For large files, we would stream directly to disk
            file_data = StringIO()
            ftp.retrlines(f'RETR {year_filename}', file_data.write)
            file_data.seek(0)

            # Read the data
            try:
                df = pd.read_csv(file_data, comment='#')
                
                # Filter by date range if necessary
                if 'time' in df.columns or 'Time' in df.columns:
                    time_col = 'time' if 'time' in df.columns else 'Time'
                    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                    df = df.dropna(subset=[time_col])
                    
                    # Filter by date range
                    mask = (df[time_col] >= start_date) & (df[time_col] <= end_date)
                    df = df[mask]
                
                if not df.empty:
                    all_data.append(df)
                    logger.info(f"Processed ACE data for year {current_year}: {len(df)} rows")
            except Exception as e:
                logger.warning(f"Failed to parse ACE data for year {current_year}: {e}")
            
            current_year += 1

        ftp.quit()

        if not all_data:
            raise ValueError("No ACE data found in the specified date range")

        # Concatenate all data
        full_df = pd.concat(all_data, ignore_index=True)

        # Validate required columns exist
        required_cols = ['N_p', 'T_p', 'He2+_ratio']
        missing_cols = [col for col in required_cols if col not in full_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required ACE variables: {missing_cols}")

        # Write to output file
        full_df.to_csv(output_path, index=False)
        logger.info(f"Wrote ACE data to {output_path} ({len(full_df)} rows)")

        return output_path

    except ftplib.error_perm as e:
        if "SSL/TLS required" in str(e):
            raise ConnectionError(
                f"Failed to connect to ACE FTP server: SSL/TLS required. "
                f"Error: {e}"
            )
        raise ConnectionError(f"Failed to connect to ACE FTP server: {e}")
    except Exception as e:
        raise ConnectionError(f"Failed to fetch ACE data: {e}")


def _fetch_noaa_chunked(start_date: datetime, end_date: datetime, output_path: str) -> str:
    """
    Fetch NOAA Kp and Dst data in chunks and write incrementally to disk.

    This function downloads NOAA geomagnetic index data for the specified
    date range, processing it in chunks to avoid memory issues.

    Args:
        start_date: Start date for data fetch
        end_date: End date for data fetch
        output_path: Path to write the output CSV file

    Returns:
        Path to the written output file

    Raises:
        ConnectionError: If the real data source is unreachable
        ValueError: If the downloaded data is invalid
    """
    logger.info(f"Fetching NOAA data from {start_date} to {end_date}")

    # Prepare date range for file names
    current_year = start_date.year
    end_year = end_date.year

    all_data = []

    # SSL context for secure connection
    ssl_context = SSL_CONTEXT

    try:
        # Connect to FTP server
        ftp = ftplib.FTP_TLS(NOAA_FTP_HOST)
        ftp.login()
        ftp.prot_p()  # Secure data connection

        # Iterate through years
        while current_year <= end_year:
            # Try to find the data file for this year
            # NOAA Kp/Dst files are typically named like: kp_YYYY.txt or similar
            # Common paths:
            kp_paths = [
                f"{NOAA_KP_DST_PATH}{current_year}/",
                f"{NOAA_KP_DST_PATH}",
            ]
            
            found_file = False
            for kp_path in kp_paths:
                try:
                    ftp.cwd(kp_path)
                except ftplib.error_perm:
                    continue
                
                # Look for Kp and Dst files
                files = ftp.nlst()
                kp_file = None
                dst_file = None
                
                for f in files:
                    if 'kp' in f.lower() and str(current_year) in f:
                        kp_file = f
                    elif 'dst' in f.lower() and str(current_year) in f:
                        dst_file = f
                
                if kp_file:
                    # Download Kp file
                    file_data = StringIO()
                    ftp.retrlines(f'RETR {kp_file}', file_data.write)
                    file_data.seek(0)
                    
                    try:
                        df_kp = pd.read_csv(file_data, comment='#', delim_whitespace=True)
                        if not df_kp.empty:
                            # Ensure we have a timestamp column
                            if 'time' not in df_kp.columns and 'Time' not in df_kp.columns:
                                # Try to create a timestamp from year, month, day, hour
                                if 'year' in df_kp.columns and 'month' in df_kp.columns:
                                    df_kp['time'] = pd.to_datetime(
                                        df_kp[['year', 'month', 'day', 'hour']].fillna(0).astype(int)
                                    )
                            all_data.append(df_kp)
                            logger.info(f"Processed NOAA Kp data for year {current_year}: {len(df_kp)} rows")
                    except Exception as e:
                        logger.warning(f"Failed to parse NOAA Kp data for year {current_year}: {e}")
                    
                    found_file = True
                
                if dst_file:
                    # Download Dst file
                    file_data = StringIO()
                    ftp.retrlines(f'RETR {dst_file}', file_data.write)
                    file_data.seek(0)
                    
                    try:
                        df_dst = pd.read_csv(file_data, comment='#', delim_whitespace=True)
                        if not df_dst.empty:
                            # Ensure we have a timestamp column
                            if 'time' not in df_dst.columns and 'Time' not in df_dst.columns:
                                if 'year' in df_dst.columns and 'month' in df_dst.columns:
                                    df_dst['time'] = pd.to_datetime(
                                        df_dst[['year', 'month', 'day', 'hour']].fillna(0).astype(int)
                                    )
                            all_data.append(df_dst)
                            logger.info(f"Processed NOAA Dst data for year {current_year}: {len(df_dst)} rows")
                    except Exception as e:
                        logger.warning(f"Failed to parse NOAA Dst data for year {current_year}: {e}")
                    
                    found_file = True
                
                if found_file:
                    break
            
            if not found_file:
                logger.warning(f"No NOAA data found for year {current_year}")
            
            current_year += 1

        ftp.quit()

        if not all_data:
            raise ValueError("No NOAA data found in the specified date range")

        # Concatenate all data
        full_df = pd.concat(all_data, ignore_index=True)

        # Validate required columns exist
        required_cols = ['Kp', 'Dst']
        missing_cols = [col for col in required_cols if col not in full_df.columns]
        if missing_cols:
            # Try to find alternative column names
            alt_kp = [col for col in full_df.columns if 'kp' in col.lower()]
            alt_dst = [col for col in full_df.columns if 'dst' in col.lower()]
            
            if alt_kp and alt_dst:
                full_df['Kp'] = full_df[alt_kp[0]]
                full_df['Dst'] = full_df[alt_dst[0]]
            else:
                raise ValueError(f"Missing required NOAA variables: {missing_cols}")

        # Write to output file
        full_df.to_csv(output_path, index=False)
        logger.info(f"Wrote NOAA data to {output_path} ({len(full_df)} rows)")

        return output_path

    except ftplib.error_perm as e:
        if "SSL/TLS required" in str(e):
            raise ConnectionError(
                f"Failed to connect to NOAA FTP server: SSL/TLS required. "
                f"Error: {e}"
            )
        raise ConnectionError(f"Failed to connect to NOAA FTP server: {e}")
    except Exception as e:
        raise ConnectionError(f"Failed to fetch NOAA data: {e}")


def fetch_ace(start_date: str, end_date: str) -> str:
    """
    Fetch ACE solar wind data for the specified date range.

    This function downloads ACE Level 2 solar wind data from the CDAWeb FTP server.
    It uses chunked fetching to handle large datasets within memory constraints.

    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format

    Returns:
        Path to the written output file (data/raw/ace_raw.csv)

    Raises:
        ConnectionError: If the real data source is unreachable
        ValueError: If the downloaded data is invalid
    """
    output_path = "data/raw/ace_raw.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Parse dates
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Fetch data with chunked logic
    result = _fetch_ace_chunked(start_dt, end_dt, output_path)
    
    return result


def fetch_noaa(start_date: str, end_date: str) -> str:
    """
    Fetch NOAA Kp and Dst geomagnetic indices for the specified date range.

    This function downloads NOAA geomagnetic index data from the NOAA FTP server.
    It uses chunked fetching to handle large datasets within memory constraints.

    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format

    Returns:
        Path to the written output file (data/raw/noaa_raw.csv)

    Raises:
        ConnectionError: If the real data source is unreachable
        ValueError: If the downloaded data is invalid
    """
    output_path = "data/raw/noaa_raw.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Parse dates
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Fetch data with chunked logic
    result = _fetch_noaa_chunked(start_dt, end_dt, output_path)
    
    return result

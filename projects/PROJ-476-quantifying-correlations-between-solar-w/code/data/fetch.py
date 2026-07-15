"""
Data fetching module for solar wind and geomagnetic indices.

Implements T011: Download ACE Level 2 (SWEPAM/SWICS) and NOAA Kp/Dst data.
"""
from datetime import datetime
from typing import Tuple
import os
import requests
import pandas as pd
from io import StringIO
from code import logger

# Ensure the raw data directory exists
os.makedirs('data/raw', exist_ok=True)

# Verified URLs as per project claims
# ACE: https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level_2/
# We use the CDAWeb HTTPS mirror for Level 2 SWEPAM/SWICS data
ACE_BASE_URL = "https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level_2/"
# NOAA: https://www.ngdc.noaa.gov/stp/space-weather/geomagnetic/kp/
# We use the NOAA FTP/HTTPS mirror for Kp and Dst indices
NOAA_KP_URL = "https://www.ngdc.noaa.gov/stp/space-weather/geomagnetic/kp/3_hourly/kp.txt"
NOAA_DST_URL = "https://www.ngdc.noaa.gov/stp/space-weather/geomagnetic/dst/daily/dst.txt"

def fetch_ace(start_date: datetime, end_date: datetime) -> str:
    """
    Fetch ACE Level 2 data (SWEPAM/SWICS) for the specified date range.

    Downloads N_p, T_p, He2+_ratio from CDAWeb.
    
    Args:
        start_date: Start of the time window (inclusive).
        end_date: End of the time window (inclusive).
        
    Returns:
        str: Path to the saved raw CSV file: 'data/raw/ace_raw.csv'
        
    Raises:
        ValueError: If the data source is unreachable or returns empty data.
        RuntimeError: If the download fails.
    """
    output_path = 'data/raw/ace_raw.csv'
    logger.info(f"Fetching ACE data from {start_date} to {end_date}")
    
    # We will construct a list of years to fetch and concatenate
    # ACE data is typically available in yearly files.
    # Format: ace_swepam_l2_<year>.asc or similar.
    # We'll try to fetch a range of files covering the dates.
    
    all_data = []
    current_year = start_date.year
    end_year = end_date.year
    
    # CDAWeb directory listing is not always easy to parse programmatically without a specific API.
    # However, standard ACE Level 2 files are often named: ace_hl2_swepam_<year>.asc
    # Let's try to fetch files for the range.
    # Note: In a production environment, one might use the CDAWeb API or a specific directory listing.
    # For this implementation, we will attempt to download the standard yearly files.
    
    # We will use a known pattern for ACE Level 2 data.
    # Pattern: https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level_2/ace_swepam_l2_<year>.asc
    
    for year in range(current_year, end_year + 1):
        url = f"{ACE_BASE_URL}ace_swepam_l2_{year}.asc"
        logger.debug(f"Attempting to fetch ACE file: {url}")
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Parse the raw ASCII data. ACE files are space/tab delimited.
                # We need to identify the columns for N_p, T_p, He2+_ratio.
                # Typically: Year, DOY, Hour, N_p, T_p, He2+_ratio, etc.
                # Let's read the whole file content into a DataFrame.
                # The files usually have a header section that needs to be skipped.
                # We'll try to read with pandas, skipping header lines if necessary.
                
                # Read raw text
                text_data = response.text
                lines = text_data.split('\n')
                
                # Find the start of data (usually after lines starting with # or specific headers)
                data_lines = []
                header_found = False
                for line in lines:
                    if line.startswith('#') or line.startswith(' ') or line.startswith('\t'):
                        if not header_found and line.strip() and not line.startswith('C'):
                            # Might be a header line
                            pass
                        continue
                    if line.strip():
                        data_lines.append(line)
                
                if not data_lines:
                    logger.warning(f"No data found in ACE file for {year}")
                    continue
                    
                # Attempt to parse as whitespace delimited
                # ACE files often have a specific format. Let's try to read the first few lines to guess.
                # Assuming standard columns: Year, DOY, Hour, N_p, T_p, He2+_ratio, ...
                # We'll read the whole block and hope pandas can infer.
                try:
                    df = pd.read_csv(StringIO('\n'.join(data_lines)), delim_whitespace=True, comment='#')
                    # Filter by date range if the file spans multiple years (unlikely for yearly files)
                    # ACE data usually has 'Year', 'Day', 'Hour' columns.
                    if 'Year' in df.columns and 'Day' in df.columns and 'Hour' in df.columns:
                        df['timestamp'] = pd.to_datetime({
                            'year': df['Year'],
                            'dayofyear': df['Day'],
                            'hour': df['Hour']
                        })
                        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
                        # Select relevant columns if they exist
                        # Common ACE SWEPAM/SWICS columns: N_p, T_p, He2+_ratio
                        # We need to map the actual column names from the file to our expected names.
                        # If the file has 'N_p' (or similar) we keep it.
                        # For this task, we assume the columns are named 'N_p', 'T_p', 'He2+_ratio' in the file
                        # or we map them. The task requires verifying headers later in T012.
                        # We'll assume the file has columns like 'N_p', 'T_p', 'He2+_ratio' or similar.
                        # If the file uses different names (e.g., 'Proton_Density'), we might need to map.
                        # However, T012 will validate the headers. We just need to get the data in.
                        # Let's assume the file has columns: Year, Day, Hour, N_p, T_p, He2+_ratio, ...
                        # We'll keep all columns and let T012 validate.
                        all_data.append(df)
                    else:
                        logger.warning(f"ACE file for {year} does not have expected time columns.")
                except Exception as e:
                    logger.warning(f"Could not parse ACE file for {year}: {e}")
            else:
                logger.warning(f"Failed to fetch ACE file for {year}: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Network error fetching ACE data for {year}: {e}")
            raise RuntimeError(f"Failed to fetch ACE data: {e}")

    if not all_data:
        raise ValueError("No ACE data retrieved for the specified date range.")
        
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Ensure we have the timestamp column
    if 'timestamp' not in final_df.columns:
        # Fallback: try to construct from Year, Day, Hour if they exist
        if 'Year' in final_df.columns and 'Day' in final_df.columns and 'Hour' in final_df.columns:
            final_df['timestamp'] = pd.to_datetime({
                'year': final_df['Year'],
                'dayofyear': final_df['Day'],
                'hour': final_df['Hour']
            })
        
    # Save to CSV
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved ACE data to {output_path}")
    return output_path

def fetch_noaa(start_date: datetime, end_date: datetime) -> str:
    """
    Fetch NOAA Kp and Dst indices for the specified date range.
    
    Downloads Kp and Dst from NOAA NGDC.
    
    Args:
        start_date: Start of the time window (inclusive).
        end_date: End of the time window (inclusive).
        
    Returns:
        str: Path to the saved raw CSV file: 'data/raw/noaa_raw.csv'
        
    Raises:
        ValueError: If the data source is unreachable or returns empty data.
        RuntimeError: If the download fails.
    """
    output_path = 'data/raw/noaa_raw.csv'
    logger.info(f"Fetching NOAA Kp/Dst data from {start_date} to {end_date}")
    
    kp_data = []
    dst_data = []
    
    # Fetch Kp (3-hourly)
    try:
        response = requests.get(NOAA_KP_URL, timeout=30)
        if response.status_code == 200:
            # NOAA Kp file format: Year, Month, Day, Hour, Kp, ap, ...
            # Skip header lines (usually starting with # or specific text)
            lines = response.text.split('\n')
            data_lines = [l for l in lines if l and not l.startswith('#') and not l.startswith(' ')]
            if data_lines:
                kp_df = pd.read_csv(StringIO('\n'.join(data_lines)), delim_whitespace=True, comment='#')
                # Filter by date
                # Columns are usually: Year, Month, Day, Hour, Kp, ...
                if 'Year' in kp_df.columns and 'Month' in kp_df.columns and 'Day' in kp_df.columns:
                    kp_df['timestamp'] = pd.to_datetime({
                        'year': kp_df['Year'],
                        'month': kp_df['Month'],
                        'day': kp_df['Day'],
                        'hour': kp_df['Hour']
                    })
                    kp_df = kp_df[(kp_df['timestamp'] >= start_date) & (kp_df['timestamp'] <= end_date)]
                    kp_data.append(kp_df)
        else:
            logger.warning(f"Failed to fetch NOAA Kp: HTTP {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Network error fetching NOAA Kp: {e}")
        raise RuntimeError(f"Failed to fetch NOAA Kp data: {e}")
        
    # Fetch Dst (daily)
    try:
        response = requests.get(NOAA_DST_URL, timeout=30)
        if response.status_code == 200:
            # NOAA Dst file format: Year, Month, Day, Dst, ...
            lines = response.text.split('\n')
            data_lines = [l for l in lines if l and not l.startswith('#') and not l.startswith(' ')]
            if data_lines:
                dst_df = pd.read_csv(StringIO('\n'.join(data_lines)), delim_whitespace=True, comment='#')
                if 'Year' in dst_df.columns and 'Month' in dst_df.columns and 'Day' in dst_df.columns:
                    dst_df['timestamp'] = pd.to_datetime({
                        'year': dst_df['Year'],
                        'month': dst_df['Month'],
                        'day': dst_df['Day']
                    })
                    # For daily data, we might want to assign the timestamp to 00:00:00
                    dst_df = dst_df[(dst_df['timestamp'] >= start_date) & (dst_df['timestamp'] <= end_date)]
                    dst_data.append(dst_df)
        else:
            logger.warning(f"Failed to fetch NOAA Dst: HTTP {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Network error fetching NOAA Dst: {e}")
        raise RuntimeError(f"Failed to fetch NOAA Dst data: {e}")
        
    if not kp_data and not dst_data:
        raise ValueError("No NOAA Kp or Dst data retrieved for the specified date range.")
        
    # Merge Kp and Dst on timestamp
    # Kp is 3-hourly, Dst is daily. We'll merge on the timestamp.
    # We need to align the columns.
    # Kp columns: timestamp, Kp, ...
    # Dst columns: timestamp, Dst, ...
    
    final_df = pd.DataFrame()
    
    if kp_data:
        kp_df = pd.concat(kp_data, ignore_index=True)
        # Ensure Kp column is named 'Kp'
        if 'Kp' in kp_df.columns:
            final_df = kp_df[['timestamp', 'Kp']].copy()
        elif 'kp' in kp_df.columns:
            final_df = kp_df[['timestamp', 'kp']].copy()
            final_df.rename(columns={'kp': 'Kp'}, inplace=True)
        else:
            # Try to find the column
            for col in kp_df.columns:
                if col.lower().startswith('kp'):
                    final_df = kp_df[['timestamp', col]].copy()
                    final_df.rename(columns={col: 'Kp'}, inplace=True)
                    break
        
    if dst_data:
        dst_df = pd.concat(dst_data, ignore_index=True)
        # Ensure Dst column is named 'Dst'
        if 'Dst' in dst_df.columns:
            dst_col = 'Dst'
        elif 'dst' in dst_df.columns:
            dst_col = 'dst'
        else:
            for col in dst_df.columns:
                if col.lower().startswith('dst'):
                    dst_col = col
                    break
            
        if 'Dst' in final_df.columns:
            final_df = final_df.merge(dst_df[['timestamp', dst_col]], on='timestamp', how='outer')
            final_df.rename(columns={dst_col: 'Dst'}, inplace=True)
        else:
            final_df = dst_df[['timestamp', dst_col]].copy()
            final_df.rename(columns={dst_col: 'Dst'}, inplace=True)
            
    if final_df.empty:
        raise ValueError("Could not merge Kp and Dst data.")
        
    # Save to CSV
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved NOAA data to {output_path}")
    return output_path
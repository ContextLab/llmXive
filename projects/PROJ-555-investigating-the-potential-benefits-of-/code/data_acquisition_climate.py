"""
Module to fetch CHIRPS precipitation and NASA POWER temperature data.

This module implements FR-003 by fetching multi-decadal climate data
for the early 21st century (2000-2023) and aggregating it to monthly
resolution.

Data Sources:
- CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data):
  Accessed via the `chirps` Python package (wraps Google Earth Engine).
- NASA POWER: Accessed via the `power` Python package (wraps NASA API).

Output:
- data/processed/climate_covariates.parquet
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
from tqdm import tqdm

# Local imports
from config import ensure_directories
from utils.chunking import process_chunked

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from code.config import ensure_directories
    from code.utils.chunking import process_chunked

try:
    import chirps
    CHIRPS_AVAILABLE = True
except ImportError:
    CHIRPS_AVAILABLE = False
    print("WARNING: chirps package not installed. CHIRPS data will be skipped.")

try:
    import power
    POWER_AVAILABLE = True
except ImportError:
    POWER_AVAILABLE = False
    print("WARNING: power package not installed. NASA POWER data will be skipped.")

# Constants
START_YEAR = 2000
END_YEAR = 2023
CHUNK_SIZE_MONTHS = 12  # Process data in 1-year chunks to manage memory

def load_site_coordinates() -> gpd.GeoDataFrame:
    """
    Load site coordinates from the generated CSV.
    Expects: data/raw/site_coordinates.csv
    """
    path = Path("data/raw/site_coordinates.csv")
    if not path.exists():
        raise FileNotFoundError(
            f"Site coordinates file not found at {path}. "
            "Please run T012b first to generate site coordinates."
        )
    
    df = pd.read_csv(path)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['longitude'], df['latitude']),
        crs="EPSG:4326"
    )
    return gdf

def fetch_chirps_precipitation(
    gdf: gpd.GeoDataFrame,
    start_year: int = START_YEAR,
    end_year: int = END_YEAR
) -> Optional[pd.DataFrame]:
    """
    Fetch CHIRPS precipitation data for given sites.
    
    Args:
        gdf: GeoDataFrame with site locations
        start_year: Start year for data retrieval
        end_year: End year for data retrieval
        
    Returns:
        DataFrame with columns: site_id, date, precip_mm
    """
    if not CHIRPS_AVAILABLE:
        print("Skipping CHIRPS fetch: package not available.")
        return None
        
    print(f"Fetching CHIRPS precipitation data for {start_year}-{end_year}...")
    
    # Prepare data structures
    all_data = []
    
    # Process sites in chunks to avoid memory issues
    sites = gdf.to_dict('records')
    
    for site in tqdm(sites, desc="Fetching CHIRPS sites"):
        site_id = site.get('site_id', f"site_{site['latitude']}_{site['longitude']}")
        lat = site['latitude']
        lon = site['longitude']
        
        # Fetch data for the full range in one go if possible, 
        # or chunk it if the API limits requests
        try:
            # CHIRPS point data retrieval
            # Using the API directly via the package
            ds = chirps.get_point(lon, lat, f"{start_year}-01-01", f"{end_year}-12-31")
            
            # Convert to DataFrame
            df_site = ds.to_dataframe().reset_index()
            df_site.columns = ['date', 'precip_mm']
            df_site['site_id'] = site_id
            
            # Resample to monthly (sum for precipitation)
            df_site['date'] = pd.to_datetime(df_site['date'])
            df_monthly = df_site.set_index('date').resample('M')['precip_mm'].sum().reset_index()
            df_monthly['site_id'] = site_id
            
            all_data.append(df_monthly)
            
        except Exception as e:
            print(f"Error fetching CHIRPS for site {site_id}: {e}")
            continue
    
    if not all_data:
        return None
        
    return pd.concat(all_data, ignore_index=True)

def fetch_nasa_power_temperature(
    gdf: gpd.GeoDataFrame,
    start_year: int = START_YEAR,
    end_year: int = END_YEAR
) -> Optional[pd.DataFrame]:
    """
    Fetch NASA POWER temperature data for given sites.
    
    Args:
        gdf: GeoDataFrame with site locations
        start_year: Start year for data retrieval
        end_year: End year for data retrieval
        
    Returns:
        DataFrame with columns: site_id, date, temp_avg_c, temp_min_c, temp_max_c
    """
    if not POWER_AVAILABLE:
        print("Skipping NASA POWER fetch: package not available.")
        return None
        
    print(f"Fetching NASA POWER temperature data for {start_year}-{end_year}...")
    
    all_data = []
    sites = gdf.to_dict('records')
    
    # NASA POWER parameters
    parameters = ['T2M_MAX', 'T2M_MIN', 'T2M_AVG']
    
    for site in tqdm(sites, desc="Fetching NASA POWER sites"):
        site_id = site.get('site_id', f"site_{site['latitude']}_{site['longitude']}")
        lat = site['latitude']
        lon = site['longitude']
        
        try:
            # Fetch data for the full range
            # NASA POWER API returns daily data
            ds = power.get_point_data(
                lat=lat, 
                lon=lon, 
                start_date=f"{start_year}-01-01", 
                end_date=f"{end_year}-12-31",
                parameters=parameters,
                temporal_api='daily'
            )
            
            # Convert to DataFrame
            df_site = ds.to_dataframe().reset_index()
            # Rename columns to match expected format
            df_site = df_site.rename(columns={
                'T2M_MAX': 'temp_max_c',
                'T2M_MIN': 'temp_min_c',
                'T2M_AVG': 'temp_avg_c'
            })
            df_site['site_id'] = site_id
            
            # Resample to monthly (mean for temperature)
            df_site['date'] = pd.to_datetime(df_site['date'])
            df_site = df_site.set_index('date')
            
            df_monthly = df_site.resample('M').mean().reset_index()
            df_monthly['site_id'] = site_id
            
            all_data.append(df_monthly)
            
        except Exception as e:
            print(f"Error fetching NASA POWER for site {site_id}: {e}")
            continue
    
    if not all_data:
        return None
        
    return pd.concat(all_data, ignore_index=True)

def merge_climate_data(
    precip_df: Optional[pd.DataFrame],
    temp_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    Merge precipitation and temperature data into a single DataFrame.
    
    Args:
        precip_df: Monthly precipitation data
        temp_df: Monthly temperature data
        
    Returns:
        Merged DataFrame with all climate covariates
    """
    if precip_df is None and temp_df is None:
        raise ValueError("Both precipitation and temperature data are None.")
    
    if precip_df is None:
        return temp_df
    if temp_df is None:
        return precip_df
        
    # Ensure date columns are datetime
    precip_df['date'] = pd.to_datetime(precip_df['date'])
    temp_df['date'] = pd.to_datetime(temp_df['date'])
    
    # Merge on site_id and date
    merged = pd.merge(
        precip_df,
        temp_df,
        on=['site_id', 'date'],
        how='outer'
    )
    
    return merged

def main():
    """
    Main function to fetch and process climate covariates.
    """
    print("Starting climate covariates data acquisition (T009)...")
    
    # Ensure output directory exists
    ensure_directories()
    
    # Load site coordinates
    print("Loading site coordinates...")
    gdf = load_site_coordinates()
    print(f"Loaded {len(gdf)} sites.")
    
    # Fetch data
    precip_df = fetch_chirps_precipitation(gdf)
    temp_df = fetch_nasa_power_temperature(gdf)
    
    # Merge data
    print("Merging climate data...")
    climate_df = merge_climate_data(precip_df, temp_df)
    
    if climate_df is None or climate_df.empty:
        print("ERROR: No climate data was retrieved. Check API availability and site coordinates.")
        sys.exit(1)
    
    # Sort and clean
    climate_df = climate_df.sort_values(['site_id', 'date']).reset_index(drop=True)
    
    # Handle missing values
    print(f"Data shape before dropping NaN: {climate_df.shape}")
    climate_df = climate_df.dropna()
    print(f"Data shape after dropping NaN: {climate_df.shape}")
    
    # Save to Parquet
    output_path = Path("data/processed/climate_covariates.parquet")
    print(f"Saving climate covariates to {output_path}...")
    climate_df.to_parquet(output_path, index=False)
    
    print(f"Successfully saved {len(climate_df)} records to {output_path}")
    print("Climate covariates data acquisition complete.")

if __name__ == "__main__":
    main()

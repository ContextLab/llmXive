"""
Data Ingestion Module for Energy Systems Project.

This module provides functions to fetch raw data from official sources:
- EIA Residential Energy Consumption Survey (RECS)
- US Census Bureau American Community Survey (ACS)

All functions are designed to fail loudly if the real data source is unreachable
or if required columns are missing, in accordance with the project's data integrity
and reproducibility principles.
"""

import pandas as pd
import requests
from typing import Optional
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Required columns for EIA RECS data as per specification
EIA_REQUIRED_COLUMNS = {
    'income',
    'energy_cost',
    'solar_installation',
    'location',
    'household_id',
    'census_tract'
}

# Required columns for ACS data
ACS_REQUIRED_COLUMNS = {
    'tract_id',
    'median_income',
    'population',
    'housing_units'
}


def fetch_eia_rec(url: str) -> pd.DataFrame:
    """
    Fetch EIA Residential Energy Consumption Survey (RECS) data from the specified URL.

    This function retrieves the real EIA RECS dataset. It strictly enforces that
    the data comes from the provided URL and does not fall back to synthetic data.
    If the fetch fails or required columns are missing, it raises an exception.

    Args:
        url (str): The official URL to the EIA RECS dataset (e.g., CSV or Parquet file).

    Returns:
        pd.DataFrame: A DataFrame containing the EIA RECS data.

    Raises:
        RuntimeError: If the URL is unreachable, the download fails, or required
                      columns are missing from the dataset.
        ValueError: If the URL format is invalid or the file cannot be parsed.
    """
    logger.info(f"Fetching EIA RECS data from {url}")

    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL format: {url}. Must start with http:// or https://")

    try:
        # Attempt to fetch the data
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Determine file type based on extension or content
        if url.endswith('.csv'):
            df = pd.read_csv(pd.io.common.BytesIO(response.content))
        elif url.endswith('.parquet') or url.endswith('.pq'):
            # Requires pyarrow, which is in requirements
            df = pd.read_parquet(pd.io.common.BytesIO(response.content))
        else:
            # Try CSV as default, fallback to JSON if applicable
            try:
                df = pd.read_csv(pd.io.common.BytesIO(response.content))
            except Exception:
                try:
                    df = pd.read_json(pd.io.common.BytesIO(response.content))
                except Exception as e:
                    raise RuntimeError(f"Could not parse response as CSV or JSON: {e}")

        logger.info(f"Successfully fetched {len(df)} rows from EIA RECS")

        # Validate required columns
        missing_cols = EIA_REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise RuntimeError(
                f"Missing required columns in EIA RECS data: {missing_cols}. "
                f"Available columns: {list(df.columns)}"
            )

        return df

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch EIA RECS data from {url}: {e}")
    except Exception as e:
        raise RuntimeError(f"Error processing EIA RECS data: {e}")


def fetch_acs(tract_id: str) -> pd.DataFrame:
    """
    Fetch American Community Survey (ACS) data for a specific census tract.

    This function retrieves ACS data for the given census tract ID. It uses the
    Census API (or a direct data source if available) to fetch real demographic
    and economic data. It strictly enforces that the data comes from a real source.

    Args:
        tract_id (str): The census tract ID (e.g., '06037101100' for a tract in LA County).

    Returns:
        pd.DataFrame: A DataFrame containing ACS data for the specified tract.

    Raises:
        RuntimeError: If the API request fails, the tract ID is invalid, or required
                      columns are missing.
        ValueError: If the tract_id format is invalid.
    """
    logger.info(f"Fetching ACS data for tract {tract_id}")

    if not tract_id or len(tract_id) < 11:
        raise ValueError(f"Invalid tract_id format: {tract_id}. Expected a valid census tract ID (11 digits).")

    # Note: In a real implementation, this would use the censusdata library or Census API.
    # Since the project uses `censusdata` as mentioned in T015, we will simulate the call
    # to the real API structure. However, per the "fail loudly" constraint, we must
    # attempt a real fetch. Since we cannot include an API key in this static artifact,
    # we will attempt to use a public endpoint if available, or raise a clear error
    # if credentials are missing (which is the correct behavior for a real system).

    # For the purpose of this implementation, we assume the presence of the `censusdata`
    # library as specified in T015. If the library is not installed, this will fail loudly.
    try:
        import censusdata
    except ImportError:
        raise RuntimeError(
            "The 'censusdata' library is required to fetch ACS data. "
            "Please install it: pip install censusdata"
        )

    try:
        # Define the ACS year (e.g., 2021) and variables
        # 06 = California (example), but we need to handle state/county from tract_id
        # A real implementation would parse the tract_id to get state/county
        # For now, we assume the tract_id includes state/county info or we fetch all.
        # Since we can't fetch a single tract without state/county, we will attempt
        # to fetch the tract using the library's API.

        # Note: The censusdata library requires an API key for most queries.
        # If no key is set in the environment, it will fail. This is the desired behavior
        # to ensure real data is used.
        acs = censusdata.censusdata('acs5', 2021)

        # We need to specify the state and county. Since tract_id is 11 digits:
        # Digits 1-2: State FIPS
        # Digits 3-5: County FIPS
        # Digits 6-10: Tract
        if len(tract_id) < 11:
            raise ValueError(f"Tract ID too short: {tract_id}")

        state_fips = tract_id[:2]
        county_fips = tract_id[2:5]
        tract_fips = tract_id[5:11]

        # Fetch variables: B19013 (Median Income), B01001 (Population), B25001 (Housing Units)
        # Note: These are standard ACS variable codes.
        variables = ['B19013_001E', 'B01001_001E', 'B25001_001E']

        df = acs.download(
            variables=variables,
            state=state_fips,
            county=county_fips,
            tract=tract_fips
        )

        # Rename columns to match our schema
        df = df.reset_index()
        df = df.rename(columns={
            'B19013_001E': 'median_income',
            'B01001_001E': 'population',
            'B25001_001E': 'housing_units',
            'tract': 'tract_id'
        })

        # Ensure tract_id is in the DataFrame
        if 'tract_id' not in df.columns:
            df['tract_id'] = tract_id

        logger.info(f"Successfully fetched ACS data for tract {tract_id}")

        # Validate required columns
        missing_cols = ACS_REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise RuntimeError(
                f"Missing required columns in ACS data: {missing_cols}. "
                f"Available columns: {list(df.columns)}"
            )

        return df

    except Exception as e:
        raise RuntimeError(
            f"Failed to fetch ACS data for tract {tract_id}. "
            f"This may be due to missing API key, invalid tract ID, or network issues. "
            f"Error: {e}"
        )
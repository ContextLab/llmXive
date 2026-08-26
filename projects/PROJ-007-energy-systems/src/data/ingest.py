"""
Data Ingestion Module for Energy Systems Project.

This module provides functions to fetch raw data from the EIA Residential
Energy Consumption Survey (RECS) and the American Community Survey (ACS).
"""

import pandas as pd
from typing import Optional


def fetch_eia_rec(url: str) -> pd.DataFrame:
    """
    Fetch EIA Residential Energy Consumption Survey (RECS) data from a given URL.

    This function is a stub implementation for Task T008. It raises
    NotImplementedError to indicate that the actual fetching logic using
    pandas or a specific EIA API client has not yet been implemented.
    In the full implementation (Task T015), this will download the CSV/Excel
    file from the official EIA RECS URL, parse it, and return a DataFrame.

    Args:
        url (str): The direct URL to the EIA RECS dataset file.

    Returns:
        pd.DataFrame: A DataFrame containing the raw EIA RECS data.

    Raises:
        NotImplementedError: This is a stub implementation.
    """
    raise NotImplementedError(
        "fetch_eia_rec is not yet implemented. "
        "This stub is for Task T008. "
        "Implement the actual download and parsing logic in Task T015."
    )


def fetch_acs(tract_id: str) -> pd.DataFrame:
    """
    Fetch American Community Survey (ACS) data for a specific census tract.

    This function is a stub implementation for Task T008. It raises
    NotImplementedError to indicate that the actual fetching logic using
    the `censusdata` library has not yet been implemented.
    In the full implementation (Task T015), this will query the Census API
    for the specified tract_id and return a DataFrame with socioeconomic
    variables (e.g., median income, population).

    Args:
        tract_id (str): The FIPS code for the census tract (e.g., '06037101100').

    Returns:
        pd.DataFrame: A DataFrame containing the raw ACS data for the tract.

    Raises:
        NotImplementedError: This is a stub implementation.
    """
    raise NotImplementedError(
        "fetch_acs is not yet implemented. "
        "This stub is for Task T008. "
        "Implement the actual Census API query logic in Task T015."
    )
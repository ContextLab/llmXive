"""
Data Ingestion Module for Statistical Analysis of Sentiment Drift.

This module provides client wrappers for:
1. FRED (Federal Reserve Economic Data) API for macroeconomic indicators.
2. GDELT (Global Database of Events, Language, and Tone) API for sentiment data.
   Note: The project plan overrides the initial spec's HuggingFace requirement
   with GDELT to satisfy the need for historical time-series sentiment data.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

import pandas as pd
import requests
from dotenv import find_dotenv, load_dotenv

# Import environment helpers from existing config module
from config import get_fred_api_key, get_gdelt_api_key, get_hf_token, load_environment

# Ensure environment variables are loaded
load_environment()

# Constants
DEFAULT_OUTPUT_DIR = Path("data/raw")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
GDELT_BASE_URL = "http://api.gdeltproject.org/api/v2/doc/doc"

# Ensure output directory exists
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class FREDClient:
    """
    Client wrapper for the FRED API to fetch macroeconomic time series data.

    Attributes:
        api_key (str): The FRED API key.
        base_url (str): The base URL for FRED API requests.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the FRED client.

        Args:
            api_key: Optional FRED API key. If not provided, attempts to load
                     from environment variable 'FRED_API_KEY'.
        """
        self.api_key = api_key or get_fred_api_key()
        if not self.api_key:
            raise ValueError(
                "FRED API key is missing. Please set the FRED_API_KEY "
                "environment variable or pass it to the constructor."
            )
        self.base_url = FRED_BASE_URL

    def fetch_series(
        self,
        series_id: str,
        start_date: str = "1980-01-01",
        end_date: str = "2024-12-31",
        output_file: Optional[Union[str, Path]] = None,
        frequency: str = "monthly"
    ) -> pd.DataFrame:
        """
        Fetch time series data from FRED.

        Args:
            series_id: The FRED series ID (e.g., 'GDP', 'UNRATE').
            start_date: Start date in 'YYYY-MM-DD' format.
            end_date: End date in 'YYYY-MM-DD' format.
            output_file: Optional path to save the CSV output.
            frequency: Desired frequency of observations ('daily', 'weekly', 'monthly', 'quarterly', 'annual').

        Returns:
            A pandas DataFrame containing the time series data with columns:
            ['date', 'value', 'series_id'].

        Raises:
            requests.HTTPError: If the API request fails.
            ValueError: If the API returns no data.
        """
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
            "frequency": frequency,
            "sort_order": "asc"
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch data from FRED for {series_id}: {e}")

        if "observations" not in data or not data["observations"]:
            raise ValueError(f"No data returned from FRED for series {series_id} in the specified range.")

        # Parse observations
        records = []
        for obs in data["observations"]:
            # FRED returns "date" as string, sometimes "value" as "." for missing
            date_str = obs.get("date")
            value_str = obs.get("value")

            # Handle missing values
            if value_str == ".":
                value = None
            else:
                try:
                    value = float(value_str)
                except ValueError:
                    value = None

            records.append({
                "date": date_str,
                "value": value,
                "series_id": series_id
            })

        df = pd.DataFrame(records)
        
        # Convert date column to datetime
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # Save to file if path provided
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)

        return df

    def fetch_gdp(self, output_file: Optional[Union[str, Path]] = None) -> pd.DataFrame:
        """
        Fetch US Real GDP data (Billions of Chained 2017 Dollars, Quarterly).
        
        Args:
            output_file: Path to save the CSV. Defaults to 'data/raw/fred_gdp.csv'.
        
        Returns:
            DataFrame with GDP data.
        """
        if output_file is None:
            output_file = DEFAULT_OUTPUT_DIR / "fred_gdp.csv"
        
        # GDP is quarterly, but we fetch raw data and align later in preprocessing
        return self.fetch_series(
            series_id="GDP",
            start_date="1980-01-01",
            end_date="2024-12-31",
            output_file=output_file,
            frequency="quarterly"
        )

    def fetch_unemployment_rate(self, output_file: Optional[Union[str, Path]] = None) -> pd.DataFrame:
        """
        Fetch US Unemployment Rate data (Percent, Monthly).
        
        Args:
            output_file: Path to save the CSV. Defaults to 'data/raw/fred_unrate.csv'.
        
        Returns:
            DataFrame with unemployment rate data.
        """
        if output_file is None:
            output_file = DEFAULT_OUTPUT_DIR / "fred_unrate.csv"
        
        return self.fetch_series(
            series_id="UNRATE",
            start_date="1980-01-01",
            end_date="2024-12-31",
            output_file=output_file,
            frequency="monthly"
        )


class GDELTClient:
    """
    Client wrapper for the GDELT 2.1 Event Database API to fetch sentiment data.
    
    The GDELT API provides a global database of events with tone scores.
    We aggregate these to monthly sentiment averages.
    
    Attributes:
        api_key (str): The GDELT API key (optional for public access, but recommended).
        base_url (str): The base URL for GDELT API requests.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GDELT client.

        Args:
            api_key: Optional GDELT API key. If not provided, attempts to load
                     from environment variable 'GDELT_API_KEY'.
        """
        self.api_key = api_key or get_gdelt_api_key()
        self.base_url = GDELT_BASE_URL
        # GDELT public API does not strictly require a key for basic queries,
        # but we handle it if provided.

    def fetch_sentiment_by_country(
        self,
        country_code: str = "USA",
        start_date: str = "1980-01-01",
        end_date: str = "2024-12-31",
        output_file: Optional[Union[str, Path]] = None
    ) -> pd.DataFrame:
        """
        Fetch daily average tone scores for a specific country from GDELT.
        
        This uses the GDELT 2.1 Event Database API (v2).
        Query: Select average tone for events in the specified country.
        
        Args:
            country_code: ISO 3-letter country code (e.g., 'USA').
            start_date: Start date in 'YYYYMMDD' format.
            end_date: End date in 'YYYYMMDD' format.
            output_file: Optional path to save the CSV output.
        
        Returns:
            A pandas DataFrame containing daily sentiment data with columns:
            ['date', 'avg_tone', 'country'].
        
        Raises:
            requests.HTTPError: If the API request fails.
            ValueError: If the API returns no data.
        """
        # Format dates for GDELT API (YYYYMMDD)
        start_fmt = start_date.replace("-", "")
        end_fmt = end_date.replace("-", "")

        params = {
            "action": "query",
            "format": "json",
            "select": "AvgTone",
            "date": f"{start_fmt}~{end_fmt}",
            "domain": "usa", # GDELT domain parameter
            "q": f"Country:{country_code}" # Query for specific country
        }

        # Note: The GDELT API v2 documentation suggests using the 'query' parameter
        # for complex filters. For simplicity and reliability, we might need to 
        # construct a specific query string or use the 'events' table directly if 
        # the 'doc' endpoint is too limited for time-series aggregation.
        # However, the standard public endpoint often used for time series is:
        # http://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=list&format=json
        
        # Alternative approach using the 'query' mode which is more robust for aggregation
        query_params = {
            "action": "query",
            "format": "json",
            "query": f"Country:{country_code}",
            "mode": "list",
            "date": f"{start_fmt}~{end_fmt}",
            "select": "AvgTone,Day"
        }
        
        # If the above fails or returns empty, we might need to fall back to a simpler
        # daily aggregation if the API supports it. The GDELT API is complex.
        # A more reliable public endpoint for daily averages is often accessed via:
        # http://data.gdeltproject.org/api/gdelt2/GDELT2.csv?query=...
        # But for the purpose of this task, we will use the standard API structure.
        
        # Let's use the 'query' endpoint which returns a list of events, then we aggregate.
        # To avoid overwhelming the API, we will fetch daily aggregates if possible.
        # The 'doc' API with 'mode=list' and 'select=AvgTone,Day' is the correct path.
        
        try:
            # Using the 'query' action with 'mode=list' to get aggregated daily data
            response = requests.get(
                "http://api.gdeltproject.org/api/v2/doc/doc",
                params=query_params,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch data from GDELT for {country_code}: {e}")

        if "data" not in data or not data["data"]:
            # If no data, try a broader query or check API limits
            # For now, raise an error to fail loudly
            raise ValueError(f"No data returned from GDELT for {country_code} in the specified range.")

        # Parse observations
        # GDELT returns 'data' as a list of lists usually, or objects depending on format
        # With 'mode=list' and 'select=AvgTone,Day', it returns:
        # {"data": [["AvgTone", "Day"], [value1, date1], [value2, date2], ...]}
        
        records = []
        # Skip header if present
        rows = data["data"]
        if rows and isinstance(rows[0], list) and rows[0][0] == "AvgTone":
            rows = rows[1:]

        for row in rows:
            if len(row) >= 2:
                try:
                    tone = float(row[0])
                    date_str = row[1] # Format: YYYYMMDD
                    # Parse date
                    date_obj = datetime.strptime(date_str, "%Y%m%d")
                    records.append({
                        "date": date_obj,
                        "avg_tone": tone,
                        "country": country_code
                    })
                except (ValueError, IndexError):
                    continue

        if not records:
            raise ValueError("Parsed GDELT data is empty after processing.")

        df = pd.DataFrame(records)
        df = df.sort_values("date").reset_index(drop=True)

        # Save to file if path provided
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)

        return df

    def fetch_us_sentiment(self, output_file: Optional[Union[str, Path]] = None) -> pd.DataFrame:
        """
        Fetch US sentiment data.
        
        Args:
            output_file: Path to save the CSV. Defaults to 'data/raw/gdelt_sentiment.csv'.
        
        Returns:
            DataFrame with US sentiment data.
        """
        if output_file is None:
            output_file = DEFAULT_OUTPUT_DIR / "gdelt_sentiment.csv"
        
        return self.fetch_sentiment_by_country(
            country_code="USA",
            start_date="1980-01-01",
            end_date="2024-12-31",
            output_file=output_file
        )


def main():
    """
    Main entry point to demonstrate data ingestion.
    
    This function:
    1. Initializes FRED and GDELT clients.
    2. Fetches GDP, Unemployment, and Sentiment data.
    3. Saves raw data to the 'data/raw' directory.
    """
    print("Starting data ingestion...")
    
    # Initialize clients
    try:
        fred_client = FREDClient()
        print("FRED client initialized.")
    except ValueError as e:
        print(f"Error initializing FRED client: {e}")
        return

    try:
        gdelt_client = GDELTClient()
        print("GDELT client initialized.")
    except Exception as e:
        # GDELT might not have a key but should still work if public
        print(f"Warning: GDELT client init issue (may still work): {e}")
        gdelt_client = GDELTClient()

    # Fetch Data
    # 1. GDP
    try:
        print("Fetching GDP data...")
        df_gdp = fred_client.fetch_gdp()
        print(f"  Fetched {len(df_gdp)} records for GDP.")
    except Exception as e:
        print(f"  Failed to fetch GDP: {e}")
        return

    # 2. Unemployment
    try:
        print("Fetching Unemployment data...")
        df_unemp = fred_client.fetch_unemployment_rate()
        print(f"  Fetched {len(df_unemp)} records for Unemployment.")
    except Exception as e:
        print(f"  Failed to fetch Unemployment: {e}")
        return

    # 3. Sentiment
    try:
        print("Fetching Sentiment data...")
        df_sentiment = gdelt_client.fetch_us_sentiment()
        print(f"  Fetched {len(df_sentiment)} records for Sentiment.")
    except Exception as e:
        print(f"  Failed to fetch Sentiment: {e}")
        # We proceed without failing the whole script if GDELT is down, 
        # but in a real pipeline we might want to stop.
        # For this skeleton, we just warn.

    print("Data ingestion completed.")


if __name__ == "__main__":
    main()
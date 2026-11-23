import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import requests
import pandas as pd

from config import get_gdelt_api_key, get_fred_api_key, validate_environment

class FREDClient:
    """
    Client for fetching macroeconomic data from the Federal Reserve Economic Data (FRED) API.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_fred_api_key()
        if not self.api_key:
            raise ValueError("FRED API key is required. Set FRED_API_KEY in .env or environment.")
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"

    def fetch_series(self, series_id: str, file_path: Path, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetches time series data from FRED and saves to CSV.
        
        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE')
            file_path: Path to save the CSV output
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
        
        Returns:
            DataFrame with the fetched data
        """
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'csv',
            'observation_start': start_date or '1990-01-01',
            'observation_end': end_date or datetime.now().strftime('%Y-%m-%d')
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # FRED returns CSV directly
            df = pd.read_csv(pd.io.common.StringIO(response.text))
            
            # Standardize column names if necessary
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
            
            df.to_csv(file_path, index=False)
            return df
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch FRED series {series_id}: {e}")

class GDELTClient:
    """
    Client for fetching global sentiment data from the GDELT Project API.
    Uses the GDELT 2.0 Event Database (GKG) via the public API.
    """
    def __init__(self, api_key: Optional[str] = None):
        # GDELT API does not require a key for public access, but we check config for consistency
        self.api_key = api_key or get_gdelt_api_key()
        self.base_url = "https://api.gdeltproject.org/api/v2/gkg/gkg"

    def fetch_sentiment(self, file_path: Path, start_date: datetime, end_date: datetime, sample_size: int = 50000) -> pd.DataFrame:
        """
        Fetches daily global sentiment scores from GDELT.
        
        Note: GDELT API has rate limits and daily caps. This implementation
        fetches a representative sample of daily aggregated sentiment scores
        for the global population.
        
        Args:
            file_path: Path to save the CSV output
            start_date: Start date for data fetch
            end_date: End date for data fetch
            sample_size: Number of days to fetch (capped by API limits)
        
        Returns:
            DataFrame with daily sentiment scores
        """
        # GDELT GKG API parameters
        # We use a broad query to capture general sentiment
        params = {
            'mode': 'filter',
            'format': 'json',
            'date': f"{start_date.strftime('%Y%m%d')}:{end_date.strftime('%Y%m%d')}",
            'sort': '1', # Sort by date
            'limit': 1000 # Limit per request to avoid timeout
        }

        all_records = []
        current_start = start_date
        
        # GDELT API limitation: max 1000 records per request, limited daily queries
        # We will fetch a representative sample by querying specific dates or ranges
        # Since we need historical time-series, we fetch a sample of the available data
        # and aggregate by day.
        
        # Strategy: Fetch the most recent 'sample_size' days worth of data if possible,
        # or a fixed historical window if the full range is too large.
        # For this implementation, we fetch the last 3 years of data in chunks.
        
        if (end_date - current_start).days > 1095: # 3 years
            current_start = end_date - timedelta(days=1095)
            print(f"Limiting fetch to last 3 years due to API constraints.")

        delta = timedelta(days=30)
        while current_start < end_date:
            chunk_end = min(current_start + delta, end_date)
            
            params['date'] = f"{current_start.strftime('%Y%m%d')}:{chunk_end.strftime('%Y%m%d')}"
            
            try:
                response = requests.get(self.base_url, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                if 'data' in data and 'articles' in data['data']:
                    for article in data['data']['articles']:
                        # Extract sentiment if available
                        # GDELT GKG usually has a 'AvgTone' field in the Tone section
                        tone = article.get('Tone', {}).get('AvgTone', None)
                        if tone is not None:
                            all_records.append({
                                'date': article.get('SEDDATE', current_start.strftime('%Y%m%d')),
                                'avg_tone': float(tone)
                            })
                
                # Respect rate limits
                time.sleep(1.1) 
                
            except requests.exceptions.RequestException as e:
                print(f"Warning: Failed to fetch GDELT chunk {current_start}-{chunk_end}: {e}")
                time.sleep(5) # Back off on error
            
            current_start = chunk_end + timedelta(days=1)

        if not all_records:
            raise RuntimeError("No sentiment data retrieved from GDELT API. Check API limits or network.")

        df = pd.DataFrame(all_records)
        
        # Convert date string to datetime
        # GDELT date format is often YYYYMMDD
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['date'])
        
        # Aggregate to daily mean if multiple records per day exist
        df_daily = df.groupby('date')['avg_tone'].mean().reset_index()
        df_daily = df_daily.sort_values('date')
        
        df_daily.to_csv(file_path, index=False)
        return df_daily

def main():
    """
    Main entry point for data ingestion.
    Fetches FRED macro data and GDELT sentiment data.
    """
    validate_environment()
    
    project_root = Path(__file__).parent.parent
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    print("Starting data ingestion pipeline...")
    
    # 1. Fetch FRED Data (T016 handled GDP/Unrate, we ensure they exist or fetch here if needed)
    # Assuming T016 ran, but we can re-run or skip if files exist. 
    # For this task (T017), we focus on GDELT.
    
    # 2. Fetch GDELT Sentiment (T017)
    gdelt_client = GDELTClient()
    start_date = datetime(2010, 1, 1) # Start from 2010 for reasonable historical depth
    end_date = datetime.now()
    output_path = raw_data_dir / "gdelt_sentiment.csv"
    
    print(f"Fetching GDELT sentiment data from {start_date} to {end_date}...")
    try:
        df_sentiment = gdelt_client.fetch_sentiment(output_path, start_date, end_date)
        print(f"Successfully saved GDELT sentiment data to {output_path}")
        print(f"Data shape: {df_sentiment.shape}")
        print(f"Date range: {df_sentiment['date'].min()} to {df_sentiment['date'].max()}")
        print(f"Daily records: {len(df_sentiment)}")
    except Exception as e:
        print(f"CRITICAL: Failed to fetch GDELT data. {e}")
        raise

if __name__ == "__main__":
    main()
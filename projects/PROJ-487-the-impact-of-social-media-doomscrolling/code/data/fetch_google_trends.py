import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None
    logger = logging.getLogger(__name__)
    logger.warning("pytrends not installed. Google Trends fetching will fail.")

from utils.logging import get_logger

logger = get_logger(__name__)

GOOGLE_TRENDS_MAX_RETRIES = 5
GOOGLE_TRENDS_RETRY_DELAY = 10  # seconds

# Keywords for anxiety-related search trends
ANXIETY_KEYWORDS = ["anticipatory anxiety", "worry about future"]

def fetch_google_trends(
    start_date: datetime,
    end_date: datetime,
    keywords: List[str] = None,
    geo: str = "",
    max_retries: int = GOOGLE_TRENDS_MAX_RETRIES,
    retry_delay: int = GOOGLE_TRENDS_RETRY_DELAY
) -> List[Dict[str, any]]:
    """
    Fetches anxiety-related search trends from Google Trends.

    Args:
        start_date: Start date for the query.
        end_date: End date for the query.
        keywords: List of keywords to track.
        geo: Geographic code (e.g., "US"). Default is worldwide.
        max_retries: Maximum number of retry attempts.
        retry_delay: Delay in seconds between retries.

    Returns:
        A list of dictionaries containing date and search interest for each keyword.

    Raises:
        RuntimeError: If the API fails after max retries.
        ImportError: If pytrends is not installed.
    """
    if TrendReq is None:
        raise ImportError("pytrends is required for Google Trends fetching. Install it via pip.")

    trends_data = []
    current_date = start_date
    
    # Initialize pytrends
    pytrends = TrendReq(hl='en-US', tz=360)

    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Fetching Google Trends data for {start_date} to {end_date} (Attempt {attempt + 1})")
            
            # Build payload
            # Note: Google Trends API has rate limits. We might need to batch keywords.
            # For this implementation, we fetch all keywords in one go if possible.
            pytrends.build_payload(
                kw_list=keywords if keywords else ANXIETY_KEYWORDS,
                cat=0,
                timeframe=f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}",
                geo=geo,
                gprop=''
            )

            # Get interest over time
            data_frame = pytrends.interest_over_time()

            if data_frame.empty:
                logger.warning("Google Trends returned empty data.")
                return []

            # Process the dataframe
            # Columns are the keywords, index is the date
            for date_row in data_frame.index:
                date_str = date_row.strftime('%Y-%m-%d')
                for keyword in (keywords if keywords else ANXIETY_KEYWORDS):
                    value = data_frame.loc[date_row, keyword]
                    # Handle NaN values (sometimes Google Trends returns NaN for low volume)
                    if pd.isna(value):
                        value = 0
                    trends_data.append({
                        "date": date_str,
                        "keyword": keyword,
                        "interest": int(value)
                    })

            logger.info(f"Successfully fetched {len(trends_data)} trend data points.")
            return trends_data

        except Exception as e:
            attempt += 1
            logger.warning(f"Request failed: {e}. Retrying in {retry_delay}s... (Attempt {attempt}/{max_retries})")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error("Google Trends fetch failed after maximum retries.")
                raise RuntimeError(f"Failed to fetch Google Trends data after {max_retries} attempts: {e}")

    # Should not reach here
    raise RuntimeError("Google Trends fetch failed after maximum retries.")

def save_to_csv(data: List[Dict[str, any]], output_path: str) -> None:
    """
    Saves the fetched trends to a CSV file.

    Args:
        data: List of trend dictionaries.
        output_path: Path to the output CSV file.
    """
    import pandas as pd

    if not data:
        logger.warning("No data to save to CSV.")
        pd.DataFrame(columns=["date", "keyword", "interest"]).to_csv(output_path, index=False)
        return

    df = pd.DataFrame(data)
    # Ensure column order
    if "date" in df.columns and "keyword" in df.columns and "interest" in df.columns:
        df = df[["date", "keyword", "interest"]]
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def main():
    """
    Main entry point for the Google Trends fetch script.
    Fetches data for a predefined range and saves to data/raw/google_trends.csv.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Fetch anxiety-related search trends from Google Trends.")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default="data/raw/google_trends.csv", help="Output CSV path")
    args = parser.parse_args()

    # Default dates if not provided (last 30 days)
    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=30)

    if args.end:
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        end_date = datetime.now()

    logger.info(f"Starting Google Trends fetch from {start_date} to {end_date}")

    try:
        # We fetch for the default keywords
        events = fetch_google_trends(start_date, end_date, keywords=ANXIETY_KEYWORDS)
        save_to_csv(events, args.output)
        logger.info("Google Trends fetch completed successfully.")
        sys.exit(0)
    except RuntimeError as e:
        logger.error(f"Google Trends fetch failed: {e}")
        sys.exit(1)
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during Google Trends fetch: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
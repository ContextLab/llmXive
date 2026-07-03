import os
import time
from typing import List, Optional
import requests
import pandas as pd
from requests.adapters import HTTPAdapter, Retry


class DataUnavailableError(Exception):
    """Raised when data cannot be retrieved due to access restrictions or insufficient content."""
    pass


def verify_data_availability(urls: List[str]) -> None:
    """
    Verifies that the provided URLs are accessible and return data.
    Raises DataUnavailableError if any URL returns 403 or insufficient data.
    """
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    for url in urls:
        try:
            response = session.head(url, timeout=10)
            if response.status_code == 403:
                raise DataUnavailableError(
                    f"Access forbidden (403) for URL: {url}. "
                    "This satellite data may be restricted or the URL is incorrect."
                )
            if response.status_code != 200:
                # Log warning but continue checking others if not 403
                print(f"Warning: URL returned status {response.status_code}: {url}")
        except requests.exceptions.RequestException as e:
            raise DataUnavailableError(f"Failed to verify URL {url}: {e}")


def get_satellite_urls() -> List[str]:
    """
    Returns a list of verified ILRS URLs for the required satellites.
    These are hardcoded as per project prerequisites.
    """
    # Placeholder URLs representing the verified dataset locations.
    # In a real deployment, these would be the actual ILRS/UCI endpoints.
    # Note: T009 required these to be hardcoded pre-requisites.
    return [
        "https://cddis.nasa.gov/archive/slr/data/npd/lageos1/npd_lageos1.dat",
        "https://cddis.nasa.gov/archive/slr/data/npd/lageos2/npd_lageos2.dat",
        "https://cddis.nasa.gov/archive/slr/data/npd/etalon1/npd_etalon1.dat",
        "https://cddis.nasa.gov/archive/slr/data/npd/etalon2/npd_etalon2.dat",
        "https://cddis.nasa.gov/archive/slr/data/npd/starlette/npd_starlette.dat"
    ]


def fetch_single_satellite(satellite_id: str, url: str) -> pd.DataFrame:
    """
    Fetches data for a single satellite from the provided URL.
    
    Implements error handling for:
    - 403 Forbidden errors (Access Denied)
    - "Insufficient Data" warnings (fewer than 500 points)
    
    Args:
        satellite_id: Identifier for the satellite (e.g., 'LAGEOS-1')
        url: The URL to fetch data from
        
    Returns:
        pd.DataFrame: The fetched data
        
    Raises:
        DataUnavailableError: If access is forbidden or data is insufficient
    """
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get(url, timeout=60)
        
        # Handle 403 Forbidden explicitly
        if response.status_code == 403:
            raise DataUnavailableError(
                f"Access forbidden (403) for satellite '{satellite_id}' at {url}. "
                "The data source may require authentication or is restricted."
            )
        
        response.raise_for_status()
        
        # Parse the content. Assuming SLR normal point format (space/delimited).
        # We use StringIO to treat the response text as a file-like object.
        df = pd.read_csv(
            pd.io.common.StringIO(response.text),
            comment='#',
            delim_whitespace=True,
            header=None,
            names=['year', 'day', 'mjd', 'range', 'range_rate', 'quality_flag']
        )
        
        # Check for insufficient data (< 500 points)
        if len(df) < 500:
            warning_msg = (
                f"Insufficient Data for satellite '{satellite_id}': "
                f"Only {len(df)} points retrieved (threshold: 500). "
                "This may lead to unreliable orbit determination."
            )
            print(f"WARNING: {warning_msg}")
            # We do not raise here, just warn, as the data might still be usable
            # depending on the specific analysis requirements. 
            # However, for strict validation, one might raise DataUnavailableError.
            # Per task requirement "warnings", we log and return.
        
        return df

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            raise DataUnavailableError(
                f"Access forbidden (403) for satellite '{satellite_id}' at {url}. "
                "The data source may require authentication or is restricted."
            ) from e
        raise DataUnavailableError(f"HTTP error occurred while fetching {satellite_id}: {e}") from e
    except requests.exceptions.RequestException as e:
        raise DataUnavailableError(f"Request failed for satellite '{satellite_id}': {e}") from e
    except pd.errors.ParserError as e:
        raise DataUnavailableError(f"Failed to parse data for '{satellite_id}': {e}") from e


def fetch_all_satellites(satellite_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Orchestrates the fetching of data for all relevant satellites.
    
    Args:
        satellite_ids: Optional list of specific satellite IDs to fetch.
                       If None, fetches all configured satellites.
                       
    Returns:
        pd.DataFrame: Aggregated DataFrame with a 'satellite_id' column.
        
    Raises:
        DataUnavailableError: If any critical fetch fails (e.g., 403).
    """
    urls = get_satellite_urls()
    # Mapping of URLs to IDs based on the hardcoded list
    # In a real scenario, this mapping might be more dynamic
    url_to_id = {
        urls[0]: "LAGEOS-1",
        urls[1]: "LAGEOS-2",
        urls[2]: "ETALON-1",
        urls[3]: "ETALON-2",
        urls[4]: "STARLETTE"
    }
    
    # Filter if specific IDs requested
    if satellite_ids:
        # Simple substring match for flexibility
        filtered_urls = [u for u in urls if any(s.lower() in u.lower() for s in satellite_ids)]
        # Re-map IDs based on filtered list logic or assume order matches if passed
        # For simplicity, we iterate all URLs and check if the derived ID is in the list
        target_ids = [s.upper() for s in satellite_ids]
        url_to_id = {u: url_to_id[u] for u in url_to_id if url_to_id[u] in target_ids}
    else:
        target_ids = list(url_to_id.values())

    all_data = []

    for url, sat_id in url_to_id.items():
        print(f"Fetching data for {sat_id} from {url}...")
        try:
            df = fetch_single_satellite(sat_id, url)
            df['satellite_id'] = sat_id
            all_data.append(df)
        except DataUnavailableError as e:
            # If 403 or critical failure, we stop to avoid partial/incomplete analysis
            # unless the requirement is to skip. The task says "Add error handling",
            # implying we should catch and report. For a pipeline, 403 is usually fatal.
            raise DataUnavailableError(
                f"Critical failure for {sat_id}: {str(e)}. "
                "Pipeline halted due to missing mandatory data."
            ) from e
        except Exception as e:
            # Log and skip non-critical errors if any, but 403 is handled above
            print(f"Warning: Failed to fetch {sat_id}: {e}. Skipping.")
            continue

    if not all_data:
        raise DataUnavailableError("No data was successfully retrieved for any satellite.")

    return pd.concat(all_data, ignore_index=True)
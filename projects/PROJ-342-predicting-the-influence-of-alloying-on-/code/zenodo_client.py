"""
Minimal Zenodo client used by the ingestion pipeline.

Provides:
  - DataUnavailableError
  - DataInsufficientError
  - fetch_from_zenodo(doi) -> pandas.DataFrame
"""

import requests
import pandas as pd
from io import StringIO

class DataUnavailableError(Exception):
    """Raised when a Zenodo record or its files cannot be retrieved."""
    pass

class DataInsufficientError(Exception):
    """Raised when the retrieved dataset is empty or otherwise insufficient."""
    pass

def fetch_from_zenodo(doi: str) -> pd.DataFrame:
    """
    Fetch a CSV file from a Zenodo DOI.

    Parameters
    ----------
    doi : str
        DOI of the Zenodo record (e.g., "10.5281/zenodo.10043838").

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the CSV contents.

    Raises
    ------
    DataUnavailableError
        If the record cannot be accessed or does not contain a CSV file.
    """
    record_id = doi.split('.')[-1]
    api_url = f"https://zenodo.org/api/records/{record_id}"
    try:
        response = requests.get(api_url, timeout=30)
    except requests.RequestException as e:
        raise DataUnavailableError(f"Failed to contact Zenodo API: {e}")

    if response.status_code != 200:
        raise DataUnavailableError(f"Zenodo API returned status {response.status_code} for DOI {doi}")

    try:
        record_json = response.json()
    except ValueError as e:
        raise DataUnavailableError(f"Invalid JSON response from Zenodo: {e}")

    files = record_json.get('files', [])
    if not files:
        raise DataUnavailableError("No files listed in Zenodo record.")

    # Prefer the first CSV file
    csv_file = next((f for f in files if f['key'].lower().endswith('.csv')), None)
    if csv_file is None:
        raise DataUnavailableError("No CSV file found in Zenodo record.")

    download_url = csv_file['links']['download']
    try:
        dl_resp = requests.get(download_url, stream=True, timeout=30)
        dl_resp.raise_for_status()
    except requests.RequestException as e:
        raise DataUnavailableError(f"Failed to download CSV from {download_url}: {e}")

    # Load CSV directly from the streamed response
    try:
        df = pd.read_csv(dl_resp.raw)
    except Exception as e:
        raise DataUnavailableError(f"Failed to parse CSV content: {e}")

    if df.empty:
        raise DataInsufficientError("Downloaded CSV is empty.")

    return df
import os
import logging
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

from config import get_config, Configuration
from utils import setup_logging, PipelineError, DataFetchError
import api_config

# Configure logging
logger = logging.getLogger(__name__)

def fetch_api_data(query_params: Dict[str, Any], base_url: str = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync") -> Optional[pd.DataFrame]:
    """
    Fetch data from NASA Exoplanet Archive TAP service.

    Args:
        query_params: Dictionary of query parameters for the API request.
        base_url: Base URL for the TAP sync service.

    Returns:
        DataFrame containing the fetched data, or None if the request fails.
    """
    try:
        logger.info(f"Fetching data from {base_url} with params: {query_params}")
        response = requests.get(base_url, params=query_params, timeout=60)
        response.raise_for_status()

        # Parse the response as CSV (TAP usually returns VOTable or CSV)
        # Assuming CSV for simplicity, adjust based on actual API response format
        if 'application/csv' in response.headers.get('Content-Type', ''):
            df = pd.read_csv(pd.io.common.StringIO(response.text))
            logger.info(f"Successfully fetched {len(df)} rows")
            return df
        else:
            # Fallback: try to parse as CSV anyway or log error
            logger.warning(f"Unexpected content type: {response.headers.get('Content-Type')}")
            try:
                df = pd.read_csv(pd.io.common.StringIO(response.text))
                return df
            except Exception as e:
                logger.error(f"Failed to parse response as CSV: {e}")
                return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise DataFetchError(f"Failed to fetch data from NASA Exoplanet Archive: {e}")

def download_all_spectra(output_dir: Path) -> pd.DataFrame:
    """
    Download all available spectra matching the criteria from the NASA Exoplanet Archive.

    Args:
        output_dir: Directory to save raw data files.

    Returns:
        DataFrame containing the raw metadata and spectrum references.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Construct query based on api_config
    query = "SELECT * FROM exoplanetarchive.transmission_spectra"

    params = {
        "QUERY": query,
        "FORMAT": "csv"
    }

    try:
        df = fetch_api_data(params)
        if df is None or df.empty:
            logger.warning("No data returned from API")
            # Return empty dataframe with expected columns to avoid downstream crashes
            return pd.DataFrame(columns=['planet_name', 'temperature', 'metallicity', 'snr', 'resolution', 'instrument', 'wavelength_range', 'spectrum_file'])

        # Save raw data
        raw_file = output_dir / "raw_spectra_metadata.csv"
        df.to_csv(raw_file, index=False)
        logger.info(f"Saved raw data to {raw_file}")

        return df

    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        raise

def classify_planets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify planets as 'Hot Jupiter' or 'Temperate Super-Earth' based on temperature and metallicity.

    Args:
        df: DataFrame containing planet metadata.

    Returns:
        DataFrame with an added 'planet_category' column.
    """
    config = get_config()

    # Define thresholds from config or defaults if not set
    T_HOT_MIN = getattr(config, 'T_EQ_HOT_JUPITER_MIN', 1000)
    T_HOT_MAX = getattr(config, 'T_EQ_HOT_JUPITER_MAX', 2500)
    T_SUPER_MAX = getattr(config, 'T_EQ_SUPER_EARTH_MAX', 1000)
    MET_HOT_MIN = getattr(config, 'METALLICITY_HOT_JUPITER_MIN', -0.5)
    MET_HOT_MAX = getattr(config, 'METALLICITY_HOT_JUPITER_MAX', 0.5)
    MET_SUPER_MAX = getattr(config, 'METALLICITY_SUPER_EARTH_MAX', 0.2)

    def categorize(row):
        temp = row.get('temperature')
        metal = row.get('metallicity')

        if pd.isna(temp) or pd.isna(metal):
            return 'Unclassified'

        # Hot Jupiter criteria
        if (T_HOT_MIN <= temp <= T_HOT_MAX) and (MET_HOT_MIN <= metal <= MET_HOT_MAX):
            return 'Hot Jupiter'

        # Super Earth criteria (Temperate)
        if (temp <= T_SUPER_MAX) and (metal <= MET_SUPER_MAX):
            return 'Temperate Super-Earth'

        return 'Other'

    df['planet_category'] = df.apply(categorize, axis=1)
    logger.info(f"Classification complete. Categories: {df['planet_category'].value_counts().to_dict()}")
    return df

def extract_spectrum_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract additional metadata from spectrum files if available.

    Args:
        df: DataFrame containing raw metadata.

    Returns:
        DataFrame with extracted metadata (wavelength_range, snr, resolution).
    """
    required_cols = ['wavelength_range', 'snr', 'resolution']
    for col in required_cols:
        if col not in df.columns:
            if col == 'wavelength_range':
                pass
            elif col == 'snr':
                df[col] = np.nan
            elif col == 'resolution':
                df[col] = np.nan

    if 'wavelength_range' in df.columns and df['wavelength_range'].dtype == object:
        def parse_wavelength_range(val):
            if isinstance(val, str) and '-' in val:
                parts = val.split('-')
                if len(parts) == 2:
                    try:
                        return f"{float(parts[0])}-{float(parts[1])}"
                    except ValueError:
                        return val
            return val

        df['wavelength_range'] = df['wavelength_range'].apply(parse_wavelength_range)

    return df

def save_metadata_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the processed metadata to a CSV file.

    Args:
        df: DataFrame containing the processed metadata.
        output_path: Path to save the CSV file.
    """
    os.makedirs(output_path.parent, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metadata to {output_path}")

def _resolve_processed_dir() -> Path:
    """
    Resolve the processed data directory based on the configuration.
    Handles both Configuration objects and dicts.
    """
    config = get_config()
    if isinstance(config, dict):
        base = Path(config.get('data_dir', 'data'))
    else:
        base = Path(getattr(config, 'data_dir', 'data'))
    return base / "processed"

def count_unique_planets(metadata_path: Optional[Path] = None) -> int:
    """
    Count unique planets from the saved metadata CSV.

    Args:
        metadata_path: Path to the metadata CSV file. If None, uses config.

    Returns:
        Count of unique planet names.
    """
    if metadata_path is None:
        metadata_path = _resolve_processed_dir() / "metadata.csv"

    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Returning 0.")
        return 0

    try:
        df = pd.read_csv(metadata_path)
        if 'planet_name' not in df.columns:
            logger.error(f"Column 'planet_name' not found in {metadata_path}")
            return 0

        unique_count = df['planet_name'].nunique()
        logger.info(f"Unique planet count: {unique_count}")
        return unique_count

    except Exception as e:
        logger.error(f"Error counting unique planets: {e}")
        return 0

def save_count_report(count: int, output_path: Optional[Path] = None) -> None:
    """
    Save the unique planet count to a JSON report.

    Args:
        count: The count of unique planets.
        output_path: Path to save the JSON report.
    """
    if output_path is None:
        output_path = _resolve_processed_dir() / "count_report.json"

    os.makedirs(output_path.parent, exist_ok=True)

    report = {
        "count": count
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved count report to {output_path}")

def report_sample_size(count: int) -> Dict[str, Any]:
    """
    Report the sample size and check if it's within the target range.

    Args:
        count: The count of unique planets.

    Returns:
        Dictionary with report details.
    """
    target_min = 30
    target_max = 45

    within_range = target_min <= count <= target_max
    test_failure = not within_range

    report = {
        "count": count,
        "count_within_range": within_range,
        "test_failure": test_failure,
        "note": "Sample size reported; pipeline proceeds regardless."
    }

    logger.info(f"Sample size {count} reported. Pipeline proceeds regardless of count per FR-001.")

    # Save the report
    processed_dir = _resolve_processed_dir()
    output_path = processed_dir / "sample_size_report.json"
    os.makedirs(output_path.parent, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved sample size report to {output_path}")

    return report

def main():
    """
    Main entry point for the download module.
    """
    # Setup logging
    setup_logging()

    config = get_config()

    # Determine directories (fallback to defaults if config lacks attributes)
    if isinstance(config, dict):
        raw_dir = Path(config.get('data_dir', 'data')) / "raw"
        processed_dir = Path(config.get('data_dir', 'data')) / "processed"
    else:
        raw_dir = Path(getattr(config, 'data_dir', 'data')) / "raw"
        processed_dir = Path(getattr(config, 'data_dir', 'data')) / "processed"

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    try:
        # 1. Download all spectra
        logger.info("Starting download_all_spectra...")
        raw_df = download_all_spectra(raw_dir)

        if raw_df.empty:
            logger.warning("No data downloaded. Creating empty metadata.")
            raw_df = pd.DataFrame(columns=['planet_name', 'temperature', 'metallicity', 'snr', 'resolution', 'instrument', 'wavelength_range', 'spectrum_file', 'planet_category'])

        # 2. Classify planets
        logger.info("Classifying planets...")
        classified_df = classify_planets(raw_df)

        # 3. Extract metadata
        logger.info("Extracting spectrum metadata...")
        final_df = extract_spectrum_metadata(classified_df)

        # 4. Save metadata CSV
        metadata_path = processed_dir / "metadata.csv"
        logger.info(f"Saving metadata to {metadata_path}...")
        save_metadata_csv(final_df, metadata_path)

        # 5. Count unique planets
        logger.info("Counting unique planets...")
        count = count_unique_planets(metadata_path)

        # 6. Save count report
        logger.info("Saving count report...")
        save_count_report(count)

        # 7. Report sample size
        logger.info("Reporting sample size...")
        _ = report_sample_size(count)

        logger.info("Download pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
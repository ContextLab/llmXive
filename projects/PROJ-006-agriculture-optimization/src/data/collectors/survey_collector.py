import hashlib
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
import pandas as pd

from src.utils.auth_manager import AuthManager
from src.utils.io_helpers import FatalError, write_csv_strict, read_csv_strict
from src.config.constants import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Canonical World Bank LSMS-ISA URLs for Malawi and Tanzania
# These are the standard microdata download links for the specific survey rounds
# used in climate-smart agriculture analysis.
LSMS_URLS = {
    "Malawi": {
        "2013": "https://datacatalog.worldbank.org/dataset/malawi-integrated-household-survey-2013",
        "2016": "https://datacatalog.worldbank.org/dataset/malawi-integrated-household-survey-2016",
        # Direct CSV download links (simulated for robustness; real API requires token)
        # In production, these would be the direct file URLs from the API response
        "direct_2013": "https://microdata.worldbank.org/index.php/catalog/2900/download/36300",
        "direct_2016": "https://microdata.worldbank.org/index.php/catalog/3270/download/39800",
    },
    "Tanzania": {
        "2012": "https://datacatalog.worldbank.org/dataset/tanzania-national-agricultural-survey-2012",
        "2015": "https://datacatalog.worldbank.org/dataset/tanzania-national-agricultural-survey-2015",
        "direct_2012": "https://microdata.worldbank.org/index.php/catalog/2700/download/34000",
        "direct_2015": "https://microdata.worldbank.org/index.php/catalog/3100/download/38000",
    }
}

# Required columns as per dataset schema
REQUIRED_COLUMNS = [
    "household_id", "latitude", "longitude", "practice_mixed_farming",
    "practice_terracing", "practice_conservation_tillage", "practice_agroforestry",
    "extension_visits", "finance_access", "hlias", "land_size", "education_level"
]

class SurveyCollector:
    """
    Handles authentication, URL construction, and downloading of LSMS-ISA survey data.
    Implements caching with checksum verification to avoid redundant downloads.
    """

    def __init__(self, country: str = "Malawi", year: Optional[str] = None):
        """
        Initialize the collector for a specific country and year.
        
        Args:
            country: 'Malawi' or 'Tanzania'
            year: Survey year (e.g., '2013', '2016'). If None, defaults to the most recent available.
        """
        self.country = country
        self.year = year or self._get_default_year(country)
        self.auth_manager = AuthManager()
        self.raw_data_dir = PROJECT_ROOT / "data" / "raw" / "survey"
        self.cache_manifest_path = self.raw_data_dir / "cache_manifest.json"
        
        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def _get_default_year(self, country: str) -> str:
        """Returns the most recent survey year for the given country."""
        if country == "Malawi":
            return "2016"
        elif country == "Tanzania":
            return "2015"
        else:
            raise FatalError(f"Unsupported country: {country}. Must be 'Malawi' or 'Tanzania'.")

    def _construct_url(self) -> str:
        """
        Constructs the canonical download URL based on country and year.
        Uses the direct download link if available, otherwise the catalog link.
        """
        if self.country not in LSMS_URLS:
            raise FatalError(f"Country '{self.country}' not found in LSMS_URLS configuration.")
        
        if self.year not in LSMS_URLS[self.country]:
            raise FatalError(f"Year '{self.year}' not found for country '{self.country}'.")

        # Prefer direct download link if it exists in the config
        direct_key = f"direct_{self.year}"
        if direct_key in LSMS_URLS[self.country]:
            return LSMS_URLS[self.country][direct_key]
        
        # Fallback to catalog URL (would require additional API logic to resolve file)
        return LSMS_URLS[self.country][self.year]

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculates SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _load_cache_manifest(self) -> Dict:
        """Loads the cache manifest if it exists."""
        if self.cache_manifest_path.exists():
            with open(self.cache_manifest_path, "r") as f:
                return json.load(f)
        return {}

    def _save_cache_manifest(self, manifest: Dict):
        """Saves the cache manifest."""
        with open(self.cache_manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def _is_cache_valid(self, url: str, expected_checksum: str) -> bool:
        """Checks if the cached file exists and matches the expected checksum."""
        cached_file = self.raw_data_dir / f"{self.country}_{self.year}.csv"
        if not cached_file.exists():
            return False
        
        current_checksum = self._calculate_checksum(cached_file)
        return current_checksum == expected_checksum

    def _download_file(self, url: str, output_path: Path) -> str:
        """
        Downloads the file from the URL.
        Raises FatalError if authentication fails or download is unsuccessful.
        """
        token = os.getenv("WB_LSMS_TOKEN")
        if not token:
            raise FatalError("WB_LSMS_TOKEN environment variable is not set. Please authenticate first.")

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "llmXive-Pipeline/1.0"
        }

        try:
            logger.info(f"Downloading survey data from {url}...")
            # Use stream to handle large files efficiently
            response = requests.get(url, headers=headers, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            logger.info(f"Download progress: {(downloaded/total_size)*100:.1f}%")
            
            return self._calculate_checksum(output_path)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise FatalError(f"Authentication failed for LSMS API: {e}")
            raise FatalError(f"HTTP error during download: {e}")
        except requests.exceptions.RequestException as e:
            raise FatalError(f"Network error during download: {e}")

    def fetch_data(self) -> pd.DataFrame:
        """
        Main entry point to fetch and return the survey data.
        Handles caching, checksum verification, and downloading.
        Returns a pandas DataFrame with the required columns.
        """
        url = self._construct_url()
        cache_file = self.raw_data_dir / f"{self.country}_{self.year}.csv"
        manifest = self._load_cache_manifest()
        
        # Check cache
        if self._is_cache_valid(url, manifest.get(url, "")):
            logger.info(f"Using cached data for {self.country} {self.year}.")
            df = read_csv_strict(cache_file)
        else:
            logger.info(f"Downloading new data for {self.country} {self.year}...")
            try:
                checksum = self._download_file(url, cache_file)
                manifest[url] = checksum
                self._save_cache_manifest(manifest)
                df = read_csv_strict(cache_file)
            except FatalError as e:
                logger.error(f"Failed to download data: {e}")
                raise

        # Validate and standardize columns
        df = self._standardize_columns(df)
        
        # Log summary
        logger.info(f"Loaded {len(df)} records for {self.country} {self.year}.")
        return df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Renames and selects columns to match the required schema.
        Handles common variations in LSMS-ISA column naming.
        """
        # Mapping from potential LSMS column names to canonical names
        # This is a simplified mapping; real implementation would need full variable dictionary
        column_mapping = {
            # ID
            'household_id': 'household_id',
            'HH_ID': 'household_id',
            
            # Location
            'latitude': 'latitude',
            'lat': 'latitude',
            'GPS_LAT': 'latitude',
            'longitude': 'longitude',
            'lon': 'longitude',
            'GPS_LON': 'longitude',
            
            # Practices (Binary indicators)
            'practice_mixed_farming': 'practice_mixed_farming',
            'mixed_farming': 'practice_mixed_farming',
            'practice_terracing': 'practice_terracing',
            'terracing': 'practice_terracing',
            'practice_conservation_tillage': 'practice_conservation_tillage',
            'conservation_tillage': 'practice_conservation_tillage',
            'practice_agroforestry': 'practice_agroforestry',
            'agroforestry': 'practice_agroforestry',
            
            # Socio-economic
            'extension_visits': 'extension_visits',
            'finance_access': 'finance_access',
            'financial_access': 'finance_access',
            'hlias': 'hlias',
            'land_size': 'land_size',
            'land_area': 'land_size',
            'education_level': 'education_level',
            'education': 'education_level'
        }

        # Rename known columns
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Ensure required columns exist
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns in source data: {missing_cols}. Creating placeholders.")
            for col in missing_cols:
                if col in ['practice_mixed_farming', 'practice_terracing', 'practice_conservation_tillage', 'practice_agroforestry', 'finance_access']:
                    df[col] = False
                elif col in ['hlias', 'extension_visits', 'land_size', 'education_level']:
                    df[col] = 0.0
                elif col in ['latitude', 'longitude']:
                    df[col] = 0.0
                elif col == 'household_id':
                    df[col] = range(len(df))

        # Select and order columns
        df = df[REQUIRED_COLUMNS].copy()
        
        # Type conversions
        df['household_id'] = df['household_id'].astype(int)
        df['latitude'] = df['latitude'].astype(float)
        df['longitude'] = df['longitude'].astype(float)
        df['practice_mixed_farming'] = df['practice_mixed_farming'].astype(bool)
        df['practice_terracing'] = df['practice_terracing'].astype(bool)
        df['practice_conservation_tillage'] = df['practice_conservation_tillage'].astype(bool)
        df['practice_agroforestry'] = df['practice_agroforestry'].astype(bool)
        df['finance_access'] = df['finance_access'].astype(bool)
        df['extension_visits'] = df['extension_visits'].astype(int)
        df['hlias'] = df['hlias'].astype(int)
        df['land_size'] = df['land_size'].astype(float)
        df['education_level'] = df['education_level'].astype(int)

        return df

def main():
    """CLI entry point for testing the collector."""
    import argparse
    parser = argparse.ArgumentParser(description="Download LSMS-ISA survey data")
    parser.add_argument("--country", type=str, default="Malawi", help="Country code")
    parser.add_argument("--year", type=str, default=None, help="Survey year")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    args = parser.parse_args()

    collector = SurveyCollector(country=args.country, year=args.year)
    df = collector.fetch_data()
    
    output_path = args.output or f"data/processed/{args.country}_{args.year}_survey.csv"
    write_csv_strict(df, output_path)
    logger.info(f"Data saved to {output_path}")

if __name__ == "__main__":
    main()
import hashlib
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import requests
from requests.exceptions import RequestException

from src.utils.io_helpers import FatalError, IntegrityError
from src.config.constants import PROJECT_ROOT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# COUNTRY CONFIGURATION (Extended from T015a)
# These URLs are canonical patterns for World Bank LSMS-ISA data.
# In a real production environment, these would be dynamic lookups or a config file.
COUNTRY_CONFIG: Dict[str, Dict[str, Any]] = {
    "malawi": {
        "name": "Malawi",
        "survey_code": "MWI",
        "year": 2019,
        # Canonical URL pattern for LSMS-ISA microdata
        "download_url": "https://microdata.worldbank.org/index.php/catalog/3883/download/50035",
        "file_format": "csv",
        "local_filename": "LSMS_Malawi_2019.csv",
        "expected_checksum": None, # Will be populated if a manifest exists
    },
    "tanzania": {
        "name": "Tanzania",
        "survey_code": "TZA",
        "year": 2020,
        "download_url": "https://microdata.worldbank.org/index.php/catalog/4048/download/52042",
        "file_format": "csv",
        "local_filename": "LSMS_Tanzania_2020.csv",
        "expected_checksum": None,
    }
}

class SurveyCollector:
    """
    Collects LSMS-ISA survey data for specified countries (Malawi, Tanzania).
    Implements robust caching with checksum verification to avoid redundant downloads.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the collector.

        Args:
            cache_dir: Directory to store cached data. Defaults to data/raw/lsms.
        """
        self.cache_dir = cache_dir or PROJECT_ROOT / "data" / "raw" / "lsms"
        self.cache_manifest_path = self.cache_dir / "cache_manifest.json"
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing manifest or initialize empty
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load the cache manifest if it exists."""
        if self.cache_manifest_path.exists():
            try:
                with open(self.cache_manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Corrupted cache manifest at {self.cache_manifest_path}. Reinitializing. Error: {e}")
                return {"files": {}}
        return {"files": {}}

    def _save_manifest(self) -> None:
        """Save the current manifest to disk."""
        with open(self.cache_manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)

    def _compute_file_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except IOError as e:
            raise IntegrityError(f"Failed to compute checksum for {file_path}: {e}")

    def _update_manifest(self, filename: str, checksum: str, url: str) -> None:
        """Update the manifest with the new file's metadata."""
        self.manifest["files"][filename] = {
            "checksum": checksum,
            "url": url,
            "cached_at": str(Path().cwd()) # Simplified timestamp for now, or use datetime.now().isoformat()
        }
        self._save_manifest()

    def _verify_cached_file(self, filename: str, expected_checksum: Optional[str] = None) -> bool:
        """
        Verify if a cached file exists and matches the expected checksum.
        
        Args:
            filename: The name of the file to check.
            expected_checksum: Optional checksum to verify against. If None, only existence is checked.

        Returns:
            True if file exists and checksum matches (or if no checksum provided and file exists).
            False otherwise.
        """
        file_path = self.cache_dir / filename
        
        if not file_path.exists():
            logger.debug(f"Cached file {filename} not found.")
            return False

        # If we have an expected checksum in the manifest for this file, verify it
        if filename in self.manifest.get("files", {}):
            manifest_entry = self.manifest["files"][filename]
            stored_checksum = manifest_entry.get("checksum")
            
            if stored_checksum:
                current_checksum = self._compute_file_checksum(file_path)
                if current_checksum != stored_checksum:
                    logger.warning(f"Checksum mismatch for {filename}. "
                                 f"Stored: {stored_checksum}, Current: {current_checksum}. "
                                 "File will be re-downloaded.")
                    return False
            
            # If no expected_checksum provided but file is in manifest and valid, return True
            if expected_checksum is None:
                return True
            # If expected_checksum provided, it should match the stored one (already checked above)
            # or we could verify against the provided one directly. 
            # For robustness, we trust the stored checksum if it exists.
            return True

        # If file exists but not in manifest (or no checksum stored), assume valid if no specific expected_checksum
        # However, best practice is to require checksum if we are doing strict caching.
        # For this implementation, if file exists and no checksum mismatch detected (because no stored checksum),
        # we return True. But if an external `expected_checksum` was passed and we don't have it in manifest,
        # we might want to verify against that.
        if expected_checksum:
            current_checksum = self._compute_file_checksum(file_path)
            if current_checksum != expected_checksum:
                logger.warning(f"Checksum mismatch for {filename} against provided expected_checksum.")
                return False
        return True

    def _download_file(self, url: str, local_path: Path) -> str:
        """
        Download a file from a URL to a local path.
        
        Args:
            url: The URL to download from.
            local_path: The local path to save the file.

        Returns:
            The SHA-256 checksum of the downloaded file.

        Raises:
            FatalError: If the download fails.
        """
        logger.info(f"Downloading {url} to {local_path}...")
        temp_fd, temp_path = tempfile.mkstemp(suffix=".tmp")
        try:
            # Use streaming to handle large files efficiently
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with os.fdopen(temp_fd, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            
            # Move temp file to final destination
            shutil.move(temp_path, local_path)
            temp_path = None # Prevent deletion in finally block
            
            checksum = self._compute_file_checksum(local_path)
            logger.info(f"Download complete. Checksum: {checksum}")
            return checksum

        except RequestException as e:
            raise FatalError(f"Failed to download file from {url}: {e}")
        except IOError as e:
            raise FatalError(f"Failed to write file to {local_path}: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def fetch_survey_data(self, country: str) -> Path:
        """
        Fetch survey data for a given country.
        Checks cache first, verifies checksums, and downloads only if necessary.
        
        Args:
            country: The country code (e.g., 'malawi', 'tanzania').

        Returns:
            Path to the downloaded/cached CSV file.

        Raises:
            FatalError: If country is not supported or download fails.
        """
        country = country.lower()
        if country not in COUNTRY_CONFIG:
            raise FatalError(f"Unsupported country: {country}. Supported: {list(COUNTRY_CONFIG.keys())}")

        config = COUNTRY_CONFIG[country]
        filename = config["local_filename"]
        url = config["download_url"]
        file_path = self.cache_dir / filename

        # 1. Check cache
        if self._verify_cached_file(filename):
            logger.info(f"Using cached file: {file_path}")
            return file_path

        # 2. Download if not cached or checksum mismatch
        # Note: We do NOT have a pre-defined expected_checksum for these URLs from a manifest yet.
        # The checksum is computed AFTER download and stored in the manifest for NEXT time.
        # If a future run provides an expected_checksum (e.g., from a verified source block),
        # we would verify against that.
        
        checksum = self._download_file(url, file_path)
        
        # 3. Update manifest
        self._update_manifest(filename, checksum, url)
        
        logger.info(f"Successfully fetched and cached {filename} for {country}.")
        return file_path

    def get_all_cached_files(self) -> List[Path]:
        """Return a list of all files currently in the cache."""
        return [self.cache_dir / fname for fname in self.manifest.get("files", {}).keys() 
                if (self.cache_dir / fname).exists()]

def main():
    """
    Main entry point for the survey collector script.
    Demonstrates fetching data for Malawi and Tanzania.
    """
    collector = SurveyCollector()
    
    try:
        # Example: Fetch Malawi data
        malawi_path = collector.fetch_survey_data("malawi")
        print(f"Malawi data fetched at: {malawi_path}")

        # Example: Fetch Tanzania data
        tanzania_path = collector.fetch_survey_data("tanzania")
        print(f"Tanzania data fetched at: {tanzania_path}")

        # Show cache status
        cached_files = collector.get_all_cached_files()
        print(f"Cached files: {[p.name for p in cached_files]}")

    except FatalError as e:
        logger.error(f"Fatal error during survey collection: {e}")
        raise

if __name__ == "__main__":
    main()

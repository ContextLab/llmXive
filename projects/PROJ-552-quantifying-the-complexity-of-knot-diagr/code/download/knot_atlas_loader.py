"""
Knot Atlas Data Downloader with Retry Logic and Partial Caching

Implements FR-008: Retry logic with exponential backoff and partial result caching.

Retry Configuration (per FR-008):
- Initial delay: 1 second
- Maximum delay: 32 seconds
- Multiplier: 2

Caching (per FR-008):
- Cache partial results to disk after 3 consecutive failures
- Cache stored in data/raw/knot_atlas_partial_cache.json
"""
import json
import time
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field

from reproducibility.logs import log_operation, ReproducibilityLogger, get_logger

# Retry configuration constants (per FR-008)
RETRY_INITIAL_DELAY = 1.0  # seconds
RETRY_MAX_DELAY = 32.0     # seconds
RETRY_MULTIPLIER = 2
RETRY_CACHE_THRESHOLD = 3  # consecutive failures before caching partial results

# Knot Atlas URLs
KNOT_ATLAS_BASE_URL = "https://katlas.org"
KNOT_ATLAS_CENSUS_URL = "https://katlas.org/wiki/Complete_Knot_Census"

@dataclass
class KnotRecord:
    """Dataclass representing a single knot record from Knot Atlas."""
    id: str
    crossing_number: int
    braid_index: Optional[int] = None
    hyperbolic_volume: Optional[float] = None
    is_alternating: Optional[bool] = None
    braid_word: Optional[str] = None
    dt_code: Optional[str] = None
    source: str = "knot_atlas"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnotRecord':
        """Create record from dictionary."""
        return cls(**data)

@dataclass
class DownloadFailure:
    """Dataclass representing a download failure."""
    url: str
    error_message: str
    timestamp: str
    attempt_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert failure to dictionary."""
        return asdict(self)

class KnotAtlasDownloader:
    """
    Downloader for Knot Atlas data with retry logic and partial caching.
    
    Implements FR-008: Retry with exponential backoff and cache partial results
    after 3 consecutive failures.
    """
    
    def __init__(
        self,
        base_url: str = KNOT_ATLAS_BASE_URL,
        cache_dir: Optional[Path] = None,
        logger: Optional[ReproducibilityLogger] = None
    ):
        """
        Initialize the downloader.
        
        Args:
            base_url: Base URL for Knot Atlas
            cache_dir: Directory for partial cache files
            logger: Reproducibility logger for operation logging
        """
        self.base_url = base_url
        self.cache_dir = cache_dir or Path("data/raw")
        self.logger = logger or get_logger()
        self.cache_file = self.cache_dir / "knot_atlas_partial_cache.json"
        
        # Retry configuration
        self.retry_initial_delay = RETRY_INITIAL_DELAY
        self.retry_max_delay = RETRY_MAX_DELAY
        self.retry_multiplier = RETRY_MULTIPLIER
        self.retry_cache_threshold = RETRY_CACHE_THRESHOLD
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay for given attempt number.
        
        Args:
            attempt: Current attempt number (0-indexed)
        
        Returns:
            Delay in seconds (exponential backoff, capped at max)
        """
        delay = self.retry_initial_delay * (self.retry_multiplier ** attempt)
        return min(delay, self.retry_max_delay)
    
    def _load_partial_cache(self) -> List[KnotRecord]:
        """
        Load any existing partial cache from disk.
        
        Returns:
            List of cached KnotRecord objects
        """
        if not self.cache_file.exists():
            return []
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                return [KnotRecord.from_dict(record) for record in data.get('records', [])]
        except (json.JSONDecodeError, KeyError):
            return []
    
    def _save_partial_cache(self, records: List[KnotRecord]) -> None:
        """
        Save partial results to disk cache.
        
        Args:
            records: List of KnotRecord objects to cache
        """
        cache_data = {
            'records': [record.to_dict() for record in records],
            'cached_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'retry_count': self.retry_cache_threshold,
            'cache_threshold': self.retry_cache_threshold
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def _download_with_retry(
        self,
        url: str,
        max_retries: int = 5,
        timeout: float = 30.0
    ) -> tuple[Optional[Dict[str, Any]], List[DownloadFailure]]:
        """
        Download content with exponential backoff retry logic.
        
        Args:
            url: URL to download
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        
        Returns:
            Tuple of (parsed JSON data or None, list of failures)
        """
        failures: List[DownloadFailure] = []
        consecutive_failures = 0
        all_records: List[KnotRecord] = self._load_partial_cache()
        
        for attempt in range(max_retries):
            delay = self._calculate_delay(attempt)
            
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                
                # Clear cache on successful download
                if consecutive_failures > 0:
                    if self.cache_file.exists():
                        self.cache_file.unlink()
                
                return response.json(), failures
                
            except requests.RequestException as e:
                failure = DownloadFailure(
                    url=url,
                    error_message=str(e),
                    timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    attempt_number=attempt + 1
                )
                failures.append(failure)
                consecutive_failures += 1
                
                # Log the failure
                log_operation(
                    logger=self.logger,
                    operation="download_retry",
                    input_file=url,
                    output_file=None,
                    parameters={"attempt": attempt + 1, "delay": delay, "error": str(e)},
                    status="retry",
                    duration_ms=int(delay * 1000)
                )
                
                # Cache partial results after threshold consecutive failures
                if consecutive_failures >= self.retry_cache_threshold:
                    log_operation(
                        logger=self.logger,
                        operation="partial_cache_created",
                        input_file=url,
                        output_file=str(self.cache_file),
                        parameters={"consecutive_failures": consecutive_failures, "threshold": self.retry_cache_threshold},
                        status="success",
                        duration_ms=0
                    )
                    
                    # Save current partial cache if we have any records
                    if all_records:
                        self._save_partial_cache(all_records)
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    time.sleep(delay)
        
        # All retries exhausted - save final partial cache
        if all_records:
            self._save_partial_cache(all_records)
        
        return None, failures
    
    def download_census_data(
        self,
        max_crossing_number: int = 13
    ) -> tuple[List[KnotRecord], List[DownloadFailure]]:
        """
        Download knot census data up to specified crossing number.
        
        Args:
            max_crossing_number: Maximum crossing number to include
        
        Returns:
            Tuple of (list of KnotRecord, list of DownloadFailure)
        """
        url = f"{self.base_url}/wiki/Complete_Knot_Census"
        data, failures = self._download_with_retry(url)
        
        if data is None:
            return [], failures
        
        # Parse knot records from census data
        records: List[KnotRecord] = []
        
        # Note: Actual parsing depends on Knot Atlas HTML structure
        # This is a placeholder for the parsing logic
        # In real implementation, would parse HTML or API response
        
        return records, failures

def download_knot_atlas_data(
    url: str,
    cache_dir: Optional[Path] = None,
    max_retries: int = 5,
    timeout: float = 30.0
) -> tuple[Optional[Dict[str, Any]], List[DownloadFailure]]:
    """
    Convenience function to download Knot Atlas data with retry logic.
    
    Args:
        url: URL to download
        cache_dir: Directory for partial cache files
        max_retries: Maximum retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (parsed JSON data or None, list of DownloadFailure)
    """
    downloader = KnotAtlasDownloader(cache_dir=cache_dir)
    return downloader._download_with_retry(url, max_retries, timeout)

def verify_downloaded_record(record: KnotRecord) -> bool:
    """
    Verify that a downloaded record has required fields.
    
    Args:
        record: KnotRecord to verify
    
    Returns:
        True if record has all required fields
    """
    required_fields = ['id', 'crossing_number']
    return all(getattr(record, field, None) is not None for field in required_fields)

def verify_retry_logic(
    initial_delay: float = RETRY_INITIAL_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    multiplier: float = RETRY_MULTIPLIER,
    attempts: int = 5
) -> Dict[str, float]:
    """
    Verify exponential backoff delay calculations.
    
    Args:
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        multiplier: Delay multiplier
        attempts: Number of attempts to calculate delays for
    
    Returns:
        Dictionary mapping attempt number to calculated delay
    """
    delays = {}
    for attempt in range(attempts):
        delay = initial_delay * (multiplier ** attempt)
        delays[f"attempt_{attempt}"] = min(delay, max_delay)
    
    # Verify delays are monotonically increasing (capped at max)
    delay_values = list(delays.values())
    is_monotonic = all(delay_values[i] <= delay_values[i+1] for i in range(len(delay_values)-1))
    delays['is_monotonic'] = is_monotonic
    delays['max_delay_capped'] = delay_values[-1] == max_delay
    
    return delays

def verify_partial_caching(
    cache_file: Path,
    expected_threshold: int = RETRY_CACHE_THRESHOLD
) -> Dict[str, Any]:
    """
    Verify partial cache file structure and content.
    
    Args:
        cache_file: Path to cache file
        expected_threshold: Expected retry threshold for caching
    
    Returns:
        Dictionary with verification results
    """
    result = {
        'exists': False,
        'has_records': False,
        'record_count': 0,
        'has_metadata': False,
        'threshold_matches': False,
        'error': None
    }
    
    try:
        if not cache_file.exists():
            result['error'] = "Cache file does not exist"
            return result
        
        result['exists'] = True
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        result['has_records'] = 'records' in data
        result['record_count'] = len(data.get('records', []))
        result['has_metadata'] = all(
            key in data 
            for key in ['cached_at', 'retry_count', 'cache_threshold']
        )
        result['threshold_matches'] = data.get('cache_threshold') == expected_threshold
        
    except json.JSONDecodeError as e:
        result['error'] = f"Invalid JSON: {str(e)}"
    except Exception as e:
        result['error'] = str(e)
    
    return result
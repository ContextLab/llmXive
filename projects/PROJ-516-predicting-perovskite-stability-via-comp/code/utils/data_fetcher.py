"""
T006b: Data fetcher with retry logic.
"""
import time
import logging
import yaml
from pathlib import Path
from typing import Optional, Callable, Any, Dict, Tuple
from urllib.error import URLError, HTTPError
import urllib.request
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FetchError(Exception):
    pass

def load_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        return {"delay_multiplier": 1.0, "retry_delays": [1.0, 2.0, 4.0]}
    with open(config_path) as f:
        return yaml.safe_load(f)

def fetch_with_retry(url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[Any]:
    config = load_config()
    retry_delays = config.get("retry_delays", [1.0, 2.0, 4.0])
    multiplier = config.get("delay_multiplier", 1.0)

    query_string = ""
    if params:
        query_string = "?" + urllib.parse.urlencode(params)
    
    full_url = url + query_string

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(full_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response
        except (URLError, HTTPError, TimeoutError) as e:
            if attempt < max_retries - 1:
                delay = retry_delays[attempt] * multiplier
                logger.warning(f"Fetch failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Fetch failed after {max_retries} retries: {e}")
                return None
    return None

def fetch_text_with_retry(url: str, params: Optional[Dict] = None) -> Optional[str]:
    response = fetch_with_retry(url, params)
    if response:
        return response.read().decode('utf-8')
    return None

def extract_and_validate_instrumentation(data: Dict) -> Dict:
    # Placeholder for instrumentation extraction
    return data

def main():
    logger.info("Data fetcher module loaded.")

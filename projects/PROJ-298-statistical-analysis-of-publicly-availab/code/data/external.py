import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import requests
from datetime import datetime, timedelta

# Constants
CACHE_DIR = Path("data/cache")
CACHE_FILE = CACHE_DIR / "github_api_cache.json"
NPM_CACHE_FILE = CACHE_DIR / "npm_api_cache.json"
TTL_HOURS = 24
RATE_LIMIT_DELAY = 1.0  # seconds between requests to respect rate limits

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_cache_dir():
    """Ensure the cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR

def get_cache_key(url: str, params: Optional[Dict] = None) -> str:
    """Generate a unique cache key for a request."""
    key_data = f"{url}:{json.dumps(params, sort_keys=True) if params else ''}"
    return hashlib.md5(key_data.encode()).hexdigest()

def load_cache(cache_path: Path) -> Dict:
    """Load cache from disk, returning empty dict if not found or invalid."""
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load cache from {cache_path}: {e}")
        return {}

def save_cache(cache_path: Path, data: Dict):
    """Save cache to disk."""
    ensure_cache_dir()
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def is_cache_valid(cache_entry: Dict) -> bool:
    """Check if a cache entry is still valid (within TTL)."""
    if 'timestamp' not in cache_entry:
        return False
    try:
        timestamp = datetime.fromisoformat(cache_entry['timestamp'])
        expiry = timestamp + timedelta(hours=TTL_HOURS)
        return datetime.now() < expiry
    except (ValueError, TypeError):
        return False

def get_from_cache(cache: Dict, key: str) -> Optional[Dict]:
    """Retrieve data from cache if valid."""
    if key in cache:
        entry = cache[key]
        if is_cache_valid(entry):
            logger.info(f"Cache hit for key: {key}")
            return entry.get('data')
        else:
            logger.info(f"Cache expired for key: {key}, removing.")
            del cache[key]
    return None

def set_cache(cache: Dict, key: str, data: Any):
    """Store data in cache with current timestamp."""
    cache[key] = {
        'timestamp': datetime.now().isoformat(),
        'data': data
    }

def rate_limit_wait():
    """Enforce rate limiting delay between requests."""
    time.sleep(RATE_LIMIT_DELAY)

def fetch_github_stars(tag: str) -> Optional[Dict]:
    """
    Fetch GitHub star counts for a given tag using GitHub Search API.
    Uses caching and rate limiting.
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"topic:{tag}",
        "sort": "stars",
        "order": "desc",
        "per_page": 5
    }
    
    cache_key = get_cache_key(url, params)
    
    # Try cache first
    cache = load_cache(CACHE_FILE)
    cached_data = get_from_cache(cache, cache_key)
    if cached_data is not None:
        return cached_data
    
    try:
        rate_limit_wait()
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Process and cache
        result = {
            "tag": tag,
            "total_count": data.get("total_count", 0),
            "items": [
                {
                    "name": item["full_name"],
                    "stars": item["stargazers_count"],
                    "url": item["html_url"]
                }
                for item in data.get("items", [])
            ]
        }
        
        set_cache(cache, cache_key, result)
        save_cache(CACHE_FILE, cache)
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"GitHub API request failed for tag '{tag}': {e}")
        return None

def fetch_npm_downloads(tag: str) -> Optional[Dict]:
    """
    Fetch NPM download counts for a given tag using NPM Search API.
    Uses caching and rate limiting.
    """
    # NPM Search API for packages
    search_url = "https://registry.npmjs.org/-/v1/search"
    search_params = {
        "text": f"keywords:{tag}",
        "size": 5
    }
    
    search_key = get_cache_key(search_url, search_params)
    cache = load_cache(NPM_CACHE_FILE)
    
    # Try cache first for search
    cached_search = get_from_cache(cache, search_key)
    if cached_search is None:
        try:
            rate_limit_wait()
            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            cached_search = {
                "tag": tag,
                "packages": [
                    pkg["package"]["name"]
                    for pkg in search_data.get("objects", [])
                ]
            }
            set_cache(cache, search_key, cached_search)
            save_cache(NPM_CACHE_FILE, cache)
        except requests.exceptions.RequestException as e:
            logger.error(f"NPM search API request failed for tag '{tag}': {e}")
            return None
    
    # Fetch download counts for found packages
    download_results = []
    for pkg_name in cached_search.get("packages", []):
        download_url = f"https://api.npmjs.org/downloads/point/last-month/{pkg_name}"
        dl_key = get_cache_key(download_url)
        
        cached_dl = get_from_cache(cache, dl_key)
        if cached_dl is None:
            try:
                rate_limit_wait()
                dl_response = requests.get(download_url, timeout=10)
                if dl_response.status_code == 200:
                    dl_data = dl_response.json()
                    cached_dl = dl_data.get("downloads", 0)
                else:
                    cached_dl = 0
                set_cache(cache, dl_key, cached_dl)
                save_cache(NPM_CACHE_FILE, cache)
            except requests.exceptions.RequestException:
                cached_dl = 0
        
        download_results.append({
            "name": pkg_name,
            "downloads": cached_dl
        })
    
    return {
        "tag": tag,
        "packages": download_results
    }

def load_trend_results() -> List[str]:
    """Load the top 50 tags from trend results."""
    trend_path = Path("data/processed/trend_results.json")
    if not trend_path.exists():
        logger.error(f"Trend results file not found: {trend_path}")
        return []
    
    try:
        with open(trend_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Assuming structure: {"results": [{"tag": "name", ...}, ...]}
            if "results" in data:
                return [item["tag"] for item in data["results"]]
            elif isinstance(data, list):
                return [item.get("tag") for item in data if isinstance(item, dict)]
            return []
    except (json.JSONDecodeError, IOError, KeyError) as e:
        logger.error(f"Failed to load trend results: {e}")
        return []

def fetch_external_metrics(tags: List[str]) -> Dict:
    """
    Fetch external metrics (GitHub stars, NPM downloads) for a list of tags.
    Implements rate limiting and caching as per T051.
    """
    if not tags:
        logger.warning("No tags provided for external metrics fetch.")
        return {"tags": []}
    
    results = []
    errors = []
    
    for tag in tags:
        logger.info(f"Fetching metrics for tag: {tag}")
        
        # Fetch GitHub data
        github_data = fetch_github_stars(tag)
        if github_data is None:
            github_data = {"tag": tag, "error": "GitHub API failed"}
            errors.append({"tag": tag, "source": "github", "error": "API failed"})
        
        # Fetch NPM data
        npm_data = fetch_npm_downloads(tag)
        if npm_data is None:
            npm_data = {"tag": tag, "error": "NPM API failed"}
            errors.append({"tag": tag, "source": "npm", "error": "API failed"})
        
        results.append({
            "tag": tag,
            "github": github_data,
            "npm": npm_data
        })
    
    output = {
        "tags": results,
        "fetch_errors": errors,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save raw metrics to file as required by T039/T051
    output_path = Path("data/processed/external_metrics.json")
    ensure_cache_dir() # Ensure data/processed exists via ensure_cache_dir logic or separate
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"External metrics saved to {output_path}")
    return output

def save_external_metrics(metrics: Dict, path: Optional[Path] = None):
    """Save external metrics to a specified path."""
    if path is None:
        path = Path("data/processed/external_metrics.json")
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main entry point for fetching external metrics."""
    logger.info("Starting external metrics fetch with caching and rate limiting.")
    
    # Load tags from trend results
    tags = load_trend_results()
    if not tags:
        logger.warning("No tags found in trend results. Exiting.")
        return
    
    logger.info(f"Found {len(tags)} tags to process.")
    
    # Fetch metrics
    metrics = fetch_external_metrics(tags)
    
    logger.info(f"Completed fetching metrics for {len(metrics.get('tags', []))} tags.")
    if metrics.get('fetch_errors'):
        logger.warning(f"Encountered {len(metrics['fetch_errors'])} API errors.")

if __name__ == "__main__":
    main()
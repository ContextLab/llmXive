"""
Fetch raw speedrun data from speedrun.com API with checkpointing support.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path

# Configuration
CONFIG_PATH = "code/config.yaml"
API_BASE_URL = "https://www.speedrun.com/api/v1"
TIMEOUT_PER_REQUEST = 30
RETRY_COUNT = 3
RETRY_DELAY = 2

def load_config():
    """Load configuration from YAML file."""
    import yaml
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def setup_logging():
    """Setup logging with file and console handlers."""
    log_dir = Path("code/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "fetch_data.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_cache_key(game_id):
    """Generate a cache key for a game."""
    return f"{game_id}_raw"

def load_from_cache(cache_dir, game_id):
    """Load raw data from cache if available."""
    cache_file = Path(cache_dir) / f"{game_id}_raw.json"
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None

def save_to_cache(cache_dir, game_id, data):
    """Save raw data to cache."""
    cache_file = Path(cache_dir) / f"{game_id}_raw.json"
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)

def fetch_page(url, logger):
    """Fetch a single page from the API with retry logic."""
    for attempt in range(RETRY_COUNT):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'SpeedrunStats/1.0'})
            with urllib.request.urlopen(req, timeout=TIMEOUT_PER_REQUEST) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            logger.warning(f"HTTP Error {e.code} for {url} (attempt {attempt+1})")
            if e.code == 429:  # Rate limit
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise
        except urllib.error.URLError as e:
            logger.warning(f"URL Error for {url} (attempt {attempt+1}): {e.reason}")
            time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            logger.warning(f"Unexpected error for {url} (attempt {attempt+1}): {e}")
            time.sleep(RETRY_DELAY * (attempt + 1))
    
    raise RuntimeError(f"Failed to fetch {url} after {RETRY_COUNT} attempts")

def fetch_game_runs(game_id, logger, max_pages=100):
    """Fetch all runs for a specific game with pagination."""
    runs = []
    page = 1
    
    while page <= max_pages:
        url = f"{API_BASE_URL}/games/{game_id}/runs?per-page=100&order=asc&page={page}"
        logger.info(f"Fetching page {page} for game {game_id}")
        
        response = fetch_page(url, logger)
        data = response.get('data', [])
        
        if not data:
            break
        
        runs.extend(data)
        
        # Check for pagination
        pagination = response.get('pagination', {})
        if not pagination.get('has_next', False):
            break
        
        page += 1
        time.sleep(0.5)  # Be respectful to the API
    
    return runs

def save_raw_data(data_dir, game_id, runs):
    """Save raw data to disk."""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    
    output_file = data_path / f"{game_id}_raw.json"
    with open(output_file, 'w') as f:
        json.dump(runs, f, indent=2)
    
    logger.info(f"Saved {len(runs)} runs for {game_id} to {output_file}")

def main():
    """Main entry point with checkpointing support."""
    logger = setup_logging()
    logger.info("Starting data fetch with checkpointing")
    
    config = load_config()
    games = config.get('games', [])
    min_sample_size = config.get('min_sample_size', 100)
    
    raw_data_dir = "data/raw"
    checkpoint_dir = "data/checkpoints"
    ensure_checkpoint_dir(checkpoint_dir)
    
    checkpoint_path = get_checkpoint_path(checkpoint_dir, "fetch_data")
    checkpoint = load_checkpoint(checkpoint_path)
    
    # Determine starting point
    if checkpoint and 'completed_games' in checkpoint:
        completed_games = set(checkpoint['completed_games'])
        games_to_fetch = [g for g in games if g not in completed_games]
        logger.info(f"Resuming from checkpoint. Completed: {completed_games}, Remaining: {games_to_fetch}")
    else:
        completed_games = set()
        games_to_fetch = games
        logger.info("Starting fresh. Games to fetch: {games_to_fetch}")
    
    # Process each game
    for game_id in games_to_fetch:
        logger.info(f"Processing game: {game_id}")
        
        try:
            # Check cache first
            cached_data = load_from_cache(raw_data_dir, game_id)
            if cached_data:
                logger.info(f"Loaded {game_id} from cache")
                runs = cached_data
            else:
                # Fetch from API
                runs = fetch_game_runs(game_id, logger)
                save_to_cache(raw_data_dir, game_id, runs)
            
            # Save to raw data directory
            save_raw_data(raw_data_dir, game_id, runs)
            
            # Update checkpoint
            completed_games.add(game_id)
            checkpoint = {
                'completed_games': list(completed_games),
                'total_games': len(games),
                'last_updated': time.time()
            }
            save_checkpoint(checkpoint_path, checkpoint)
            
            logger.info(f"Successfully fetched {len(runs)} runs for {game_id}")
            
        except Exception as e:
            logger.error(f"Failed to fetch {game_id}: {e}")
            raise
    
    logger.info(f"All games processed. Total completed: {len(completed_games)}/{len(games)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

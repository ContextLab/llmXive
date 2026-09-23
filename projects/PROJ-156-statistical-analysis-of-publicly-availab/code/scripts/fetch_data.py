import json
import os
import sys
import time
import urllib.request
import urllib.error
import logging
from pathlib import Path

# Import checkpoint utilities from sibling module
from scripts.utils.checkpoint import save_checkpoint, load_checkpoint, get_checkpoint_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/fetch_data.log')
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    # Simple YAML parser for basic key-value and list structures
    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('[') and value.endswith(']'):
                    # Parse list
                    items = value[1:-1].split(',')
                    config[key] = [item.strip().strip('"').strip("'") for item in items if item.strip()]
                else:
                    # Try to parse as number, else keep as string
                    try:
                        config[key] = int(value)
                    except ValueError:
                        try:
                            config[key] = float(value)
                        except ValueError:
                            config[key] = value.strip('"').strip("'")
    return config

def fetch_game_runs(game_id, page_size=100, max_pages=10):
    """
    Fetch runs for a specific game from speedrun.com API.
    
    Args:
        game_id: The game identifier (e.g., 'super-mario-64')
        page_size: Number of runs per page
        max_pages: Maximum number of pages to fetch
        
    Returns:
        List of run records
    """
    base_url = f"https://www.speedrun.com/api/v1/games/{game_id}/runs"
    runs = []
    page = 1
    
    logger.info(f"Starting fetch for game: {game_id}")
    
    while page <= max_pages:
        url = f"{base_url}?top=1&per-page={page_size}&page={page}"
        try:
            logger.debug(f"Fetching page {page} for {game_id}")
            req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-scraper/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if 'data' not in data:
                logger.warning(f"No data found in response for page {page}")
                break
            
            page_runs = data['data']
            if not page_runs:
                logger.info(f"No more runs found on page {page}")
                break
            
            runs.extend(page_runs)
            logger.info(f"Fetched {len(page_runs)} runs (total: {len(runs)}) for {game_id}")
            
            # Check if there are more pages
            pagination = data.get('pagination', {})
            if pagination.get('next') is None:
                logger.info(f"Reached last page for {game_id}")
                break
            
            page += 1
            time.sleep(1)  # Rate limiting
            
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code} fetching {game_id} page {page}: {e.reason}")
            if e.code == 429:  # Too Many Requests
                logger.warning("Rate limit hit, waiting 60 seconds")
                time.sleep(60)
                continue
            break
        except urllib.error.URLError as e:
            logger.error(f"URL Error fetching {game_id}: {e.reason}")
            break
        except Exception as e:
            logger.error(f"Unexpected error fetching {game_id} page {page}: {str(e)}")
            break
    
    logger.info(f"Completed fetch for {game_id}: {len(runs)} total runs")
    return runs

def save_raw_data(game_id, runs, output_dir="data/raw"):
    """
    Save raw run data to JSON file.
    
    Args:
        game_id: The game identifier
        runs: List of run records
        output_dir: Directory to save the file
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{game_id}_raw.json"
    filepath = os.path.join(output_dir, filename)
    
    logger.info(f"Saving {len(runs)} runs to {filepath}")
    try:
        with open(filepath, 'w') as f:
            json.dump(runs, f, indent=2)
        logger.info(f"Successfully saved data to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save data: {str(e)}")
        return False

def main():
    """Main entry point for data fetching."""
    logger.info("Starting data acquisition process")
    
    try:
        config = load_config()
        games = config.get('games', [])
        checkpoint_enabled = config.get('checkpoint_enabled', True)
        
        if not games:
            logger.error("No games configured in config.yaml")
            sys.exit(1)
        
        logger.info(f"Processing {len(games)} games: {games}")
        
        for game_id in games:
            logger.info(f"Processing game: {game_id}")
            
            # Load checkpoint if exists
            if checkpoint_enabled:
                checkpoint_path = get_checkpoint_path("fetch", game_id)
                if os.path.exists(checkpoint_path):
                    logger.info(f"Resuming from checkpoint: {checkpoint_path}")
                    state = load_checkpoint(checkpoint_path)
                    if state.get('status') == 'completed':
                        logger.info(f"Game {game_id} already completed, skipping")
                        continue
            
            # Fetch runs
            runs = fetch_game_runs(game_id)
            
            if not runs:
                logger.warning(f"No runs fetched for {game_id}, skipping save")
                continue
            
            # Save raw data
            success = save_raw_data(game_id, runs)
            
            if checkpoint_enabled:
                # Save checkpoint
                save_checkpoint("fetch", game_id, {
                    'status': 'completed' if success else 'failed',
                    'runs_count': len(runs),
                    'timestamp': time.time()
                })
            
            if not success:
                logger.error(f"Failed to save data for {game_id}, stopping")
                sys.exit(1)
            
            logger.info(f"Successfully processed {game_id}")
        
        logger.info("Data acquisition completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

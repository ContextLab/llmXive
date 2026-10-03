import json
import os
import sys
import time
import urllib.request
import urllib.error
import logging
import yaml
from pathlib import Path

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code/logs/fetch_data.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    config_path = Path('code/config.yaml')
    if not config_path.exists():
        logger.error(f"Configuration file not found at {config_path}")
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        if 'games' not in config or not config['games']:
            logger.error("No games specified in config.yaml")
            raise ValueError("No games specified in config.yaml")
        logger.info(f"Loaded config with {len(config['games'])} games")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config: {e}")
        raise

def parse_value(key, config):
    value = config.get(key)
    if value is None:
        logger.warning(f"Key '{key}' not found in config, using default")
        return None
    return value

def get_cache_key(game_id, page):
    return f"{game_id}_page_{page}"

def load_from_cache(cache_dir, game_id, page):
    cache_path = Path(cache_dir) / f"{get_cache_key(game_id, page)}.json"
    if cache_path.exists():
        logger.info(f"Loading from cache: {cache_path}")
        with open(cache_path, 'r') as f:
            return json.load(f)
    return None

def save_to_cache(cache_dir, game_id, page, data):
    cache_path = Path(cache_dir) / f"{get_cache_key(game_id, page)}.json"
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(data, f)
    logger.debug(f"Saved to cache: {cache_path}")

def fetch_page(game_id, page, retries=3):
    base_url = "https://speedrun.com/api/v1/runs"
    params = f"?game={game_id}&top=100&offset={page * 100}"
    url = base_url + params
    
    for attempt in range(retries):
        try:
            logger.info(f"Fetching page {page} for {game_id} (attempt {attempt + 1}/{retries})")
            req = urllib.request.Request(url, headers={'User-Agent': 'SpeedrunAnalysis/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                logger.info(f"Successfully fetched page {page} for {game_id}")
                return data
        except urllib.error.URLError as e:
            logger.warning(f"URL Error fetching {url}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise
    
    logger.error(f"Failed to fetch page {page} for {game_id} after {retries} attempts")
    raise Exception(f"Failed to fetch page {page} for {game_id}")

def fetch_game_runs(game_id, cache_dir='data/raw/cache'):
    all_runs = []
    page = 0
    max_pages = 10  # Safety limit for demo, adjust based on real needs
    
    while page < max_pages:
        data = load_from_cache(cache_dir, game_id, page)
        if data is None:
            data = fetch_page(game_id, page)
            save_to_cache(cache_dir, game_id, page, data)
        
        runs = data.get('data', [])
        if not runs:
            logger.info(f"No more runs found for {game_id} at page {page}")
            break
        
        all_runs.extend(runs)
        logger.info(f"Fetched {len(runs)} runs for {game_id} (total: {len(all_runs)})")
        page += 1
    
    return all_runs

def save_raw_data(data, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f)
    logger.info(f"Saved raw data to {output_path}")

def main():
    logger.info("Starting data acquisition pipeline")
    config = load_config()
    games = config['games']
    min_sample_size = parse_value('min_sample_size', config) or 100
    checkpoint_dir = Path('data/checkpoints')
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_file = checkpoint_dir / 'fetch_checkpoint.json'
    completed_games = []
    
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
            completed_games = checkpoint.get('completed_games', [])
            logger.info(f"Resuming from checkpoint: {len(completed_games)} games completed")
    
    for game_id in games:
        if game_id in completed_games:
            logger.info(f"Skipping {game_id} (already completed)")
            continue
        
        try:
            logger.info(f"Processing game: {game_id}")
            runs = fetch_game_runs(game_id)
            
            if len(runs) < min_sample_size:
                logger.warning(f"Game {game_id} has only {len(runs)} runs (< {min_sample_size}). Skipping.")
                continue
            
            output_path = f"data/raw/{game_id}_raw.json"
            save_raw_data(runs, output_path)
            
            completed_games.append(game_id)
            with open(checkpoint_file, 'w') as f:
                json.dump({'completed_games': completed_games}, f)
            
            logger.info(f"Successfully processed {game_id} with {len(runs)} runs")
        except Exception as e:
            logger.error(f"Failed to process {game_id}: {e}")
            raise
    
    logger.info("Data acquisition pipeline completed successfully")

if __name__ == '__main__':
    main()

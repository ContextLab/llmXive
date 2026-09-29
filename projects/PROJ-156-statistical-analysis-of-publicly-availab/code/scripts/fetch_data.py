import json
import os
import sys
import time
import urllib.request
import urllib.error
import logging
from pathlib import Path

# Import checkpoint utilities
from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from code/config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
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
                # Handle list format [item1, item2]
                if value.startswith('[') and value.endswith(']'):
                    items = value[1:-1].split(',')
                    config[key] = [item.strip().strip('"').strip("'") for item in items]
                else:
                    # Try to convert to appropriate type
                    if value.isdigit():
                        config[key] = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        config[key] = float(value)
                    elif value.lower() == 'true':
                        config[key] = True
                    elif value.lower() == 'false':
                        config[key] = False
                    else:
                        config[key] = value.strip('"').strip("'")
    return config

def fetch_game_runs(game_id, retry_count=3):
    """Fetch runs for a specific game from speedrun.com API"""
    base_url = "https://www.speedrun.com/api/v1/runs"
    game_url = f"{base_url}?game={game_id}&embed=category,platform,region"
    
    runs = []
    next_url = game_url
    
    attempts = 0
    while next_url and attempts < retry_count:
        try:
            logger.info(f"Fetching data for {game_id} from {next_url}")
            req = urllib.request.Request(
                next_url,
                headers={'User-Agent': 'llmXive-Speedrun-Analysis/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Extract runs
                runs.extend(data.get('data', []))
                
                # Handle pagination
                pagination = data.get('pagination', {})
                if pagination.get('next'):
                    next_url = pagination['next']
                else:
                    next_url = None
                    
            # Respect API rate limits
            time.sleep(1)
            
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code} for {game_id}: {e.reason}")
            attempts += 1
            time.sleep(2 ** attempts)  # Exponential backoff
            continue
        except urllib.error.URLError as e:
            logger.error(f"URL Error for {game_id}: {e.reason}")
            attempts += 1
            time.sleep(2 ** attempts)
            continue
        except Exception as e:
            logger.error(f"Unexpected error fetching {game_id}: {e}")
            raise
    
    if not runs:
        logger.warning(f"No runs found for game: {game_id}")
    
    return runs

def save_raw_data(game_id, runs):
    """Save raw run data to data/raw/"""
    raw_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = raw_dir / f"{game_id}_runs.json"
    with open(output_path, 'w') as f:
        json.dump(runs, f, indent=2)
    
    logger.info(f"Saved {len(runs)} runs for {game_id} to {output_path}")
    return output_path

def main():
    """Main execution function with checkpoint support"""
    config = load_config()
    games = config.get('games', [])
    
    if not games:
        logger.error("No games specified in config.yaml")
        sys.exit(1)
    
    # Initialize checkpoint
    checkpoint_dir = ensure_checkpoint_dir()
    checkpoint_file = get_checkpoint_path("fetch_data")
    
    # Load checkpoint state
    processed_games = []
    if os.path.exists(checkpoint_file):
        checkpoint_data = load_checkpoint(checkpoint_file)
        processed_games = checkpoint_data.get('processed_games', [])
        logger.info(f"Resuming from checkpoint. Already processed: {processed_games}")
    
    # Process games
    for game_id in games:
        if game_id in processed_games:
            logger.info(f"Skipping already processed game: {game_id}")
            continue
        
        logger.info(f"Processing game: {game_id}")
        
        try:
            # Fetch runs
            runs = fetch_game_runs(game_id)
            
            # Save raw data
            save_raw_data(game_id, runs)
            
            # Update processed games list
            processed_games.append(game_id)
            
            # Save checkpoint after each game
            save_checkpoint(checkpoint_file, {
                'processed_games': processed_games,
                'timestamp': time.time()
            })
            
            logger.info(f"Successfully processed {game_id}")
            
        except Exception as e:
            logger.error(f"Failed to process {game_id}: {e}")
            # Don't mark as processed, will retry next run
            raise
    
    logger.info("All games processed successfully")
    # Clean up checkpoint on successful completion
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

if __name__ == "__main__":
    main()

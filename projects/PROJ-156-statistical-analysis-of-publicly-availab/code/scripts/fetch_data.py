import json
import os
import sys
import time
import urllib.request
import urllib.error
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.checkpoint import save_checkpoint, load_checkpoint, ensure_checkpoint_dir
from scripts.load_game_metadata import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'fetch_data.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

SPEEDRUN_API_BASE = "https://www.speedrun.com/api/v1"
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # seconds

def fetch_game_runs(game_id: str, max_runs: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch runs for a specific game from speedrun.com API with pagination.
    
    Args:
        game_id: The game identifier (e.g., 'super-mario-64')
        max_runs: Maximum number of runs to fetch
        
    Returns:
        List of run records
    """
    runs = []
    uri = f"{SPEEDRUN_API_BASE}/runs"
    query_params = {
        'game': game_id,
        'top': 100,  # Fetch 100 at a time
        'order': 'asc'
    }
    
    page = 1
    while len(runs) < max_runs:
        params_str = '&'.join([f"{k}={v}" for k, v in query_params.items()])
        url = f"{uri}?{params_str}&offset={(page-1)*100}"
        
        try:
            logger.info(f"Fetching page {page} for game {game_id}: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-speedrun-analysis'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if 'data' not in data:
                logger.warning(f"No data found in response for game {game_id} at page {page}")
                break
                
            page_runs = data['data']
            if not page_runs:
                break
                
            runs.extend(page_runs)
            
            # Check if there are more pages
            pagination = data.get('pagination', {})
            if not pagination.get('has_next', False):
                break
                
            page += 1
            time.sleep(1)  # Rate limiting
            
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code} fetching game {game_id}: {e.reason}")
            break
        except urllib.error.URLError as e:
            logger.error(f"URL Error fetching game {game_id}: {e.reason}")
            break
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for game {game_id}: {e}")
            break
        except Exception as e:
            logger.error(f"Unexpected error fetching game {game_id}: {e}")
            break
            
    return runs[:max_runs]

def save_raw_data(game_id: str, runs: List[Dict[str, Any]], output_dir: Path) -> str:
    """
    Save raw run data to JSON file.
    
    Args:
        game_id: The game identifier
        runs: List of run records
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{game_id}_raw.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(runs, f, indent=2)
        
    logger.info(f"Saved {len(runs)} runs for {game_id} to {filepath}")
    return str(filepath)

def main():
    """
    Main entry point for fetching speedrun data with checkpointing.
    """
    config = load_config()
    games = config.get('games', [])
    output_dir = project_root / 'data' / 'raw'
    checkpoint_dir = ensure_checkpoint_dir()
    
    logger.info(f"Starting data fetch for {len(games)} games")
    
    # Load checkpoint if exists
    checkpoint_path = checkpoint_dir / 'fetch_data_checkpoint.json'
    completed_games = []
    
    if checkpoint_path.exists():
        logger.info(f"Loading checkpoint from {checkpoint_path}")
        checkpoint_data = load_checkpoint(checkpoint_path)
        completed_games = checkpoint_data.get('completed_games', [])
        logger.info(f"Resuming from game: {completed_games[-1] if completed_games else 'start'}")
    
    for game_id in games:
        if game_id in completed_games:
            logger.info(f"Skipping already completed game: {game_id}")
            continue
            
        try:
            logger.info(f"Processing game: {game_id}")
            
            # Fetch runs
            runs = fetch_game_runs(game_id)
            
            if not runs:
                logger.warning(f"No runs found for game {game_id}, skipping")
                # Still mark as completed to avoid infinite retry
                completed_games.append(game_id)
                save_checkpoint(checkpoint_path, {
                    'completed_games': completed_games,
                    'last_updated': time.time()
                })
                continue
            
            # Save raw data
            save_raw_data(game_id, runs, output_dir)
            
            # Update checkpoint
            completed_games.append(game_id)
            save_checkpoint(checkpoint_path, {
                'completed_games': completed_games,
                'last_updated': time.time()
            })
            
            logger.info(f"Successfully processed game {game_id} ({len(runs)} runs)")
            
        except Exception as e:
            logger.error(f"Failed to process game {game_id}: {e}")
            # Don't mark as completed if failed, will retry next time
            raise
    
    logger.info("Data fetching completed successfully")
    
    # Clean up checkpoint on successful completion
    if checkpoint_path.exists():
        logger.info("Removing checkpoint file after successful completion")
        checkpoint_path.unlink()

if __name__ == '__main__':
    main()

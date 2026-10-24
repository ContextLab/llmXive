import json
import logging
import sys
import time
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Callable
import yaml

from llmxive_toolkit import paths, get_logger
from scripts.utils.pagination import paginate_api
from scripts.utils.checkpoint import save_checkpoint, load_checkpoint, get_checkpoint_path

def _setup_logger() -> logging.Logger:
    """Initialize the logger for the fetch script."""
    return get_logger(__name__)

def load_config() -> Dict[str, Any]:
    """
    Load code/config.yaml using PyYAML.
    Robust against leading indentation in some environment contexts.
    """
    config_path = paths.code("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        content = f.read()
        # Strip leading whitespace if the content looks like a block scalar
        if content.startswith(' ') or content.startswith('\t'):
            import textwrap
            content = textwrap.dedent(content)
        config = yaml.safe_load(content)
    
    if not isinstance(config, dict):
        raise ValueError("config.yaml must be a valid YAML mapping")
    return config

def _url_builder_factory(game_id: str, page_size: int = 200) -> Callable[[int], str]:
    """
    Returns a function that builds the API URL for a given page (1-based).
    The Speedrun.com API uses offset pagination: offset = (page-1) * page_size.
    """
    def builder(page: int) -> str:
        offset = (page - 1) * page_size
        # Example endpoint for runs; in a real scenario, this would match the specific API spec
        return f"https://www.speedrun.com/api/v1/games/{game_id}/runs?offset={offset}&limit={page_size}"
    return builder

def _fetch_page(url: str, logger: logging.Logger) -> Dict[str, Any]:
    """Fetch a single page from the Speedrun.com API."""
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        logger.error(f"Failed to fetch page {url}: {e}")
        raise

def fetch_game_runs(game_id: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Download all run records for a given game_id using the generic pagination helper.
    """
    url_builder = _url_builder_factory(game_id)
    # paginate_api handles the loop and sleep_seconds
    all_data = paginate_api(
        fetch_page_func=_fetch_page,
        url_builder=url_builder,
        logger=logger,
        max_pages=100,
        sleep_seconds=0.5
    )
    
    # The API usually returns a list of runs or a dict with a 'data' key
    if isinstance(all_data, dict) and 'data' in all_data:
        return all_data['data']
    return all_data if isinstance(all_data, list) else []

def save_raw_data(game_id: str, runs: List[Dict[str, Any]], base_dir: Path = None) -> Path:
    """Write the raw run payload for a single game to data/raw/<game_id>.json."""
    if base_dir is None:
        base_dir = paths.data("raw")
    
    output_path = base_dir / f"{game_id}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(runs, f, indent=2)
    return output_path

def _update_fetch_checkpoint(completed_games: List[str], checkpoint_path: Path) -> None:
    """Persist the list of successfully fetched games to the checkpoint file."""
    save_checkpoint({"completed_games": completed_games}, checkpoint_path)

def main() -> None:
    """Main entry point for data acquisition with checkpointing."""
    logger = _setup_logger()
    
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    games = config.get('games', [])
    if not games:
        logger.error("No games specified in config.yaml")
        sys.exit(1)

    # Resolve checkpoint path
    checkpoint_path = get_checkpoint_path("fetch_checkpoint.json")
    checkpoint = load_checkpoint(checkpoint_path)
    completed_games = checkpoint.get("completed_games", []) if checkpoint else []
    
    logger.info(f"Found {len(completed_games)} already completed games in checkpoint.")

    for game_id in games:
        if game_id in completed_games:
            logger.info(f"Skipping {game_id}, already downloaded.")
            continue
        
        logger.info(f"Fetching data for game: {game_id}...")
        try:
            runs = fetch_game_runs(game_id, logger)
            if not runs:
                logger.warning(f"No runs found for game {game_id}. Marking as completed (empty).")
            
            save_raw_data(game_id, runs)
            
            # Update progress
            completed_games.append(game_id)
            _update_fetch_checkpoint(completed_games, checkpoint_path)
            logger.info(f"Successfully downloaded and checkpointed {game_id}.")
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {game_id}: {e}")
            # We do not exit here to allow other games to be attempted, 
            # but the current game is not added to completed_games.
            continue

    logger.info("Data acquisition process completed.")

if __name__ == "__main__":
    main()

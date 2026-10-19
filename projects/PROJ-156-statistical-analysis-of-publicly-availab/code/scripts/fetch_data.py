"""
fetch_data.py

Fetch raw speedrun data from speedrun.com API with checkpointing support.
Refactored to use the reusable pagination helper ``paginate_api``.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
import logging
from pathlib import Path

# Ensure sibling modules can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.checkpoint import (
    ensure_checkpoint_dir,
    save_checkpoint,
    load_checkpoint,
    get_checkpoint_path,
)
from scripts.utils.pagination import paginate_api  # pagination helper

# Configuration constants
CONFIG_PATH = "code/config.yaml"
API_BASE_URL = "https://www.speedrun.com/api/v1"
TIMEOUT_PER_REQUEST = 30
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds between retries

def load_config():
    """Load configuration from the YAML file."""
    import yaml
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def setup_logging():
    """Configure a logger that writes to ``code/logs/fetch_data.log``."""
    log_dir = Path("code/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("fetch_data")
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers on repeated runs
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_dir / "fetch_data.log")
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Stream (stdout) handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)

    return logger

def get_cache_key(game_id):
    """Generate a simple cache key for a game."""
    return f"{game_id}_raw"

def load_from_cache(cache_dir, game_id):
    """Load raw data from a local cache if it exists."""
    cache_file = Path(cache_dir) / f"{game_id}_raw.json"
    if cache_file.is_file():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_to_cache(cache_dir, game_id, data):
    """Persist raw API data to a cache file."""
    cache_file = Path(cache_dir) / f"{game_id}_raw.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def fetch_page(url, logger):
    """Fetch a single API page with retry logic."""
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "SpeedrunStats/1.0"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_PER_REQUEST) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            logger.warning(f"HTTP error {e.code} for {url} (attempt {attempt})")
            if e.code == 429:  # rate‑limit
                time.sleep(RETRY_DELAY * attempt)
            else:
                raise
        except urllib.error.URLError as e:
            logger.warning(f"URL error for {url} (attempt {attempt}): {e.reason}")
            time.sleep(RETRY_DELAY * attempt)
        except Exception as e:
            logger.warning(f"Unexpected error for {url} (attempt {attempt}): {e}")
            time.sleep(RETRY_DELAY * attempt)

    raise RuntimeError(f"Failed to fetch {url} after {RETRY_COUNT} attempts")

def fetch_game_runs(game_id, logger, max_pages=100):
    """Fetch all runs for a game using the generic ``paginate_api`` helper."""
    # Build the URL for a given page number
    url_builder = lambda page: (
        f"{API_BASE_URL}/games/{game_id}/runs?"
        f"per-page=100&order=asc&page={page}"
    )
    # Delegate pagination to the helper
    return paginate_api(fetch_page, url_builder, logger, max_pages=max_pages)

def save_raw_data(data_dir, game_id, runs):
    """Write the raw JSON payload for a game to ``data/raw/{game_id}.json``."""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    output_file = data_path / f"{game_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(runs, f, indent=2)

    logging.getLogger("fetch_data").info(
        f"Saved {len(runs)} runs for {game_id} to {output_file}"
    )

def main():
    """Entry point – iterate over configured games, fetch data, checkpoint."""
    logger = setup_logging()
    logger.info("Starting data acquisition with checkpoint support")

    config = load_config()
    games = config.get("games", [])
    if not games:
        logger.error("No games specified in config.yaml")
        sys.exit(1)

    raw_data_dir = "data/raw"
    checkpoint_dir = "data/checkpoints"
    ensure_checkpoint_dir(checkpoint_dir)

    # Resolve checkpoint file path (e.g., data/checkpoints/fetch_data.json)
    checkpoint_path = get_checkpoint_path(checkpoint_dir, "fetch_data")
    checkpoint = load_checkpoint(checkpoint_path) or {}

    completed_games = set(checkpoint.get("completed_games", []))
    games_to_fetch = [g for g in games if g not in completed_games]

    logger.info(
        f"{len(completed_games)} games already completed; "
        f"{len(games_to_fetch)} remaining."
    )

    for game_id in games_to_fetch:
        logger.info(f"Fetching runs for game: {game_id}")

        try:
            # Attempt to load from local cache first
            cached = load_from_cache(raw_data_dir, game_id)
            if cached is not None:
                logger.info(f"Loaded cached data for {game_id}")
                runs = cached
            else:
                runs = fetch_game_runs(game_id, logger)
                # Cache the fresh result for potential future runs
                save_to_cache(raw_data_dir, game_id, runs)

            # Persist the raw JSON for downstream steps
            save_raw_data(raw_data_dir, game_id, runs)

            # Update checkpoint
            completed_games.add(game_id)
            checkpoint_state = {
                "completed_games": list(completed_games),
                "total_games": len(games),
                "last_updated": time.time(),
            }
            save_checkpoint(checkpoint_path, checkpoint_state)
            logger.info(f"Successfully processed {game_id}")

        except Exception as exc:
            logger.error(f"Failed to process {game_id}: {exc}")
            # Re‑raise so the CI run aborts – we want loud failure
            raise

    logger.info(
        f"All games processed. Completed {len(completed_games)}/{len(games)}."
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
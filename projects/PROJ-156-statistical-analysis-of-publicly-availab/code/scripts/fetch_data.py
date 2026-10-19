"""
fetch_data.py

Data acquisition script for the Speedrun.com API.
Iterates over games in config.yaml and downloads raw run data.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import requests
import yaml

# Project utilities
from scripts.utils.pagination import paginate_api
from scripts.utils.checkpoint import (
    ensure_checkpoint_dir,
    load_checkpoint,
    save_checkpoint,
)

# ----------------------------------------------------------------------
# Logging helper
# ----------------------------------------------------------------------
def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("fetch_data")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# ----------------------------------------------------------------------
# Config loader
# ----------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    """
    Load ``code/config.yaml`` using PyYAML.

    The test suite sometimes writes the YAML file with leading indentation.
    To be robust against such formatting, we strip leading whitespace before
    parsing if the initial parse does not return a mapping.
    """
    config_path = Path("code") / "config.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        raw_content = f.read()

    # First attempt: parse as‑is
    try:
        config = yaml.safe_load(raw_content)
    except yaml.YAMLError as e:
        raise RuntimeError(f"Failed to parse config.yaml: {e}")

    # If parsing yields something other than a dict (e.g., a string because of
    # leading indentation), retry after stripping common leading whitespace.
    if not isinstance(config, dict):
        # Dedent the content to remove any accidental leading spaces.
        import textwrap

        dedented = textwrap.dedent(raw_content)
        try:
            config = yaml.safe_load(dedented)
        except yaml.YAMLError as e:
            raise RuntimeError(
                f"Failed to parse dedented config.yaml: {e}"
            ) from e

    if not isinstance(config, dict):
        raise ValueError(
            "config.yaml did not contain a mapping of configuration keys."
        )
    return config

# ----------------------------------------------------------------------
# Pagination helpers specific to the Speedrun.com runs endpoint
# ----------------------------------------------------------------------
def _url_builder_factory(game_id: str, page_size: int = 200) -> Any:
    """
    Returns a function that builds the API URL for a given *page* (1‑based).
    The Speedrun.com API uses ``offset`` pagination:
    ``offset = (page‑1) * page_size``.
    """
    base_url = "https://www.speedrun.com/api/v1/runs"

    def builder(page: int) -> str:
        offset = (page - 1) * page_size
        return f"{base_url}?game={game_id}&max={page_size}&offset={offset}"

    return builder

def _fetch_page(url: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Fetch a single page from the Speedrun.com API.
    Returns the parsed JSON dictionary.
    """
    logger.info(f"Fetching URL: {url}")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 429:
            logger.warning("Rate limit hit (429). Sleeping for 10 seconds...")
            time.sleep(10)
            return _fetch_page(url, logger)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch {url}: HTTP {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Network error fetching {url}: {e}")
        raise

# ----------------------------------------------------------------------
# Core data‑fetching routine
# ----------------------------------------------------------------------
def fetch_game_runs(game_id: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Download *all* run records for a given ``game_id`` using the
    generic pagination helper.
    """
    url_builder = _url_builder_factory(game_id)
    # paginate_api is expected to handle the loop and return the accumulated list of runs
    runs = paginate_api(_fetch_page, url_builder, logger, max_pages=10_000, sleep_seconds=0.5)
    return runs

# ----------------------------------------------------------------------
# Persistence helpers
# ----------------------------------------------------------------------
def save_raw_data(game_id: str, runs: List[Dict[str, Any]], base_dir: Path = None) -> Path:
    """
    Write the raw run payload for a single game to
    ``data/raw/<game_id>.json``.
    """
    if base_dir is None:
        base_dir = Path("data") / "raw"
    base_dir.mkdir(parents=True, exist_ok=True)
    # Use the required filename pattern: {game_id}.json
    out_path = base_dir / f"{game_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"runs": runs}, f, ensure_ascii=False, indent=2)
    return out_path

def _update_fetch_checkpoint(completed_games: List[str], checkpoint_path: Path) -> None:
    """
    Persist the list of successfully fetched games to the checkpoint file.
    """
    state = {"completed_games": completed_games}
    ensure_checkpoint_dir(checkpoint_path.parent)
    save_checkpoint(state, checkpoint_path)

# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def main() -> None:
    logger = _setup_logger()
    logger.info("Starting fetch_data pipeline")

    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Config load failed: {e}")
        sys.exit(1)

    games: List[str] = config.get("games", [])
    if not games:
        logger.error("No games specified in config.yaml")
        sys.exit(1)

    # Resolve checkpoint location
    checkpoint_path = Path("data") / "checkpoints" / "fetch_checkpoint.json"
    checkpoint = load_checkpoint(checkpoint_path) or {}
    completed: List[str] = checkpoint.get("completed_games", [])

    # Determine which games still need to be processed
    pending = [g for g in games if g not in completed]

    logger.info(f"{len(pending)} games to fetch (already completed: {len(completed)})")

    for game_id in pending:
        try:
            logger.info(f"Fetching runs for game: {game_id}")
            runs = fetch_game_runs(game_id, logger)

            if not runs:
                logger.warning(f"No runs found for game {game_id}. Saving empty list.")

            logger.info(f"Fetched {len(runs)} runs for {game_id}")

            save_raw_data(game_id, runs)

            # Update checkpoint after each successful game
            completed.append(game_id)
            _update_fetch_checkpoint(completed, checkpoint_path)
            logger.info(f"Checkpoint updated – {len(completed)} / {len(games)} games completed")
        except KeyboardInterrupt:
            logger.warning("Interrupted by user – checkpoint saved, exiting")
            _update_fetch_checkpoint(completed, checkpoint_path)
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to fetch data for {game_id}: {e}")
            # Save progress so far
            _update_fetch_checkpoint(completed, checkpoint_path)
            raise

    logger.info("All games fetched successfully")
    logger.info("fetch_data pipeline completed")

if __name__ == "__main__":
    main()
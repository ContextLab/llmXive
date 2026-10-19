"""
fetch_data.py

Data‑acquisition script for the speedrun analysis pipeline.
It reads ``code/config.yaml`` for the list of games, downloads all
runs for each game via the Speedrun.com API, writes a raw JSON file
per game under ``data/raw/`` and maintains a checkpoint so that the
process can resume after interruption.
"""

import json
import logging
import sys
import urllib.request
from pathlib import Path
from typing import List, Dict

import yaml  # PyYAML is available in the base environment

from scripts.utils.pagination import paginate_api
from scripts.utils.checkpoint import (
    get_checkpoint_path,
    load_checkpoint,
    save_checkpoint,
    ensure_checkpoint_dir,
)

# ----------------------------------------------------------------------
# Configuration handling
# ----------------------------------------------------------------------


def load_config() -> Dict:
    """
    Load the pipeline configuration from ``code/config.yaml``.

    Returns
    -------
    dict
        Parsed configuration dictionary.
    """
    config_path = Path("code/config.yaml")
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ----------------------------------------------------------------------
# API interaction helpers
# ----------------------------------------------------------------------


def _fetch_page(url: str, logger: logging.Logger) -> Dict:
    """
    Fetch a single page from the Speedrun.com API.

    Parameters
    ----------
    url : str
        Full URL to request.
    logger : logging.Logger
        Logger for optional debugging output.

    Returns
    -------
    dict
        Parsed JSON response.
    """
    logger.debug(f"Requesting URL: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        logger.error(f"Failed to fetch URL {url}: {exc}")
        raise


def _url_builder_factory(game_id: str, page_size: int = 200) -> callable:
    """
    Factory that returns a ``url_builder`` function for a specific game.

    The Speedrun.com API uses ``offset`` pagination.  ``page`` is
    1‑based; the offset for page *p* is ``(p‑1) * page_size``.

    Parameters
    ----------
    game_id : str
        Identifier of the game to query.
    page_size : int, optional
        Number of results per page (default 200, the API maximum).

    Returns
    -------
    callable
        Function ``url_builder(page) -> str``.
    """
    def builder(page: int) -> str:
        offset = (page - 1) * page_size
        return (
            f"https://www.speedrun.com/api/v1/runs?"
            f"game={game_id}&max={page_size}&offset={offset}"
        )
    return builder


def fetch_game_runs(game_id: str) -> List[Dict]:
    """
    Download *all* runs for a given game using the generic pagination helper.

    Parameters
    ----------
    game_id : str
        Speedrun.com game identifier.

    Returns
    -------
    list[dict]
        List of run dictionaries as returned by the API.
    """
    logger = logging.getLogger("fetch_data")
    logger.setLevel(logging.INFO)

    url_builder = _url_builder_factory(game_id)

    # ``paginate_api`` will call ``_fetch_page`` for each page and
    # collect the ``data`` payloads.
    runs = paginate_api(_fetch_page, url_builder, logger)

    return runs


# ----------------------------------------------------------------------
# Disk I/O helpers
# ----------------------------------------------------------------------


def save_raw_data(game_id: str, runs: List[Dict], base_dir: Path = None) -> Path:
    """
    Write the raw run payload for a single game to ``data/raw/<game_id>.json``.

    Parameters
    ----------
    game_id : str
        Identifier of the game.
    runs : list[dict]
        List of run dictionaries to persist.
    base_dir : pathlib.Path, optional
        Directory under which the ``raw`` folder resides.  If omitted,
        ``data/raw`` relative to the project root is used.

    Returns
    -------
    pathlib.Path
        Path to the written JSON file.
    """
    if base_dir is None:
        base_dir = Path("data/raw")
    else:
        base_dir = Path(base_dir)

    base_dir.mkdir(parents=True, exist_ok=True)
    out_path = base_dir / f"{game_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(runs, f, indent=2, sort_keys=True)
    return out_path


# ----------------------------------------------------------------------
# Checkpoint helper
# ----------------------------------------------------------------------


def _update_fetch_checkpoint(completed_games: List[str], checkpoint_path: Path) -> None:
    """
    Persist the list of successfully fetched games.

    Parameters
    ----------
    completed_games : list[str]
        Game identifiers that have been fully processed.
    checkpoint_path : pathlib.Path
        Destination checkpoint file.
    """
    state = {"completed_games": completed_games}
    # ``save_checkpoint`` accepts either (state, path) or (path, state)
    save_checkpoint(state, checkpoint_path)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    Execute the data‑acquisition pipeline.

    The function respects any existing checkpoint at
    ``data/checkpoints/fetch_checkpoint.json`` and resumes from the
    first incomplete game.
    """
    logger = logging.getLogger("fetch_data")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

    # Load configuration
    config = load_config()
    games: List[str] = config.get("games", [])
    if not games:
        logger.error("No games listed in configuration; aborting.")
        sys.exit(1)

    # Prepare checkpoint handling
    ensure_checkpoint_dir()
    checkpoint_path = get_checkpoint_path("fetch_checkpoint.json")
    checkpoint = load_checkpoint(checkpoint_path) or {}
    completed: List[str] = checkpoint.get("completed_games", [])

    logger.info(f"Starting fetch for {len(games)} games; {len(completed)} already done.")

    for game_id in games:
        if game_id in completed:
            logger.info(f"Skipping already‑fetched game: {game_id}")
            continue

        try:
            logger.info(f"Fetching runs for game: {game_id}")
            runs = fetch_game_runs(game_id)
            save_raw_data(game_id, runs)
            completed.append(game_id)
            _update_fetch_checkpoint(completed, checkpoint_path)
            logger.info(f"Successfully fetched {len(runs)} runs for {game_id}")
        except KeyboardInterrupt:
            logger.warning("Interrupted by user – checkpoint saved; exiting.")
            _update_fetch_checkpoint(completed, checkpoint_path)
            sys.exit(1)
        except Exception as exc:
            logger.error(f"Failed to fetch data for {game_id}: {exc}")
            # Do not update the checkpoint; the game will be retried later.
            continue

    logger.info("Data acquisition complete.")


if __name__ == "__main__":
    main()

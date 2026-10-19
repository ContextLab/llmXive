"""
Data acquisition script for speedrun.com.

This script iterates over the games listed in ``code/config.yaml``,
downloads all runs for each game via the Speedrun.com public API,
writes the raw JSON payload to ``data/raw/{game_id}.json`` and,
**adds checkpoint integration** (task T015a).

After each successful download the script records the completed game
identifiers in a checkpoint file located at
``data/checkpoints/fetch_checkpoint.json``.  On a subsequent run the
script resumes from the last unfinished game, avoiding re‑download.
"""

import json
import logging
import sys
from pathlib import Path

# Local imports – the project already provides these helpers
from scripts.fetch_data import (
    load_config,
    setup_logging,
    fetch_game_runs,
    save_raw_data,
)
from scripts.utils.checkpoint import (
    load_checkpoint,
    save_checkpoint,
    get_checkpoint_path,
)

# ----------------------------------------------------------------------
# Helper: update checkpoint after a game has been processed
# ----------------------------------------------------------------------
def _update_fetch_checkpoint(completed_games, checkpoint_path):
    """
    Persist the list of completed games.

    Parameters
    ----------
    completed_games : list[str]
        Game IDs that have been successfully fetched.
    checkpoint_path : pathlib.Path
        Destination checkpoint file.
    """
    state = {"completed_games": completed_games}
    # ``save_checkpoint`` expects a string path; we pass the resolved string.
    save_checkpoint(state, str(checkpoint_path))


def main() -> None:
    """
    Entry point for the data‑acquisition pipeline.

    The workflow is:

    1. Load configuration (list of games, etc.).
    2. Load any existing fetch checkpoint.
    3. Iterate over the configured games, skipping those already recorded
       in the checkpoint.
    4. For each remaining game:
       a. Download all runs via ``fetch_game_runs`` (which uses the
          pagination helper).
       b. Write the raw payload to ``data/raw/<game_id>.json``.
       c. Append the game ID to the checkpoint and persist it.
    5. Exit cleanly.
    """
    logger = setup_logging("fetch_data")
    config = load_config()
    games = config.get("games", [])
    if not games:
        logger.error("No games configured – aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Load (or initialise) the fetch checkpoint
    # ------------------------------------------------------------------
    checkpoint_path = get_checkpoint_path("fetch")
    checkpoint_state = load_checkpoint(str(checkpoint_path))
    completed = set(checkpoint_state.get("completed_games", []))

    logger.info(f"Resuming fetch: {len(completed)} games already completed.")

    # ------------------------------------------------------------------
    # Process each game, skipping those already done
    # ------------------------------------------------------------------
    for game_id in games:
        if game_id in completed:
            logger.info(f"Skipping already‑fetched game: {game_id}")
            continue

        logger.info(f"Fetching runs for game: {game_id}")
        try:
            runs = fetch_game_runs(game_id, logger)
            # ``save_raw_data`` writes the JSON file under data/raw/
            save_raw_data(Path("data/raw"), game_id, runs)
        except Exception as exc:
            logger.error(f"Failed to fetch data for {game_id}: {exc}")
            # Abort – the checkpoint will still contain any earlier games
            sys.exit(1)

        # ----------------------------------------------------------------
        # Update checkpoint after a successful download
        # ----------------------------------------------------------------
        completed.add(game_id)
        _update_fetch_checkpoint(sorted(completed), checkpoint_path)
        logger.info(f"Game {game_id} fetched and checkpoint updated.")

    logger.info("All configured games have been processed.")


if __name__ == "__main__":
    main()

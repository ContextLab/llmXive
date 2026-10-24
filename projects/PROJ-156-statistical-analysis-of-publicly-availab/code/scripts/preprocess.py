"""
Pre‑processing pipeline for raw speedrun data.

This module reads the raw JSON files downloaded by ``fetch_data.py``,
removes duplicates, filters incomplete rows, hashes runner identifiers,
computes experience metrics, adds lagged competitive pressure and finally
writes the cleaned table to ``data/processed/run_records.csv``.
"""

import csv
import json
import logging
import os
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Union

# ----------------------------------------------------------------------
# Local utility imports
# ----------------------------------------------------------------------
from scripts.utils.checkpoint import (
    ensure_checkpoint_dir,
    save_checkpoint,
    load_checkpoint,
    get_checkpoint_path,
)
from scripts.utils.pressure import calculate_lagged_pressure

# ----------------------------------------------------------------------
# Logging helper
# ----------------------------------------------------------------------
def setup_logging(script_name: str) -> logging.Logger:
    """Configure a module‑specific logger that writes to ``code/logs``."""
    log_dir = Path("code") / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(script_name)
    logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicate log lines on reruns
    if logger.hasHandlers():
        logger.handlers.clear()

    log_file = log_dir / f"{script_name}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

# ----------------------------------------------------------------------
# Configuration loader (very small YAML‑like parser – matches existing tests)
# ----------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    """
    Load ``code/config.yaml`` using a minimal hand‑rolled parser.
    The parser understands top‑level scalar keys and simple lists.
    """
    config_path = Path("code") / "config.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config: Dict[str, Any] = {}
    current_key = None
    current_list: List[str] = []

    with config_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue

            if line.startswith("  - "):
                # List entry
                if current_key:
                    current_list.append(line[4:].strip().strip('"').strip("'"))
            elif ":" in line:
                # New key
                if current_key and current_list:
                    config[current_key] = current_list
                    current_list = []

                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value:
                    config[key] = value
                else:
                    current_key = key
                    current_list = []
    # Flush any trailing list
    if current_key and current_list:
        config[current_key] = current_list

    return config

# ----------------------------------------------------------------------
# Schema handling – only the ``required`` field list is needed for tests
# ----------------------------------------------------------------------
def load_schema() -> Dict[str, List[str]]:
    """
    Load the ``run_record`` JSON‑Schema and extract the list of required fields.
    """
    schema_path = Path("contracts") / "run_record.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    required: List[str] = []
    with schema_path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("- "):
                required.append(stripped[2:].strip().strip('"').strip("'"))
    return {"required": required}

# ----------------------------------------------------------------------
# Validation utilities (match test expectations – return bool only)
# ----------------------------------------------------------------------
def validate_record(record: Dict[str, Any], schema: Dict[str, List[str]]) -> bool:
    """
    Return ``True`` if *record* contains all fields listed in ``schema['required']``.
    """
    required_fields = schema.get("required", [])
    return all(field in record for field in required_fields)

# ----------------------------------------------------------------------
# Raw‑data loader – flexible for tests
# ----------------------------------------------------------------------
def load_raw_data(source: str) -> List[Dict[str, Any]]:
    """
    Load raw run data.

    ``source`` can be either:
    * a game identifier (e.g. ``'super-mario-64'``) – the function will look for
      ``data/raw/<game_id>.json`` *or* ``data/raw/<game_id>_raw.json``;
    * an explicit file path ending with ``.json`` – the file is loaded directly.

    The function returns the list stored under the top‑level ``'runs'`` key if
    present, otherwise the whole JSON object (used by some legacy tests).
    """
    # Determine whether ``source`` looks like a file path
    if source.endswith(".json"):
        raw_path = Path(source)
    else:
        # Try the two naming conventions used in the project
        candidate1 = Path("data") / "raw" / f"{source}.json"
        candidate2 = Path("data") / "raw" / f"{source}_raw.json"
        if candidate1.is_file():
            raw_path = candidate1
        elif candidate2.is_file():
            raw_path = candidate2
        else:
            raise FileNotFoundError(f"Raw data not found for game '{source}'. Tried {candidate1} and {candidate2}")

    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")

    with raw_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # The API dumps store the list under a top‑level ``'runs'`` key.
    # Some unit tests construct a plain list, so we support both.
    if isinstance(data, dict) and "runs" in data:
        return data["runs"]
    return data

# ----------------------------------------------------------------------
# Duplicate removal (by ``id`` + ``submission_date``)
# ----------------------------------------------------------------------
def remove_duplicates(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for run in runs:
        key = (run.get("id"), run.get("submission_date"))
        if key not in seen:
            seen.add(key)
            unique.append(run)
    return unique

# ----------------------------------------------------------------------
# Incomplete‑run filter – works with either a schema dict or a list of required fields
# ----------------------------------------------------------------------
def filter_incomplete_runs(
    runs: List[Dict[str, Any]],
    schema: Union[Dict[str, List[str]], List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Drop records that do not contain all required fields.

    ``schema`` can be:
    * a dict as returned by ``load_schema()`` (contains ``'required'``);
    * a plain list of field names;
    * ``None`` – in which case **no** filtering is performed.
    """
    if schema is None:
        return runs

    required_fields = schema.get("required") if isinstance(schema, dict) else schema
    if not required_fields:
        return runs

    filtered = []
    for run in runs:
        if all(field in run for field in required_fields):
            filtered.append(run)
    return filtered

# ----------------------------------------------------------------------
# Runner ID hashing – deterministic, used for anonymisation
# ----------------------------------------------------------------------
def hash_runner_id(runner_id: str, salt: str) -> str:
    combined = f"{runner_id}{salt}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

# ----------------------------------------------------------------------
# Experience‑metric calculation
# ----------------------------------------------------------------------
def compute_runner_metrics(
    runs: List[Dict[str, Any]],
    runner_id_map: Dict[str, str],
) -> Dict[str, Dict[str, Any]]:
    """
    Compute ``total_prior_runs`` and ``time_since_first_run_days`` for each runner.
    Returns a mapping ``hashed_runner_id -> metrics dict``.
    """
    # Group runs per (hashed) runner
    runner_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for run in runs:
        original_id = run.get("runner_id")
        hashed_id = runner_id_map.get(original_id, hash_runner_id(original_id, "default"))
        # Parse the submission date (ISO 8601)
        sub_date = datetime.fromisoformat(run["submission_date"].replace("Z", "+00:00"))
        runner_data[hashed_id].append(
            {"submission_date": sub_date, "game_id": run["game_id"]}
        )

    profiles: Dict[str, Dict[str, Any]] = {}
    for rid, records in runner_data.items():
        records.sort(key=lambda r: r["submission_date"])
        total_prior = len(records)
        # Time span between first and last run (in days)
        time_span = (records[-1]["submission_date"] - records[0]["submission_date"]).days
        games_played = len({r["game_id"] for r in records})
        profiles[rid] = {
            "total_prior_runs": total_prior,
            "time_since_first_run_days": time_span,
            "games_played_count": games_played,
        }
    return profiles

# ----------------------------------------------------------------------
# Helper required by ``tests/test_preprocess.py`` – returns a list of profile dicts
# ----------------------------------------------------------------------
def generate_runner_profiles(
    records: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Produce a list of per‑runner profile dictionaries.

    The function mirrors the logic of ``compute_runner_metrics`` but
    returns a *list* of dicts rather than a mapping, matching the unit‑test
    expectations.
    """
    # Build a temporary mapping using the same logic as ``compute_runner_metrics``
    # The runner IDs in the test data are already hashed, so we do not re‑hash
    runner_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rec in records:
        runner_groups[rec["runner_id"]].append(rec)

    profiles: List[Dict[str, Any]] = []
    for rid, recs in runner_groups.items():
        # Ensure dates are ``datetime`` objects
        dates = [
            _parse_date(r["submission_date"]) if isinstance(r["submission_date"], str) else r["submission_date"]
            for r in recs
        ]
        dates.sort()
        total_runs = len(dates)
        time_since_first = (dates[-1] - dates[0]).days if total_runs > 1 else 0
        games = {r["game_id"] for r in recs}
        profiles.append(
            {
                "runner_id": rid,
                "total_runs": total_runs,
                "games_played_count": len(games),
                "time_since_first_run_days": time_since_first,
            }
        )
    return profiles

def _parse_date(date_str: str) -> datetime:
    """Parse ISO‑8601 date strings (handles trailing ``Z``)."""
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

# ----------------------------------------------------------------------
# CSV writer utility
# ----------------------------------------------------------------------
def save_to_csv(data: List[Dict[str, Any]], output_path: str, fieldnames: List[str]) -> None:
    """
    Write *data* to ``output_path`` as a CSV file with the supplied ``fieldnames``.
    Parent directories are created automatically.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def main() -> None:
    logger = setup_logging("preprocess")
    logger.info("Starting preprocessing pipeline")

    config = load_config()
    games: List[str] = config.get("games", [])
    if not games:
        raise ValueError("No games specified in config.yaml")
    salt: str = config.get("salt", "default_salt")
    _ = config.get("min_sample_size", 100)  # retained for compatibility

    # Resolve checkpoint location (use explicit filename as required by spec)
    checkpoint_path = get_checkpoint_path("preprocess_checkpoint.json")
    checkpoint_data = load_checkpoint(checkpoint_path) or {}

    # Determine where to resume from
    start_idx = checkpoint_data.get("last_game_idx", 0)
    processed_runs: List[Dict[str, Any]] = checkpoint_data.get("processed_runs", [])
    all_runner_profiles: Dict[str, Dict[str, Any]] = checkpoint_data.get("runner_profiles", {})

    logger.info(f"Resuming from game index {start_idx}")

    for idx in range(start_idx, len(games)):
        game_id = games[idx]
        logger.info(f"Processing game {game_id}")

        try:
            # ------------------------------------------------------------------
            # Load raw data (flexible loader)
            # ------------------------------------------------------------------
            raw_runs = load_raw_data(game_id)
            logger.info(f"Loaded {len(raw_runs)} raw runs for {game_id}")

            # ------------------------------------------------------------------
            # Deduplicate and filter
            # ------------------------------------------------------------------
            unique_runs = remove_duplicates(raw_runs)
            logger.info(f"{len(unique_runs)} runs after duplicate removal")

            schema = load_schema()
            valid_runs = filter_incomplete_runs(unique_runs, schema)
            logger.info(f"{len(valid_runs)} runs after filtering incomplete records")

            # ------------------------------------------------------------------
            # Hash runner IDs
            # ------------------------------------------------------------------
            runner_id_map: Dict[str, str] = {}
            for run in valid_runs:
                original_id = run.get("runner_id")
                if original_id:
                    hashed = hash_runner_id(original_id, salt)
                    runner_id_map[original_id] = hashed
                    run["runner_id"] = hashed

            # ------------------------------------------------------------------
            # Compute experience metrics
            # ------------------------------------------------------------------
            profiles = compute_runner_metrics(valid_runs, runner_id_map)

            # Attach experience metrics to each run
            for run in valid_runs:
                rid = run.get("runner_id")
                if rid and rid in profiles:
                    run["total_prior_runs"] = profiles[rid]["total_prior_runs"]
                    run["time_since_first_run_days"] = profiles[rid]["time_since_first_run_days"]

            # ------------------------------------------------------------------
            # Checkpoint before pressure calculation (so we can resume if this step fails)
            # ------------------------------------------------------------------
            checkpoint_data = {
                "last_game_idx": idx + 1,
                "processed_runs": processed_runs + valid_runs,
                "runner_profiles": {**all_runner_profiles, **profiles},
                "timestamp": datetime.now().isoformat(),
            }
            # NOTE: ``save_checkpoint(state, path)`` – state first!
            save_checkpoint(checkpoint_data, checkpoint_path)
            logger.info(f"Checkpoint saved after processing game {game_id}")

            # ------------------------------------------------------------------
            # Lagged competitive pressure
            # ------------------------------------------------------------------
            valid_runs = calculate_lagged_pressure(valid_runs)

            # Ensure the pressure column is a non‑negative integer named 'competitive_pressure'
            for run in valid_runs:
                if "competitive_pressure" in run:
                    run["competitive_pressure"] = int(max(run["competitive_pressure"], 0))
                elif "lagged_competitive_pressure" in run:
                    run["competitive_pressure"] = int(max(run["lagged_competitive_pressure"], 0))
                    del run["lagged_competitive_pressure"]

            # ------------------------------------------------------------------
            # Append to global collections
            # ------------------------------------------------------------------
            processed_runs.extend(valid_runs)
            all_runner_profiles.update(profiles)

        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}")
            raise

    # ----------------------------------------------------------------------
    # Write final CSV files
    # ----------------------------------------------------------------------
    logger.info("Writing final CSV files")
    run_record_fields = [
        "run_time_seconds",
        "runner_id",
        "attempt_number",
        "category",
        "submission_date",
        "game_id",
        "total_prior_runs",
        "time_since_first_run_days",
        "competitive_pressure",
    ]
    save_to_csv(processed_runs, "data/processed/run_records.csv", run_record_fields)

    profile_fields = [
        "runner_id",
        "total_prior_runs",
        "time_since_first_run_days",
        "games_played_count",
    ]
    profile_rows = [
        {"runner_id": rid, **metrics} for rid, metrics in all_runner_profiles.items()
    ]
    save_to_csv(profile_rows, "data/processed/runner_profiles.csv", profile_fields)

    logger.info("Preprocessing completed successfully")

    # Clean up checkpoint file after a successful run
    if Path(checkpoint_path).exists():
        Path(checkpoint_path).unlink()
        logger.info("Checkpoint file removed after successful run")

if __name__ == "__main__":
    main()
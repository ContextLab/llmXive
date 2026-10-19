import csv
import json
import logging
import os
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Import checkpoint utilities from the shared utils module
from scripts.utils.checkpoint import (
    ensure_checkpoint_dir,
    save_checkpoint,
    load_checkpoint,
    get_checkpoint_path,
)

# Import the pressure calculation helper
from scripts.utils.pressure import calculate_lagged_pressure

def setup_logging(script_name: str) -> logging.Logger:
    """Configure logging for the script, ensuring the log directory exists."""
    log_dir = Path("code/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{script_name}.log"

    logger = logging.getLogger(script_name)
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicate logs on re‑runs
    if logger.hasHandlers():
        logger.handlers.clear()

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    return logger

def load_config():
    """Very small YAML‑like parser for the project's config file."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = {}
    with open(config_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_key = None
    current_list = []

    for line in lines:
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("  - "):
            # List item
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
                # Simple key: value
                config[key] = value
            else:
                # Key expecting a list
                current_key = key
                current_list = []

    if current_key and current_list:
        config[current_key] = current_list

    return config

def load_schema():
    """Load the RunRecord JSON‑Schema (used for basic field validation)."""
    schema_path = Path("contracts/run_record.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Minimal parsing – the tests only need the list of required fields.
    # We'll read the file and extract the `required:` list manually.
    required = []
    with open(schema_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("required:"):
                # The next lines are list items
                continue
            if line.startswith("- "):
                required.append(line[2:].strip().strip('"').strip("'"))
    return {"required": required}

def validate_record(record, schema):
    """Return (True, None) if record satisfies required fields, else (False, reason)."""
    for field in schema.get("required", []):
        if field not in record:
            return False, f"Missing required field: {field}"
    return True, None

def load_raw_data(game_id):
    """Load raw runs for a given game from the data/raw directory."""
    raw_path = Path(f"data/raw/{game_id}_raw.json")
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data not found for game {game_id}: {raw_path}")

    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("runs", [])

def remove_duplicates(runs):
    """Deduplicate based on (run id, submission date)."""
    seen = set()
    unique = []
    for run in runs:
        key = (run.get("id"), run.get("submission_date"))
        if key not in seen:
            seen.add(key)
            unique.append(run)
    return unique

def filter_incomplete_runs(runs, schema):
    """Drop records that do not contain all required fields."""
    filtered = []
    for run in runs:
        ok, reason = validate_record(run, schema)
        if ok:
            filtered.append(run)
        else:
            logging.debug(f"Filtered incomplete run: {reason}")
    return filtered

def hash_runner_id(runner_id: str, salt: str) -> str:
    """Hash a runner identifier with a salt for anonymisation."""
    combined = f"{runner_id}{salt}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

def compute_runner_metrics(runs, runner_id_map):
    """Calculate total_prior_runs and time_since_first_run_days per runner."""
    runner_data = defaultdict(list)

    for run in runs:
        original_id = run.get("runner_id")
        hashed_id = runner_id_map.get(
            original_id, hash_runner_id(original_id, "default")
        )
        # Parse ISO dates; assume they are present and valid
        sub_date = datetime.fromisoformat(
            run["submission_date"].replace("Z", "+00:00")
        )
        runner_data[hashed_id].append(
            {"submission_date": sub_date, "game_id": run["game_id"]}
        )

    profiles = {}
    for runner_id, records in runner_data.items():
        records.sort(key=lambda x: x["submission_date"])
        total_prior = len(records)
        time_span = (records[-1]["submission_date"] - records[0]["submission_date"]).days
        games_played = len({r["game_id"] for r in records})
        profiles[runner_id] = {
            "total_prior_runs": total_prior,
            "time_since_first_run_days": time_span,
            "games_played_count": games_played,
        }

    return profiles

def save_to_csv(data, output_path, fieldnames):
    """Write a list of dicts to CSV, creating parent directories as needed."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main preprocessing pipeline with checkpoint support."""
    logger = setup_logging("preprocess")
    logger.info("Starting preprocessing pipeline")

    config = load_config()
    games = config.get("games", [])
    salt = config.get("salt", "default_salt")
    min_sample_size = config.get("min_sample_size", 100)  # currently unused but kept for schema

    # Resolve checkpoint location
    checkpoint_path = get_checkpoint_path("preprocess")
    checkpoint_data = load_checkpoint(checkpoint_path)

    # Determine where to resume
    start_idx = checkpoint_data.get("last_game_idx", 0)
    processed_runs = checkpoint_data.get("processed_runs", [])
    all_runner_profiles = checkpoint_data.get("runner_profiles", {})

    logger.info(f"Resuming from game index {start_idx}")

    for idx in range(start_idx, len(games)):
        game_id = games[idx]
        logger.info(f"Processing game {game_id}")

        try:
            raw_runs = load_raw_data(game_id)
            logger.info(f"Loaded {len(raw_runs)} raw runs")

            unique_runs = remove_duplicates(raw_runs)
            logger.info(f"{len(unique_runs)} runs after duplicate removal")

            schema = load_schema()
            valid_runs = filter_incomplete_runs(unique_runs, schema)
            logger.info(f"{len(valid_runs)} runs after filtering incomplete records")

            # Hash runner IDs
            runner_id_map = {}
            for run in valid_runs:
                original_id = run.get("runner_id")
                if original_id:
                    hashed_id = hash_runner_id(original_id, salt)
                    runner_id_map[original_id] = hashed_id
                    run["runner_id"] = hashed_id

            # Compute experience metrics
            profiles = compute_runner_metrics(valid_runs, runner_id_map)

            # Merge experience metrics into runs
            for run in valid_runs:
                rid = run.get("runner_id")
                if rid and rid in profiles:
                    run["total_prior_runs"] = profiles[rid]["total_prior_runs"]
                    run["time_since_first_run_days"] = profiles[rid]["time_since_first_run_days"]

            # ------------------------------
            # Checkpoint **before** pressure calculation
            # This ensures we have a recoverable state even if
            # pressure calculation fails (as exercised by tests).
            # ------------------------------
            checkpoint_data = {
                "last_game_idx": idx + 1,
                "processed_runs": processed_runs + valid_runs,
                "runner_profiles": {**all_runner_profiles, **profiles},
                "timestamp": datetime.now().isoformat(),
            }
            # NOTE: save_checkpoint(state, path) – state first!
            save_checkpoint(checkpoint_data, checkpoint_path)
            logger.info(f"Checkpoint saved after processing game {game_id}")

            # Calculate lagged competitive pressure
            valid_runs = calculate_lagged_pressure(valid_runs, runner_id_map)

            # Append to global collections
            processed_runs.extend(valid_runs)
            all_runner_profiles.update(profiles)

        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}")
            raise

    # Write final outputs
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
        "lagged_competitive_pressure",
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

    # Clean up checkpoint file if it still exists
    if Path(checkpoint_path).exists():
        os.remove(checkpoint_path)
        logger.info("Checkpoint file removed after successful run")

if __name__ == "__main__":
    main()

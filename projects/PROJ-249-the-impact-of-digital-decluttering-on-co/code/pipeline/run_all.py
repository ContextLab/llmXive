"""Single documented entry point for the study pipeline (T001).

Validates the study configuration strictly (raising on any missing or
malformed key), establishes the project layout, writes
``data/results/pipeline_status.json``, and (re)builds the checksum
manifest ``data/checksums.sha256`` covering every file under ``data/``.

Usage:
    python -m code.pipeline.run_all --config code/config/study_config.yaml
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TOP_LEVEL_KEYS = {
    "seed",
    "n_participants",
    "dropout_rate",
    "effect_sizes",
    "practice_effect_grid",
    "bootstrap_resamples",
    "start_date",
    "pilot_n",
}

REQUIRED_EFFECT_SIZE_METRICS = {"SART", "Ospan", "PSS-10", "PANAS-PA", "PANAS-NA"}

REQUIRED_DIRECTORIES = [
    "code/scoring",
    "code/analysis",
    "code/validation",
    "code/viz",
    "code/pipeline",
    "code/tests",
    "data/raw",
    "data/processed",
    "data/results",
]

MANIFEST_PATH = PROJECT_ROOT / "data" / "checksums.sha256"


def load_and_validate_config(config_path: Path) -> dict:
    """Load the study config and validate it strictly; raise on any error."""
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"Config file is not valid YAML: {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError("Config root must be a mapping of keys to values.")

    missing = REQUIRED_TOP_LEVEL_KEYS - set(config.keys())
    if missing:
        raise ValueError(f"Config missing required keys: {sorted(missing)}")
    extra = set(config.keys()) - REQUIRED_TOP_LEVEL_KEYS
    if extra:
        raise ValueError(f"Config contains unexpected keys: {sorted(extra)}")

    if not isinstance(config["seed"], int) or isinstance(config["seed"], bool):
        raise ValueError("'seed' must be an integer.")
    if not isinstance(config["n_participants"], int) or isinstance(config["n_participants"], bool):
        raise ValueError("'n_participants' must be an integer.")
    if config["n_participants"] < 1:
        raise ValueError("'n_participants' must be >= 1.")
    if not isinstance(config["dropout_rate"], (int, float)) or isinstance(config["dropout_rate"], bool):
        raise ValueError("'dropout_rate' must be a float.")
    if not 0.0 <= float(config["dropout_rate"]) <= 1.0:
        raise ValueError("'dropout_rate' must be within [0.0, 1.0].")

    effect_sizes = config["effect_sizes"]
    if not isinstance(effect_sizes, dict):
        raise ValueError("'effect_sizes' must be a per-metric mapping.")
    missing_metrics = REQUIRED_EFFECT_SIZE_METRICS - set(effect_sizes.keys())
    if missing_metrics:
        raise ValueError(f"'effect_sizes' missing metrics: {sorted(missing_metrics)}")
    extra_metrics = set(effect_sizes.keys()) - REQUIRED_EFFECT_SIZE_METRICS
    if extra_metrics:
        raise ValueError(f"'effect_sizes' has unexpected metrics: {sorted(extra_metrics)}")
    for metric, value in effect_sizes.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"effect_sizes[{metric}] must be numeric, got {value!r}")

    grid = config["practice_effect_grid"]
    if not isinstance(grid, list) or len(grid) != 3:
        raise ValueError("'practice_effect_grid' must be a 3-element list.")
    if [float(g) for g in grid] != [0.0, 0.2, 0.4]:
        raise ValueError("'practice_effect_grid' must be exactly [0.0, 0.2, 0.4].")

    if not isinstance(config["bootstrap_resamples"], int) or isinstance(config["bootstrap_resamples"], bool):
        raise ValueError("'bootstrap_resamples' must be an integer.")
    if config["bootstrap_resamples"] < 1:
        raise ValueError("'bootstrap_resamples' must be >= 1.")

    start_date = config["start_date"]
    if not isinstance(start_date, str):
        raise ValueError("'start_date' must be an ISO date string.")
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"'start_date' must be an ISO date (YYYY-MM-DD), got {start_date!r}") from exc

    if not isinstance(config["pilot_n"], int) or isinstance(config["pilot_n"], bool):
        raise ValueError("'pilot_n' must be an integer.")
    if config["pilot_n"] < 1:
        raise ValueError("'pilot_n' must be >= 1.")

    return config


def ensure_layout() -> list:
    """Create the required project directories; return those created now."""
    created = []
    for rel in REQUIRED_DIRECTORIES:
        directory = PROJECT_ROOT / rel
        if not directory.is_dir():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(rel)
    return created


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rebuild_checksum_manifest() -> int:
    """(Re)build data/checksums.sha256 covering every file under data/.

    The manifest itself is excluded. Paths are recorded relative to the
    project root so ``sha256sum -c data/checksums.sha256`` works from the
    project root. Returns the number of files recorded.
    """
    data_dir = PROJECT_ROOT / "data"
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    if data_dir.is_dir():
        for path in sorted(data_dir.rglob("*")):
            if path.is_file() and path != MANIFEST_PATH:
                rel = path.relative_to(PROJECT_ROOT).as_posix()
                entries.append(f"{sha256_of(path)}  {rel}")

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        for line in entries:
            f.write(line + "\n")
    return len(entries)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the study pipeline (T001 stage).")
    parser.add_argument(
        "--config",
        default="code/config/study_config.yaml",
        help="Path to the study configuration YAML (relative to project root).",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    config = load_and_validate_config(config_path)
    created_dirs = ensure_layout()

    status_path = PROJECT_ROOT / "data" / "results" / "pipeline_status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)

    n_checksummed = rebuild_checksum_manifest()

    status = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": "python -m code.pipeline.run_all --config code/config/study_config.yaml",
        "config_path": config_path.relative_to(PROJECT_ROOT).as_posix(),
        "config_validated": True,
        "config": config,
        "directories_ensured": REQUIRED_DIRECTORIES,
        "directories_created_this_run": created_dirs,
        "checksum_manifest": "data/checksums.sha256",
        "files_under_data_checksummed": n_checksummed,
        "pipeline_stages_completed": ["T001_setup"],
        "note": (
            "Setup stage only. Later tasks extend this entry point to run "
            "the seeded simulation, compliance processing, analysis, "
            "sensitivity checks, figures, and reporting in dependency order."
        ),
    }
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    # Include the status file itself in the manifest.
    n_checksummed = rebuild_checksum_manifest()

    print(f"Config validated: {config_path.relative_to(PROJECT_ROOT)}")
    print(f"Layout ensured ({len(REQUIRED_DIRECTORIES)} directories; "
          f"{len(created_dirs)} created this run)")
    print(f"Checksum manifest written: {MANIFEST_PATH.relative_to(PROJECT_ROOT)} "
          f"({n_checksummed} files recorded)")
    print(f"Status written: {status_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
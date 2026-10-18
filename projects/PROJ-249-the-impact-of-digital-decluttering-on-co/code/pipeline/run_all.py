"""
Single runnable entry point for the digital decluttering study pipeline.

Usage:
    python -m code.pipeline.run_all --config code/config/study_config.yaml

This module (T001):
  * validates the study configuration strictly (raising on any missing,
    extra, or malformed key),
  * establishes the project layout (code/scoring/, code/analysis/,
    code/validation/, code/viz/, code/pipeline/, code/tests/,
    data/raw/, data/processed/, data/results/),
  * writes data/results/pipeline_status.json,
  * (re)builds the checksum manifest data/checksums.sha256 covering
    every file under data/ (constitution Principle III).

Later tasks extend the run() function to invoke the full study
pipeline in dependency order. No synthetic data is generated here.
"""

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

# Required top-level keys and their expected types.
REQUIRED_KEYS = {
    "seed": int,
    "n_participants": int,
    "dropout_rate": float,
    "effect_sizes": dict,
    "practice_effect_grid": list,
    "bootstrap_resamples": int,
    "start_date": str,
    "pilot_n": int,
}

REQUIRED_METRICS = ["SART", "Ospan", "PSS-10", "PANAS-PA", "PANAS-NA"]
REQUIRED_PRACTICE_GRID = [0.0, 0.2, 0.4]

LAYOUT_DIRS = [
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

MANIFEST_PATH = Path("data/checksums.sha256")


def load_and_validate_config(config_path: str) -> dict:
    """Load study_config.yaml and validate it strictly.

    Raises ValueError on any missing, extra, or malformed key.
    Returns the parsed configuration dictionary.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ValueError(f"Config root must be a mapping, got {type(cfg).__name__}")

    missing = [k for k in REQUIRED_KEYS if k not in cfg]
    if missing:
        raise ValueError(f"Config missing required key(s): {missing}")

    extra = [k for k in cfg if k not in REQUIRED_KEYS]
    if extra:
        raise ValueError(f"Config contains unexpected key(s): {extra}")

    for key, expected in REQUIRED_KEYS.items():
        value = cfg[key]
          # bool is a subclass of int; reject it where int is expected.
        if expected is int and isinstance(value, bool):
            raise ValueError(f"Config key '{key}' must be an int, got bool")
        if not isinstance(value, expected):
            raise ValueError(
                f"Config key '{key}' must be {expected.__name__}, "
                f"got {type(value).__name__}"
            )

    if not (0 < cfg["n_participants"] <= 1000):
        raise ValueError("n_participants must be in (0, 1000]")
    if not (0.0 <= cfg["dropout_rate"] <= 1.0):
        raise ValueError("dropout_rate must be in [0.0, 1.0]")
    if cfg["bootstrap_resamples"] != 10000:
        raise ValueError("bootstrap_resamples must be 10000")
    if cfg["pilot_n"] < 1:
        raise ValueError("pilot_n must be >= 1")

    effect_sizes = cfg["effect_sizes"]
    missing_metrics = [m for m in REQUIRED_METRICS if m not in effect_sizes]
    if missing_metrics:
        raise ValueError(f"effect_sizes missing metric(s): {missing_metrics}")
    extra_metrics = [m for m in effect_sizes if m not in REQUIRED_METRICS]
    if extra_metrics:
        raise ValueError(f"effect_sizes has unexpected metric(s): {extra_metrics}")
    for metric, value in effect_sizes.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"effect_sizes['{metric}'] must be numeric")
        if not (-3.0 <= float(value) <= 3.0):
            raise ValueError(f"effect_sizes['{metric}'] must be in [-3, 3]")

    grid = cfg["practice_effect_grid"]
    if [float(g) for g in grid] != REQUIRED_PRACTICE_GRID:
        raise ValueError(
            f"practice_effect_grid must be {REQUIRED_PRACTICE_GRID}, got {grid}"
        )

    try:
        date.fromisoformat(cfg["start_date"])
    except ValueError:
        raise ValueError(
            f"start_date must be an ISO date (YYYY-MM-DD), got {cfg['start_date']!r}"
        )

    return cfg


def ensure_layout() -> list:
    """Create the project directory layout; return created directories."""
    created = []
    for d in LAYOUT_DIRS:
        p = Path(d)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def update_checksum_manifest() -> int:
    """(Re)build data/checksums.sha256 covering all files under data/.

    The manifest itself is excluded. Entries are written in sorted
    order so the manifest is deterministic. Returns the number of
    files recorded.
    """
    data_dir = Path("data")
    if not data_dir.exists():
        return 0

    entries = []
    for p in sorted(data_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(data_dir.parent).as_posix()
        if rel == MANIFEST_PATH.as_posix():
            continue
        entries.append((sha256_file(p), rel))

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        for digest, rel in entries:
            f.write(f"{digest}  {rel}\n")
    return len(entries)


def run(config_path: str) -> dict:
    """Execute the T001 pipeline stage; returns the status record."""
    cfg = load_and_validate_config(config_path)
    created = ensure_layout()

    status = {
        "stage": "T001-setup",
        "config_path": config_path,
        "config": cfg,
        "directories_established": LAYOUT_DIRS,
        "directories_newly_created": created,
        "checksum_manifest": MANIFEST_PATH.as_posix(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    status_path = Path("data/results/pipeline_status.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, sort_keys=True)

    n_recorded = update_checksum_manifest()

    print("Study configuration validated successfully.")
    print(f"Layout established ({len(LAYOUT_DIRS)} directories).")
    print(f"Pipeline status written to {status_path.as_posix()}")
    print(f"Checksum manifest covers {n_recorded} file(s) under data/.")
    return status


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Digital decluttering study pipeline (single entry point)."
    )
    parser.add_argument(
        "--config",
        default="code/config/study_config.yaml",
        help="Path to the study configuration YAML.",
    )
    args = parser.parse_args(argv)
    try:
        run(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"[CONFIG ERROR] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

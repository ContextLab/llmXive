"""End-to-end pipeline entry point for the digital decluttering study.

Usage:
    python -m code.pipeline.run_all --config code/config/study_config.yaml

This module establishes the project layout, validates the study
configuration strictly (raising on any missing or malformed key),
writes a pipeline status artifact under data/results/, and
(re)initializes the SHA-256 checksum manifest data/checksums.sha256
covering every file under data/ (excluding the manifest itself).
"""
import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import yaml

from llmxive_toolkit import paths

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
METRICS = ["SART", "Ospan", "PSS-10", "PANAS-PA", "PANAS-NA"]
PRACTICE_GRID = [0.0, 0.2, 0.4]


def load_config(config_path: Path) -> dict:
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if not isinstance(config, dict):
        raise ValueError(f"Config root must be a mapping, got {type(config)!r}")
    missing = [k for k in REQUIRED_KEYS if k not in config]
    if missing:
        raise ValueError(f"Config missing required keys: {missing}")
    extra = [k for k in config if k not in REQUIRED_KEYS]
    if extra:
        raise ValueError(f"Config has unexpected keys: {extra}")
    for key, expected in REQUIRED_KEYS.items():
        value = config[key]
        if expected is float:
            ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        else:
            ok = isinstance(value, expected)
        if not ok:
            raise ValueError(
                f"Config key '{key}' must be of type {expected.__name__}, "
                f"got {type(value).__name__}"
              )
    # Validate value ranges
    if not 0.0 <= config["dropout_rate"] <= 1.0:
        raise ValueError("dropout_rate must be within [0, 1]")
    if config["n_participants"] < 1:
        raise ValueError("n_participants must be >= 1")
    if config["bootstrap_resamples"] != 10000:
        raise ValueError("bootstrap_resamples must be 10000")
    if config["pilot_n"] < 1:
        raise ValueError("pilot_n must be >= 1")
    if config["practice_effect_grid"] != PRACTICE_GRID:
        raise ValueError(
            f"practice_effect_grid must be exactly {PRACTICE_GRID}, "
            f"got {config['practice_effect_grid']}"
        )
    eff = config["effect_sizes"]
    missing_metrics = [m for m in METRICS if m not in eff]
    if missing_metrics:
        raise ValueError(f"effect_sizes missing metrics: {missing_metrics}")
    for metric in METRICS:
        v = eff[metric]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise ValueError(f"effect_sizes['{metric}'] must be numeric")
    # Validate ISO date
    try:
        date.fromisoformat(config["start_date"])
    except ValueError as exc:
        raise ValueError(
            f"start_date must be an ISO date (YYYY-MM-DD): {config['start_date']}"
        ) from exc
    return config


def ensure_layout() -> None:
    """Create the canonical project directory layout."""
    for sub in [
        ("code", "scoring"),
        ("code", "analysis"),
        ("code", "validation"),
        ("code", "viz"),
        ("code", "pipeline"),
        ("code", "tests"),
        ("data", "raw"),
        ("data", "processed"),
        ("data", "results"),
    ]:
        paths.path(*sub).mkdir(parents=True, exist_ok=True)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksum_manifest(data_dir: Path, manifest_path: Path) -> int:
    """(Re)write the checksum manifest covering all files under data/."""
    entries = []
    if data_dir.is_dir():
        for path in sorted(data_dir.rglob("*")):
            if not path.is_file():
                continue
            if path == manifest_path:
                continue
            rel = path.relative_to(manifest_path.parent.parent)
            entries.append(f"{sha256_of(path)}  {rel.as_posix()}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
        for line in entries:
            fh.write(line + "\n")
    return len(entries)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the study pipeline (setup stage).")
    parser.add_argument(
        "--config",
        default="code/config/study_config.yaml",
        help="Path to the study configuration YAML",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = paths.root / config_path

    config = load_config(config_path)
    ensure_layout()

    status = {
        "stage": "T001-setup",
        "status": "ok",
        "config": str(config_path.relative_to(paths.root)),
        "seed": config["seed"],
        "n_participants": config["n_participants"],
        "dropout_rate": config["dropout_rate"],
        "bootstrap_resamples": config["bootstrap_resamples"],
        "pilot_n": config["pilot_n"],
        "practice_effect_grid": config["practice_effect_grid"],
        "start_date": config["start_date"],
        "metrics": METRICS,
        "note": (
            "Pipeline layout, configuration, and checksum manifest "
            "initialized. Later tasks append data artifacts and extend "
            "this runner with simulation, compliance, and analysis stages."
        ),
    }
    status_path = paths.data("results", "pipeline_status.json")
    with open(status_path, "w", encoding="utf-8") as fh:
        json.dump(status, fh, indent=2)
        fh.write("\n")

    manifest = paths.data("checksums.sha256")
    n = write_checksum_manifest(paths.path("data"), manifest)
    print(f"Pipeline setup complete.")
    print(f"  Config validated: {config_path}")
    print(f"  Status written:   {status_path}")
    print(f"  Manifest entries: {n} ({manifest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Aggregation of stability metrics from processed windows (T012b, SC-003).

Collects per-window importance profiles (JSON files written by
``train_and_importance.save_importance_profile`` or rows of a
``importance_profiles.csv``) and reports:
  - total windows processed
  - count of successful/stable windows (R^2 >= threshold)
  - average R^2 of valid windows
"""
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_R2_THRESHOLD = 0.8


def _extract_r2(profile: Dict[str, Any]) -> Optional[float]:
    """Pull an R^2 value out of a profile dict, if present."""
    for key in ("r_squared", "r2_score", "r2"):
        if key in profile:
            try:
                return float(profile[key])
            except (TypeError, ValueError):
                return None
    return None


def calculate_stability_metrics(
    importance_profiles: List[Dict[str, Any]],
    r2_threshold: float = DEFAULT_R2_THRESHOLD,
) -> Dict[str, Any]:
    """Calculate stability metrics from a list of profile dictionaries.

    A window counts as stable when its recorded R^2 meets the threshold;
    profiles without an R^2 value are counted as processed but do not
    contribute to the R^2 average.
    """
    total_windows = len(importance_profiles)
    if total_windows == 0:
        return {
            "total_windows": 0,
            "stable_window_count": 0,
            "average_r_squared": 0.0,
        }

    r_squared_values: List[float] = []
    stable_count = 0
    profiles_with_r2 = 0

    for profile in importance_profiles:
        r_sq = _extract_r2(profile)
        if r_sq is not None:
            profiles_with_r2 += 1
            r_squared_values.append(r_sq)
            if r_sq >= r2_threshold:
                stable_count += 1

    if profiles_with_r2 == 0:
        # No R^2 recorded: only validated windows produce profiles, so
        # treat all present profiles as successful windows.
        stable_count = total_windows
        avg_r_sq = 0.0
    else:
        avg_r_sq = sum(r_squared_values) / len(r_squared_values)

    return {
        "total_windows": total_windows,
        "stable_window_count": stable_count,
        "average_r_squared": avg_r_sq,
    }


def _load_json_profiles(directory: Path) -> List[Dict[str, Any]]:
    """Load importance profile JSON files from a directory."""
    profiles: List[Dict[str, Any]] = []
    for path in sorted(directory.glob("importance_profile_*.json")):
        try:
            with open(path, "r") as f:
                profiles.append(json.load(f))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read profile %s: %s", path, exc)
    return profiles


def _load_csv_profiles(csv_path: Path) -> List[Dict[str, Any]]:
    """Load profile rows from an importance_profiles.csv file."""
    profiles: List[Dict[str, Any]] = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            profiles.append(dict(row))
    return profiles


def aggregate_from_profiles(
    profiles_path,
    log: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """Aggregate stability metrics from profiles on disk.

    Args:
        profiles_path: Either a directory containing
            ``importance_profile_*.json`` files, or a path to a
            ``importance_profiles.csv`` file.
        log: Optional logger (defaults to the module logger).

    Returns:
        Stability metrics dict (see ``calculate_stability_metrics``).
    """
    if log is None:
        log = logger
    path = Path(profiles_path)

    profiles: List[Dict[str, Any]] = []
    if path.is_dir():
        profiles = _load_json_profiles(path)
    elif path.is_file():
        try:
            profiles = _load_csv_profiles(path)
        except (OSError, csv.Error) as exc:
            log.warning("Could not read profiles file %s: %s", path, exc)
            profiles = []
    else:
        log.warning("Profiles path not found: %s", path)
        return calculate_stability_metrics([])

    metrics = calculate_stability_metrics(profiles)
    log.info(
        "Stability metrics: %d windows, %d stable, avg R^2=%.4f",
        metrics["total_windows"],
        metrics["stable_window_count"],
        metrics["average_r_squared"],
    )
    return metrics


def save_stability_report(
    metrics: Dict[str, Any],
    output_path,
    log: Optional[logging.Logger] = None,
) -> None:
    """Save stability metrics to a JSON file."""
    if log is None:
        log = logger
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)
    log.info("Saved stability report to %s", out)


def main() -> None:
    """Entry point for stats aggregator."""
    from utils.config import get_config

    config = get_config()
    paths = config.get("paths", {})
    profiles_path = paths.get("importance_profiles", "outputs/importance_profiles.csv")
    output_path = paths.get("stability_report", "outputs/stability_report.json")

    metrics = aggregate_from_profiles(profiles_path)
    save_stability_report(metrics, output_path)


if __name__ == "__main__":
    main()

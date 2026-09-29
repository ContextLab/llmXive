"""
CI script to verify that the overall connectivity success rate of generated network
realizations meets the required threshold (≥ 95%). The script reads a JSON file
containing per‑realization connectivity information, computes the success rate,
prints a short report, and exits with a non‑zero status if the threshold is not met.

Expected JSON format (list of objects):
    [
        {"realization_id": "uuid‑1", "connected": true},
        {"realization_id": "uuid‑2", "connected": false},
        ...
    ]

The script can be invoked directly:
    python code/ci/check_connectivity.py [path/to/metrics.json]

If no path is supplied, it defaults to ``data/analysis/connectivity_metrics.json``.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_METRICS_PATH = Path("data/analysis/connectivity_metrics.json")
SUCCESS_THRESHOLD = 0.95  # 95%


def load_metrics(path: Path) -> List[Dict[str, Any]]:
    """
    Load connectivity metrics from a JSON file.

    Parameters
    ----------
    path: Path
        Path to the JSON file containing a list of metric dictionaries.

    Returns
    -------
    List[Dict[str, Any]]
        The parsed list of metric dictionaries.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    json.JSONDecodeError
        If the file does not contain valid JSON.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Connectivity metrics file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of metric objects in {path}, got {type(data)}")
    return data


def get_success_rate(metrics: List[Dict[str, Any]]) -> float:
    """
    Compute the proportion of realizations that are marked as connected.

    Parameters
    ----------
    metrics: List[Dict[str, Any]]
        List of metric dictionaries. Each dictionary must contain a boolean
        ``connected`` key.

    Returns
    -------
    float
        Success rate in the range [0.0, 1.0].
    """
    if not metrics:
        return 0.0
    total = len(metrics)
    connected = sum(1 for m in metrics if bool(m.get("connected", False)))
    return connected / total


def main() -> None:
    """
    Entry point for the CI check.

    Reads the metrics file, computes the success rate, prints a short report,
    and exits with status code 1 if the success rate is below the required
    threshold.
    """
    # Determine the metrics file location
    if len(sys.argv) > 1:
        metrics_path = Path(sys.argv[1])
    else:
        metrics_path = DEFAULT_METRICS_PATH

    try:
        metrics = load_metrics(metrics_path)
    except Exception as exc:
        print(f"[ERROR] Failed to load connectivity metrics: {exc}", file=sys.stderr)
        sys.exit(2)  # distinct exit code for load failures

    success_rate = get_success_rate(metrics)
    percent = success_rate * 100
    print(f"[INFO] Connectivity success rate: {percent:.2f}% ({success_rate:.4f})")

    if success_rate < SUCCESS_THRESHOLD:
        print(
            f"[FAIL] Success rate {percent:.2f}% is below the required "
            f"{SUCCESS_THRESHOLD * 100:.0f}% threshold. CI will abort.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print("[PASS] Connectivity success rate meets the required threshold.")
        sys.exit(0)


if __name__ == "__main__":
    main()
"""
CI utility to enforce a minimum connectivity success rate across the generated
network ensemble.

The script reads a JSON file containing connectivity metrics, computes the overall
success rate, and exits with a non‑zero status code if the rate falls below the
required 95 % threshold.  It is intended to be invoked from a CI pipeline as
a gate step, e.g.:

    python code/ci/check_connectivity.py path/to/metrics.json

If no path is supplied, the default location ``data/analysis/connectivity_metrics.json``
is used.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

DEFAULT_METRICS_PATH = Path("data/analysis/connectivity_metrics.json")
REQUIRED_SUCCESS_RATE = 0.95  # 95 %


def _normalize_metrics(raw: Union[Dict[str, Any], List[Any]]) -> Dict[str, int]:
    """
    Convert raw JSON content into a uniform ``{'total': int, 'successful': int}``
    dictionary.

    The JSON file may be one of the following forms:

    1. ``{\"total\": N, \"successful\": M}`` – explicit counts.
    2. ``[{\"realization_id\": ..., \"connected\": true}, ...]`` – a list of per‑realization
       records.  ``connected`` is interpreted as a success flag.
    3. ``[true, false, true, ...]`` – a flat list of booleans indicating success.

    Any other structure raises a ``ValueError`` so that CI fails loudly.
    """
    if isinstance(raw, dict):
        if "total" in raw and "successful" in raw:
            return {"total": int(raw["total"]), "successful": int(raw["successful"])}
        raise ValueError("Dictionary JSON must contain 'total' and 'successful' keys.")
    if isinstance(raw, list):
        # Case 3: flat list of booleans
        if all(isinstance(item, bool) for item in raw):
            total = len(raw)
            successful = sum(raw)
            return {"total": total, "successful": successful}
        # Case 2: list of dicts with a 'connected' field
        if all(isinstance(item, dict) and "connected" in item for item in raw):
            total = len(raw)
            successful = sum(1 for item in raw if bool(item["connected"]))
            return {"total": total, "successful": successful}
    raise ValueError("Unrecognised connectivity metrics JSON format.")


def load_metrics(path: Path = DEFAULT_METRICS_PATH) -> Dict[str, int]:
    """
    Load connectivity metrics from *path* and return a dictionary with the keys
    ``'total'`` and ``'successful'``.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Connectivity metrics file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return _normalize_metrics(raw)


def get_success_rate(metrics: Dict[str, int]) -> float:
    """
    Compute the success rate given a ``{'total': int, 'successful': int}`` mapping.
    Returns a float in the range [0, 1].
    """
    total = metrics.get("total", 0)
    successful = metrics.get("successful", 0)
    if total == 0:
        raise ValueError("Total number of realizations is zero; cannot compute success rate.")
    return successful / total


def main(argv: List[str] | None = None) -> None:
    """
    Entry point for the CI check.

    Parameters
    ----------
    argv
        Optional list of command‑line arguments (excluding the script name).
        If ``None``, ``sys.argv[1:]`` is used.  The first argument, if present,
        is interpreted as the path to the JSON metrics file.
    """
    if argv is None:
        argv = sys.argv[1:]

    metrics_path = Path(argv[0]) if argv else DEFAULT_METRICS_PATH

    try:
        metrics = load_metrics(metrics_path)
        rate = get_success_rate(metrics)
    except Exception as exc:
        # Any problem loading or parsing the file should cause the CI step to fail.
        print(f"[CI][CONNECTIVITY] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if rate < REQUIRED_SUCCESS_RATE:
        print(
            f"[CI][CONNECTIVITY] FAILURE: success rate {rate:.2%} "
            f"is below the required {REQUIRED_SUCCESS_RATE:.2%}.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Success path – print a concise message for CI logs.
    print(
        f"[CI][CONNECTIVITY] SUCCESS: success rate {rate:.2%} meets the required threshold."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
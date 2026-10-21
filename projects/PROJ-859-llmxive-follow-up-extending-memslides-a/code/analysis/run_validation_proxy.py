"""T000: External Validation Proxy.

Attempts to validate the synthetic trace distribution against a small,
verified external proxy dataset (if one exists on disk). If no proxy is
available, the limitation is documented in
``data/processed/validation_proxy.json`` with ``reason:
"no_proxy_available"`` per the task constraint.

Output schema (when a proxy exists):
    ks_statistic: float   (max KS statistic across metrics)
    p_value: float        (min p-value across metrics)
    is_valid_shift: bool  (True if any metric shows p < 0.05)
    per_metric: {...}     (per-metric KS statistic / p-value)

When no proxy exists:
    reason: "no_proxy_available"
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from scipy.stats import ks_2samp

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

METRICS = ["sequence_entropy", "tool_repetition_freq", "arg_semantic_variance"]

# Candidate locations where a verified external proxy dataset may live.
PROXY_CANDIDATES = [
    Path("data/proxy"),
    Path("data/external"),
    Path("data/raw/proxy"),
]

# Candidate locations of the synthetic trace data (training split).
SYNTHETIC_CANDIDATES = [
    Path("data/training"),
    Path("data/raw/traces"),
    Path("data/raw/training"),
]


def _load_json_files(directory: Path) -> List[Dict[str, Any]]:
    """Load every ``*.json`` file in ``directory`` (non-recursive)."""
    records: List[Dict[str, Any]] = []
    for fp in sorted(directory.glob("*.json")):
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                obj = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Skipping unreadable file %s: %s", fp, exc)
            continue
        if isinstance(obj, dict):
            records.append(obj)
        elif isinstance(obj, list):
            records.extend(r for r in obj if isinstance(r, dict))
    return records


def _find_dir(candidates: List[Path]) -> Optional[Path]:
    """Return the first candidate directory that exists and has JSON files."""
    for cand in candidates:
        if cand.is_dir() and any(cand.glob("*.json")):
            return cand
    return None


def _extract(records: List[Dict[str, Any]], metric: str) -> List[float]:
    """Pull a numeric metric from trace dicts, tolerating nested layouts."""
    values: List[float] = []
    for rec in records:
        # direct key
        if metric in rec:
            v = rec[metric]
        else:
            # nested under "metrics" or "structural_metrics"
            nested = rec.get("metrics") or rec.get("structural_metrics") or {}
            v = nested.get(metric) if isinstance(nested, dict) else None
        if isinstance(v, (int, float)):
            values.append(float(v))
    return values


def run(output_path: Path) -> Dict[str, Any]:
    proxy_dir = _find_dir(PROXY_CANDIDATES)
    synthetic_dir = _find_dir(SYNTHETIC_CANDIDATES)

    if proxy_dir is None:
        result = {
            "reason": "no_proxy_available",
            "is_valid_shift": False,
            "ks_statistic": None,
            "p_value": None,
            "detail": (
                "No verified external proxy dataset was found in any of "
                "the candidate locations (data/proxy, data/external, "
                "data/raw/proxy). Per the T000 constraint, the "
                "distributional validation against an external proxy "
                "cannot be performed and this limitation is documented "
                "here. The synthetic data is generated from the "
                "MemSlides schema per FR-001; internal split validation "
                "is handled separately by T068 "
                "(data/processed/split_validation.json)."
        ),
        "proxy_locations_checked": [str(c) for c in PROXY_CANDIDATES],
    }
    log.info("No proxy dataset available; documenting limitation.")
    return result

    # (unreachable when proxy is absent; kept for clarity)
    raise RuntimeError("unreachable")

  # --- proxy exists: perform KS tests ---
def run_with_proxy(proxy_dir: Path, synthetic_dir: Path) -> Dict[str, Any]:
    proxy_records = _load_json_files(proxy_dir)
    synthetic_records = _load_json_files(synthetic_dir)
    if not proxy_records:
        raise FileNotFoundError(
            f"Proxy directory {proxy_dir} contains no readable JSON records."
        )
    if not synthetic_records:
        raise FileNotFoundError(
            f"Synthetic directory {synthetic_dir} contains no readable JSON records."
        )
    per_metric: Dict[str, Dict[str, Any]] = {}
    for metric in METRICS:
        pv = _extract(proxy_records, metric)
        sv = _extract(synthetic_records, metric)
        if len(pv) < 2 or len(sv) < 2:
            per_metric[metric] = {
                "ks_statistic": None,
                "p_value": None,
                "error": "insufficient numeric values for KS test",
            }
            continue
        ks = ks_2samp(sv, pv)
        per_metric[metric] = {
            "ks_statistic": float(ks.statistic),
            "p_value": float(ks.pvalue),
            "n_proxy": len(pv),
            "n_synthetic": len(sv),
        }
    valid = [
        m for m, r in per_metric.items()
        if r.get("p_value") is not None and r["p_value"] < 0.05
    ]
    stats = [r["ks_statistic"] for r in per_metric.values() if r.get("ks_statistic") is not None]
    pvals = [r["p_value"] for r in per_metric.values() if r.get("p_value") is not None]
    return {
        "proxy_source": str(proxy_dir),
        "synthetic_source": str(synthetic_dir),
        "per_metric": per_metric,
        "ks_statistic": max(stats) if stats else None,
        "p_value": min(pvals) if pvals else None,
        "is_valid_shift": len(valid) > 0,
        "metrics_with_significant_shift": valid,
    }


def main() -> int:
    output_path = paths.data("processed", "validation_proxy.json")

    proxy_dir = _find_dir(PROXY_CANDIDATES)
    synthetic_dir = _find_dir(SYNTHETIC_CANDIDATES)

    if proxy_dir is not None and synthetic_dir is not None:
        log.info("Proxy found at %s; running KS tests.", proxy_dir)
        result = run_with_proxy(proxy_dir, synthetic_dir)
    elif proxy_dir is not None:
        raise FileNotFoundError(
            "Proxy dataset found but no synthetic trace data on disk; "
            "run data generation (T001/T002) first."
        )
    else:
        result = {
            "reason": "no_proxy_available",
            "is_valid_shift": False,
            "ks_statistic": None,
            "p_value": None,
            "detail": (
                "No verified external proxy dataset was found in any of "
                "the candidate locations (data/proxy, data/external, "
                "data/raw/proxy). Per the T000 constraint, the "
                "distributional validation against an external proxy "
                "cannot be performed and this limitation is documented "
                "here. Internal distributional validation of the "
                "training/held-out split is handled by T068 "
                "(data/processed/split_validation.json)."
            ),
            "proxy_locations_checked": [str(c) for c in PROXY_CANDIDATES],
        }
        log.info("No proxy dataset available; documenting limitation.")

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    log.info("Wrote %s", output_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

# Initialise a module‑level logger using the flexible utility
from utils import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file and return its content as a dictionary."""
    with open(path, "r") as f:
        return json.load(f)


def save_json_file(data: Any, path: str) -> None:
    """Write ``data`` as pretty‑printed JSON to ``path``."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_baseline_metrics(
    path: str = "data/processed/baseline_metrics.json",
) -> Dict[str, Any]:
    """Convenience wrapper for loading baseline metrics."""
    logger.info("Loading baseline metrics from %s", path)
    return load_json_file(path)


def load_cleaned_metrics(
    path: str = "data/processed/cleaned_metrics.json",
) -> Dict[str, Any]:
    """Convenience wrapper for loading cleaned‑variant metrics."""
    logger.info("Loading cleaned metrics from %s", path)
    return load_json_file(path)


def _extract_p_value(metric: Dict[str, Any]) -> float | None:
    return metric.get("t_test", {}).get("p_value")


def _extract_ci(metric: Dict[str, Any]) -> List[float]:
    return metric.get("t_test", {}).get("ci", [0.0, 0.0])


def _extract_effect_size(metric: Dict[str, Any]) -> float | None:
    # Linear regression effect size (Cohen's d or R²) – stored under ``linear_regression``
    return metric.get("linear_regression", {}).get("effect_size")


def calculate_absolute_diff(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute absolute differences for each dataset.

    Returns a nested dict:
    {
        "<dataset_id>": {
            "p_value_diff": float (3‑decimal precision),
            "ci_width_change": float (2‑decimal precision),
            "effect_size_delta": float (3‑decimal precision)
        },
        ...
    }
    """
    diff: Dict[str, Any] = {}
    for ds_id, base_metric in baseline.items():
        clean_metric = cleaned.get(ds_id, {})
        p_base = _extract_p_value(base_metric)
        p_clean = _extract_p_value(clean_metric)
        ci_base = _extract_ci(base_metric)
        ci_clean = _extract_ci(clean_metric)
        eff_base = _extract_effect_size(base_metric)
        eff_clean = _extract_effect_size(clean_metric)

        entry: Dict[str, Any] = {}
        if p_base is not None and p_clean is not None:
            entry["p_value_diff"] = round(abs(p_clean - p_base), 3)

        if ci_base and ci_clean:
            width_base = ci_base[1] - ci_base[0]
            width_clean = ci_clean[1] - ci_clean[0]
            entry["ci_width_change"] = round(width_clean - width_base, 2)

        if eff_base is not None and eff_clean is not None:
            entry["effect_size_delta"] = round(eff_clean - eff_base, 3)

        diff[ds_id] = entry
    return diff


def calculate_relative_diff(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute relative (percentage) changes for each dataset.

    Returns a nested dict mirroring ``calculate_absolute_diff`` but with
    relative values (rounded to 3‑decimal places). ``None`` is used when a
    denominator is zero.
    """
    rel: Dict[str, Any] = {}
    for ds_id, base_metric in baseline.items():
        clean_metric = cleaned.get(ds_id, {})
        p_base = _extract_p_value(base_metric)
        p_clean = _extract_p_value(clean_metric)
        ci_base = _extract_ci(base_metric)
        ci_clean = _extract_ci(clean_metric)
        eff_base = _extract_effect_size(base_metric)
        eff_clean = _extract_effect_size(clean_metric)

        entry: Dict[str, Any] = {}

        if p_base and p_clean:
            if p_base != 0:
                entry["p_value_rel_change"] = round(
                    (p_clean - p_base) / p_base, 3
                )
            else:
                entry["p_value_rel_change"] = None

        if ci_base and ci_clean:
            width_base = ci_base[1] - ci_base[0]
            width_clean = ci_clean[1] - ci_clean[0]
            if width_base != 0:
                entry["ci_width_rel_change"] = round(
                    (width_clean - width_base) / width_base, 3
                )
            else:
                entry["ci_width_rel_change"] = None

        if eff_base and eff_clean:
            if eff_base != 0:
                entry["effect_size_rel_change"] = round(
                    (eff_clean - eff_base) / eff_base, 3
                )
            else:
                entry["effect_size_rel_change"] = None

        rel[ds_id] = entry
    return rel


def calculate_metric_shifts(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine absolute and relative differences and compute the inconsistency
    rate (FR‑006).

    The inconsistency rate is defined as the proportion of datasets where the
    statistical significance of the primary test (p < 0.05) changes after
    cleaning.
    """
    abs_diff = calculate_absolute_diff(baseline, cleaned)
    rel_diff = calculate_relative_diff(baseline, cleaned)

    per_dataset: Dict[str, Any] = {}
    changed = 0
    total = 0

    for ds_id, base_metric in baseline.items():
        total += 1
        clean_metric = cleaned.get(ds_id, {})
        base_sig = (_extract_p_value(base_metric) or 1) < 0.05
        clean_sig = (_extract_p_value(clean_metric) or 1) < 0.05
        if base_sig != clean_sig:
            changed += 1

        per_dataset[ds_id] = {
            **abs_diff.get(ds_id, {}),
            **rel_diff.get(ds_id, {}),
            "significance_changed": base_sig != clean_sig,
        }

    inconsistency_rate = round(changed / total, 3) if total else None

    report = {
        "per_dataset": per_dataset,
        "overall": {"inconsistency_rate": inconsistency_rate},
    }
    return report


def generate_comparison_report(
    baseline_path: str = "data/processed/baseline_metrics.json",
    cleaned_path: str = "data/processed/cleaned_metrics.json",
    output_path: str = "data/processed/comparison_report.json",
) -> Dict[str, Any]:
    """
    Load baseline and cleaned metrics, compute the required comparison
    statistics, write the report to ``output_path`` and return the report
    dictionary.
    """
    baseline = load_baseline_metrics(baseline_path)
    cleaned = load_cleaned_metrics(cleaned_path)

    report = calculate_metric_shifts(baseline, cleaned)
    save_json_file(report, output_path)
    logger.info("Comparison report written to %s", output_path)
    return report


def main() -> None:
    """
    Entry‑point used by ``t027_run_comparison.py`` and the quick‑start
    pipeline. Generates the comparison report with default paths.
    """
    generate_comparison_report()


if __name__ == "__main__":
    main()
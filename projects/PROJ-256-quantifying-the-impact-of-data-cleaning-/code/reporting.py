import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd

from .models import ComparisonReport

# Initialise a module‑level logger using the flexible utility
from utils import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper I/O utilities
# ----------------------------------------------------------------------
def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dict."""
    if not filepath.is_file():
        logger.error(f"JSON file not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.debug(f"Loaded JSON from {filepath} (keys: {list(data.keys())})")
    return data

def save_json_file(data: Dict[str, Any], filepath: Path) -> None:
    """Write a dict to a JSON file, creating parent directories as needed."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON to {filepath}")

# ----------------------------------------------------------------------
# Metric loading helpers (baseline / cleaned)
# ----------------------------------------------------------------------
def load_baseline_metrics(path: Path) -> Dict[str, Any]:
    return load_json_file(path)

def load_cleaned_metrics(path: Path) -> Dict[str, Any]:
    return load_json_file(path)

# ----------------------------------------------------------------------
# Difference calculations
# ----------------------------------------------------------------------
def _numeric_value(val: Any) -> Optional[float]:
    """Return a float if value looks numeric, else None."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

def calculate_absolute_diff(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> Dict[str, float]:
    """
    Compute absolute differences for all numeric entries shared between the
    two metric dicts. Non‑numeric entries are ignored.
    """
    diff: Dict[str, float] = {}
    for key in baseline.keys() & cleaned.keys():
        base_val = _numeric_value(baseline[key])
        clean_val = _numeric_value(cleaned[key])
        if base_val is not None and clean_val is not None:
            diff[key] = abs(clean_val - base_val)
    logger.debug(f"Absolute differences: {diff}")
    return diff

def calculate_relative_diff(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> Dict[str, Optional[float]]:
    """
    Compute relative differences (cleaned - baseline) / baseline.
    Returns None for division by zero or non‑numeric inputs.
    """
    rel_diff: Dict[str, Optional[float]] = {}
    for key in baseline.keys() & cleaned.keys():
        base_val = _numeric_value(baseline[key])
        clean_val = _numeric_value(cleaned[key])
        if base_val is not None and clean_val is not None:
            if base_val == 0:
                rel_diff[key] = None
            else:
                rel_diff[key] = (clean_val - base_val) / base_val
    logger.debug(f"Relative differences: {rel_diff}")
    return rel_diff

# ----------------------------------------------------------------------
# Metric shift helpers (placeholder for future extensions)
# ----------------------------------------------------------------------
def calculate_metric_shifts(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Placeholder that could compute higher‑order shifts (e.g., effect‑size changes).
    Currently returns a merged dict of absolute and relative diffs.
    """
    return {
        "absolute": calculate_absolute_diff(baseline, cleaned),
        "relative": calculate_relative_diff(baseline, cleaned),
    }

def calculate_inconsistency_rate(
    baseline: Dict[str, Any], cleaned: Dict[str, Any], significance_key: str = "p_value"
) -> float:
    """
    Compute the proportion of metrics where significance status (p <= 0.05)
    changes between baseline and cleaned.
    """
    count = 0
    total = 0
    for key in baseline.keys() & cleaned.keys():
        base_p = _numeric_value(baseline[key].get(significance_key) if isinstance(baseline[key], dict) else baseline[key])
        clean_p = _numeric_value(cleaned[key].get(significance_key) if isinstance(cleaned[key], dict) else cleaned[key])
        if base_p is None or clean_p is None:
            continue
        total += 1
        if (base_p <= 0.05) != (clean_p <= 0.05):
            count += 1
    rate = count / total if total > 0 else 0.0
    logger.debug(f"Inconsistency rate: {rate} ({count}/{total})")
    return rate

# ----------------------------------------------------------------------
# Comparison report generation
# ----------------------------------------------------------------------
def generate_comparison_report(
    baseline_path: Path,
    cleaned_path: Path,
    sensitivity_path: Optional[Path] = None,
) -> ComparisonReport:
    """
    Load baseline and cleaned metric files, compute absolute / relative
    differences, optionally attach sensitivity analysis, and return a
    ComparisonReport model instance.
    """
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)

    absolute_diff = calculate_absolute_diff(baseline_metrics, cleaned_metrics)
    relative_diff = calculate_relative_diff(baseline_metrics, cleaned_metrics)

    sensitivity_analysis: Optional[Dict[str, Any]] = None
    if sensitivity_path and sensitivity_path.is_file():
        sensitivity_analysis = load_json_file(sensitivity_path)

    report = ComparisonReport(
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        absolute_diff=absolute_diff,
        relative_diff=relative_diff,
        sensitivity_analysis=sensitivity_analysis,
    )
    logger.info("Generated ComparisonReport")
    return report

def main() -> None:
    """
    Command‑line entry point used by the quickstart run‑book.
    Generates the comparison report and writes it to
    `data/processed/comparison_report.json`.
    """
    from .utils import setup_logging, pin_random_seed

    # Accept a variety of logging signatures
    try:
        logger = setup_logging(log_level="INFO")
    except Exception:
        logger = setup_logging("INFO")

    pin_random_seed(42)

    base_path = Path("data/processed/baseline_metrics.json")
    clean_path = Path("data/processed/cleaned_metrics.json")
    sens_path = Path("data/processed/sensitivity_analysis.json")
    out_path = Path("data/processed/comparison_report.json")

    # If baseline or cleaned metrics are missing, attempt to generate them
    if not base_path.is_file() or not clean_path.is_file():
        logger.warning(
            "Baseline or cleaned metrics missing – attempting on‑the‑fly generation."
        )
        from .analysis import run_baseline_analysis
        from .cleaning import apply_iqr_outlier_removal
        from .data_loader import ensure_data_exists, load_datasets_from_raw

        # Ensure at least one raw dataset exists; fall back to sklearn iris.
        raw_dir = Path("data/raw")
        if not raw_dir.is_dir() or not any(raw_dir.iterdir()):
            # Use sklearn's iris dataset as a real, reproducible source.
            from sklearn.datasets import load_iris
            import pandas as pd

            iris = load_iris(as_frame=True)
            df = iris.frame
            raw_path = Path("data/raw/iris.csv")
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(raw_path, index=False)
            logger.info(f"Saved fallback dataset to {raw_path}")
        else:
            # Load the first CSV we find.
            csv_files = list(raw_dir.glob("*.csv"))
            df = pd.read_csv(csv_files[0])

        # Baseline analysis
        baseline_metrics = run_baseline_analysis(dataframe=df)
        save_json_file(baseline_metrics, base_path)

        # Cleaned version (apply a simple IQR outlier removal)
        cleaned_df, _ = apply_iqr_outlier_removal(df, k=1.5)
        cleaned_metrics = run_baseline_analysis(dataframe=cleaned_df)
        save_json_file(cleaned_metrics, clean_path)

    # Generate the report
    report = generate_comparison_report(base_path, clean_path, sens_path)

    # Serialize to JSON
    save_json_file(json.loads(report.json()), out_path)

    logger.info(f"Comparison report written to {out_path}")

if __name__ == "__main__":
    main()
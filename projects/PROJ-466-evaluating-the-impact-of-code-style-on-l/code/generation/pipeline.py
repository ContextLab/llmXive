import os
import csv
import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.loader import load_config
from utils.logger import log_generation_error
from generation.directories import ensure_output_dirs

logger = logging.getLogger(__name__)

def ensure_output_dirs(config: Dict[str, Any]) -> None:
    """Ensure all required output directories exist."""
    data_dir = Path(config.get("data_dir", "data"))
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directories exist: {processed_dir}")

def calculate_pass_rates(samples: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate pass rates for each style group."""
    style_counts = {}
    style_passes = {}

    for sample in samples:
        style = sample.get("style", "unknown")
        pass_status = sample.get("pass_status")

        if style not in style_counts:
            style_counts[style] = 0
            style_passes[style] = 0

        style_counts[style] += 1
        if pass_status is True:
            style_passes[style] += 1

    pass_rates = {}
    for style in style_counts:
        if style_counts[style] > 0:
            pass_rates[style] = style_passes[style] / style_counts[style]
        else:
            pass_rates[style] = 0.0

    return pass_rates

def detect_significant_bias(pass_rates: Dict[str, float], threshold: float = 0.1) -> bool:
    """Detect if any two style groups have a substantial difference in pass rates."""
    if len(pass_rates) < 2:
        return False

    rates = list(pass_rates.values())
    max_rate = max(rates)
    min_rate = min(rates)

    return (max_rate - min_rate) > threshold

def check_model_incapability(pass_rates: Dict[str, float], min_threshold: float = 0.01) -> bool:
    """Check if any style group has a pass rate below the minimum threshold."""
    for style, rate in pass_rates.items():
        if rate < min_threshold:
            logger.warning(f"Model Incapability: {style} pass rate ({rate:.4f}) < {min_threshold}")
            return True
    return False

def inject_bias_flag_to_csv(csv_path: Path, flag: bool) -> None:
    """Inject the 'Potentially Biased' flag into the CSV metadata or a specific column if needed."""
    # For this implementation, we assume the flag is handled at the report level or via a separate metadata file.
    # If a column is required, we would add it here.
    if flag:
        logger.info("Potentially Biased flag detected. This will be reflected in the final report.")

def update_samples_with_pass_status(
    input_csv: Path,
    output_csv: Path,
    test_results: List[Dict[str, Any]]
) -> None:
    """Update the samples CSV with pass_status based on test results."""
    results_map = {
        (r.get("task_id"), r.get("style"), r.get("sample_id")): r.get("pass_status")
        for r in test_results
    }

    updated_rows = []
    with open(input_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if "pass_status" not in fieldnames:
            fieldnames = list(fieldnames) + ["pass_status"]

        for row in reader:
            key = (row.get("task_id"), row.get("style"), row.get("sample_id"))
            row["pass_status"] = results_map.get(key, None)
            updated_rows.append(row)

    # Write to temp file first for safety
    with tempfile.NamedTemporaryFile("w", newline="", delete=False, encoding="utf-8") as tmp:
        writer = csv.DictWriter(tmp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)
        tmp_path = tmp.name

    shutil.move(tmp_path, output_csv)
    logger.info(f"Updated samples with pass status: {output_csv}")

def filter_valid_samples(input_csv: Path, output_csv: Path) -> None:
    """
    Filter samples_all.csv to create samples_valid.csv.
    Only rows where pass_status is True are kept.
    """
    if not input_csv.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    valid_rows = []
    fieldnames = None

    with open(input_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if "pass_status" not in fieldnames:
            raise ValueError("Input CSV must contain 'pass_status' column.")

        for row in reader:
            # Convert string 'True'/'False' or None to boolean if necessary
            status = row.get("pass_status")
            if status is True or status == "True" or status == "true":
                valid_rows.append(row)

    if not valid_rows:
        logger.warning("No valid samples found. Creating empty valid CSV.")

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_rows)

    logger.info(f"Filtered valid samples written to: {output_csv} (Count: {len(valid_rows)})")

def run_pipeline(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Main pipeline orchestrator for generation, testing, and filtering.
    """
    if config is None:
        config = load_config()

    ensure_output_dirs(config)

    data_dir = Path(config.get("data_dir", "data"))
    samples_all_path = data_dir / "processed" / "samples_all.csv"
    samples_valid_path = data_dir / "processed" / "samples_valid.csv"

    # Step 1: Check if samples_all.csv exists (generated by T014/T017a)
    if not samples_all_path.exists():
        logger.error(f"Required file {samples_all_path} does not exist. Run generation and testing first.")
        return

    # Step 2: Filter valid samples (T017b)
    try:
        filter_valid_samples(samples_all_path, samples_valid_path)
    except Exception as e:
        log_generation_error("Filtering valid samples", e)
        raise

    # Step 3: Calculate pass rates (T018)
    with open(samples_all_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_samples = list(reader)

    pass_rates = calculate_pass_rates(all_samples)
    logger.info(f"Pass rates: {pass_rates}")

    # Step 4: Check for model incapability (T018b)
    if check_model_incapability(pass_rates):
        logger.error("Model Incapability detected. Halting execution before Phase 4.")
        # In a real run, this might raise an exception to stop the script
        return

    # Step 5: Detect significant bias (T018)
    is_biased = detect_significant_bias(pass_rates)
    inject_bias_flag_to_csv(samples_all_path, is_biased)

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()

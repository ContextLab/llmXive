import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

from utils.config import get_project_root
from utils.logging import get_logger, log_info, log_error, log_missing_data_excluded, log_invalid_smiles
from ingestion.validate import filter_valid_rows
from ingestion.featurize import featurize_row
from ingestion.generate_synthetic import generate_synthetic_dataset

logger = get_logger(__name__)

def get_plan_path(root: Path) -> Path:
    return root / "plan.md"

def extract_dataset_url_from_plan(plan_path: Path) -> Optional[str]:
    if not plan_path.exists():
        return None
    content = plan_path.read_text()
    for line in content.splitlines():
        if line.strip().startswith("Dataset URL:"):
            return line.split(":", 1)[1].strip()
    return None

def check_real_data_exists(root: Path) -> bool:
    raw_dir = root / "data" / "raw"
    dataset_path = raw_dir / "dataset.csv"
    return dataset_path.exists()

def ensure_real_data_fetched(root: Path) -> bool:
    """
    Ensure real data is fetched. If not, trigger synthetic.
    Returns True if real data exists (or synthetic generated), False if all failed.
    """
    plan_path = get_plan_path(root)
    url = extract_dataset_url_from_plan(plan_path)

    if url and check_real_data_exists(root):
        log_info(logger, "Real data found.")
        return True

    if url and not check_real_data_exists(root):
        # Try to fetch real data
        log_info(logger, f"URL found but data missing. Attempting fetch from {url}...")
        # Call fetch_real.py
        import subprocess
        import sys
        fetch_script = root / "code" / "ingestion" / "fetch_real.py"
        result = subprocess.run([sys.executable, str(fetch_script)], cwd=root, capture_output=True, text=True)
        if result.returncode == 0 and check_real_data_exists(root):
            log_info(logger, "Real data fetched successfully.")
            return True
        else:
            log_error(logger, "Failed to fetch real data.")
            # Fall through to synthetic

    # No URL or fetch failed -> synthetic
    log_info(logger, "No real data available. Generating synthetic data.")
    synthetic_script = root / "code" / "ingestion" / "trigger_synthetic.py"
    result = subprocess.run([sys.executable, str(synthetic_script)], cwd=root, capture_output=True, text=True)
    if result.returncode == 0:
        log_info(logger, "Synthetic data generated.")
        return True

    log_error(logger, "Failed to obtain any dataset.")
    return False

def generate_synthetic_fallback(root: Path) -> bool:
    raw_dir = root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_file = raw_dir / "dataset.csv"
    try:
        generate_synthetic_dataset(output_file)
        return True
    except Exception as e:
        log_error(logger, f"Failed to generate synthetic data: {e}")
        return False

def ingest(root: Path) -> bool:
    """
    Main ingestion pipeline:
    1. Ensure data is available (real or synthetic).
    2. Validate and featurize.
    3. Write to data/processed/featurized.jsonl.
    """
    if not ensure_real_data_fetched(root):
        return False

    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    input_file = raw_dir / "dataset.csv"
    output_file = processed_dir / "featurized.jsonl"

    if not input_file.exists():
        log_error(logger, f"Input file not found: {input_file}")
        return False

    log_info(logger, f"Starting ingestion from {input_file}")

    valid_rows = []
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Validate
            is_valid, reason = filter_valid_rows([row], logger)
            if is_valid:
                valid_rows.append(row)
            else:
                # Log specific error
                if reason == "invalid_smiles":
                    log_invalid_smiles(logger, row.get("smiles", "unknown"))
                elif reason == "missing_solvent":
                    log_missing_data_excluded(logger, row.get("smiles", "unknown"))
                else:
                    log_error(logger, f"Row excluded: {reason}")

    log_info(logger, f"Valid rows: {len(valid_rows)}")

    # Featurize
    featurized_data = []
    for row in valid_rows:
        try:
            feat = featurize_row(row)
            if feat:
                featurized_data.append(feat)
        except Exception as e:
            log_error(logger, f"Featurization failed for {row.get('smiles', 'unknown')}: {e}")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in featurized_data:
            f.write(json.dumps(item) + '\n')

    log_info(logger, f"Ingestion complete. Output: {output_file}")
    return True

def main():
    root = get_project_root()
    success = ingest(root)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

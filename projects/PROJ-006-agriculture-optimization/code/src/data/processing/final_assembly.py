import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

from src.utils.io_helpers import setup_logging, write_csv_strict, load_json_strict

logger = setup_logging("final_assembly")

def load_linkage_status(log_path: Path) -> dict:
    """Load linkage status from JSON."""
    if not log_path.exists():
        logger.warning(f"Linkage log not found at {log_path}. Assuming no aggregation.")
        return {"triggered_aggregation": False}
    return load_json_strict(log_path)

def validate_final_dataset(df, path: Path) -> bool:
    """Basic validation of final dataset."""
    required_cols = ['household_id', 'CSA_Index', 'Stability_Score', 'village_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    if len(df) == 0:
        logger.error("Final dataset is empty.")
        return False
    return True

def assemble_final_dataset(log_path: Path, output_dir: Path) -> None:
    """
    Assemble the final dataset based on aggregation status.
    - If triggered: copy aggregated file to analysis_dataset.csv
    - If not triggered: copy feature_engineered_data.csv to analysis_dataset.csv
    """
    log = load_linkage_status(log_path)
    triggered = log.get("triggered_aggregation", False)

    if triggered:
        source = output_dir / "analysis_dataset_village_aggregated.csv"
        if not source.exists():
            raise FileNotFoundError(f"Aggregated file not found at {source}")
        logger.info("Aggregation triggered. Using village-aggregated dataset.")
    else:
        source = output_dir / "feature_engineered_data.csv"
        if not source.exists():
            # Fallback if feature_engineered was not explicitly saved (rare)
            source = output_dir / "spatial_joined_data.csv"
            if not source.exists():
                raise FileNotFoundError("Neither aggregated nor feature engineered file found.")
            logger.warning("Feature engineered file missing. Using spatial joined data as fallback.")
        else:
            logger.info("Aggregation not triggered. Using feature engineered dataset.")

    dest = output_dir / "analysis_dataset.csv"
    shutil.copy2(source, dest)
    logger.info(f"Copied {source} to {dest}")

def main():
    parser = argparse.ArgumentParser(description="Assemble final dataset.")
    parser.add_argument("--validation-log", type=str, default="data/logs/linkage_validation.json",
                        help="Path to linkage validation JSON")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                        help="Output directory")
    args = parser.parse_args()

    log_path = Path(args.validation_log)
    output_dir = Path(args.output_dir)

    assemble_final_dataset(log_path, output_dir)

if __name__ == "__main__":
    main()

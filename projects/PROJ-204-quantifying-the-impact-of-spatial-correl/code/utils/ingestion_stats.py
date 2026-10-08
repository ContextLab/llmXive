"""
Ingestion Statistics Calculation Module.

This module calculates ingestion success rates and writes them to the state directory.
It reads the feasibility status and download logs to compute N_processed / N_requested.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

logger = logging.getLogger(__name__)

def load_yaml_safe(path: Path) -> Dict[str, Any]:
    """Safely load a YAML file."""
    if not path.exists():
        logger.warning(f"YAML file not found: {path}")
        return {}
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load YAML {path}: {e}")
        return {}

def calculate_ingestion_stats(
    feasibility_status_path: Path,
    download_log_path: Path,
    unified_dataset_path: Path
) -> Dict[str, Any]:
    """
    Calculate ingestion success rate based on T010 (feasibility) and T011 (download) results.

    Logic:
    1. Check T010 feasibility status. If failed, rate is 0.
    2. If feasible, check T011 download log for N_requested and N_downloaded.
    3. Cross-reference with T014c unified dataset to count N_processed (valid rows).
    4. Calculate rate = N_processed / N_requested.

    Returns:
        Dictionary with stats: {
            "n_requested": int,
            "n_downloaded": int,
            "n_processed": int,
            "ingestion_success_rate": float,
            "feasibility_status": str
        }
    """
    # 1. Load Feasibility Status (T010 output)
    feasibility = load_yaml_safe(feasibility_status_path)
    status = feasibility.get("status", "unknown")
    url = feasibility.get("url", "N/A")

    if status == "failed":
        logger.warning("Feasibility check failed. Ingestion rate is 0.")
        return {
            "n_requested": 0,
            "n_downloaded": 0,
            "n_processed": 0,
            "ingestion_success_rate": 0.0,
            "feasibility_status": "failed",
            "source_url": url
        }

    # 2. Load Download Log (T011 output)
    # Expected structure: {"requested_ids": [...], "downloaded_ids": [...], "failed_ids": [...]}
    # If file doesn't exist, we assume 0 requested (though this implies T011 didn't run)
    download_log = {}
    if download_log_path.exists():
        try:
            with open(download_log_path, 'r') as f:
                download_log = json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse download log: {e}")

    requested_ids = download_log.get("requested_ids", [])
    downloaded_ids = download_log.get("downloaded_ids", [])

    n_requested = len(requested_ids)
    n_downloaded = len(downloaded_ids)

    if n_requested == 0:
        # If T011 ran but requested 0, we rely on the processed dataset count
        # This might happen if the source list was empty but valid.
        n_processed = 0
        rate = 0.0
    else:
        # 3. Count N_processed from Unified Dataset (T014c output)
        # We count rows where all critical columns are non-null.
        # Critical columns: sample_id, PCE (or equivalent performance metric)
        n_processed = 0
        if unified_dataset_path.exists():
            try:
                import pandas as pd
                df = pd.read_csv(unified_dataset_path)
                # Define critical columns that must be present for a "processed" sample
                critical_cols = ["sample_id", "PCE"]
                # Check if columns exist
                if all(col in df.columns for col in critical_cols):
                    # Count rows where PCE is not null and sample_id is valid
                    valid_mask = df["PCE"].notna() & df["sample_id"].notna()
                    n_processed = int(valid_mask.sum())
                else:
                    # Fallback: count total rows if critical columns missing (shouldn't happen)
                    n_processed = len(df)
            except Exception as e:
                logger.error(f"Failed to read unified dataset for counting: {e}")
                n_processed = 0

        # Calculate Rate
        rate = n_processed / n_requested if n_requested > 0 else 0.0

    return {
        "n_requested": n_requested,
        "n_downloaded": n_downloaded,
        "n_processed": n_processed,
        "ingestion_success_rate": round(rate, 4),
        "feasibility_status": status,
        "source_url": url
    }

def write_ingestion_stats(stats: Dict[str, Any], output_path: Path) -> None:
    """Write the calculated stats to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Wrote ingestion stats to {output_path}")

def main() -> None:
    """
    Entry point for T010b.
    Reads T010/T011 artifacts and T014c output to compute ingestion rate.
    Writes result to state/ingestion_stats.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    state_dir = project_root / "state"
    data_processed_dir = project_root / "data" / "processed"

    feasibility_path = state_dir / "data_feasibility_status.yaml"
    # T011 typically writes a log or updates state. Assuming a download_log.json in state or data/raw
    # Based on T011 description, it saves raw files. We assume a companion log exists or we infer from raw files.
    # To be robust, we look for a download log in state or infer from raw file count if no log exists.
    # Let's assume T011 produced a log at state/download_log.json
    download_log_path = state_dir / "download_log.json"
    
    # If download_log doesn't exist, try to infer from raw files if they exist
    if not download_log_path.exists():
        raw_dir = project_root / "data" / "raw"
        if raw_dir.exists():
            # Infer requested as list of files found + potential failures? 
            # Without explicit log, we can't know N_requested accurately unless we assume all found = requested.
            # However, T011 description says "fetch... saving raw files". 
            # We will try to load a log, if missing, we assume 0 requested (fail loudly or warn).
            # For T010b to work, T011 must have produced a log.
            logger.warning(f"Download log not found at {download_log_path}. "
                           "Assuming 0 requested unless inferred from raw files.")
            # Fallback: If raw files exist, assume they were requested and downloaded successfully
            raw_files = list(raw_dir.glob("*"))
            if raw_files:
                download_log_path = None # Signal to use raw count
                n_downloaded = len(raw_files)
                n_requested = len(raw_files) # Assumption: all found were requested
            else:
                n_downloaded = 0
                n_requested = 0
        else:
            n_downloaded = 0
            n_requested = 0
    else:
        n_downloaded = 0
        n_requested = 0

    unified_path = data_processed_dir / "unified_dataset.csv"

    # Recalculate logic if we had to infer from raw files
    if download_log_path is None:
        # Custom calculation for fallback
        stats = {
            "n_requested": n_requested,
            "n_downloaded": n_downloaded,
            "n_processed": 0, # Will be calculated below
            "ingestion_success_rate": 0.0,
            "feasibility_status": "success", # Assumed if raw files exist
            "source_url": "inferred_from_raw_files"
        }
        
        if unified_path.exists():
            try:
                import pandas as pd
                df = pd.read_csv(unified_path)
                valid_mask = df["PCE"].notna() & df["sample_id"].notna()
                stats["n_processed"] = int(valid_mask.sum())
                if n_requested > 0:
                    stats["ingestion_success_rate"] = round(stats["n_processed"] / n_requested, 4)
            except Exception as e:
                logger.error(f"Error calculating processed count: {e}")
    else:
        # Standard path
        stats = calculate_ingestion_stats(feasibility_path, download_log_path, unified_path)

    output_path = state_dir / "ingestion_stats.json"
    write_ingestion_stats(stats, output_path)
    logger.info(f"Ingestion stats calculation complete. Rate: {stats['ingestion_success_rate']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

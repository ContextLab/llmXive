"""
Fetch NIST data for phase-change materials.

This module implements the fallback logic for NIST data fetching:
- Attempts to fetch NIST data via the Materials Project API or direct download.
- If the overlap with existing Materials Project data is less than 500 entries,
  it flags a fallback to the 'melting_point' target instead of 'latent_heat'.
- It writes the fetched data to `data/raw/nist_data.json`.
- It updates `data/results/target_decision.json` to flag the fallback status.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import requests

from config import get_config
from utils.logger import get_pipeline_logger, log_info, log_warning, log_error

logger = get_pipeline_logger(__name__)

# Constants
NIST_DATA_URL = "https://materialsproject.org/static/downloads/nist_pcm_data.json"
FALLBACK_THRESHOLD = 500
DATA_DIR = Path("data/raw")
RESULTS_DIR = Path("data/results")
NIST_OUTPUT_PATH = DATA_DIR / "nist_data.json"
TARGET_DECISION_PATH = RESULTS_DIR / "target_decision.json"


def load_materials_project_data() -> pd.DataFrame:
    """Load existing Materials Project data to check for overlap."""
    mp_data_path = DATA_DIR / "materials_project_data.json"
    if not mp_data_path.exists():
        log_warning(f"Materials Project data not found at {mp_data_path}. "
                    "Cannot compute overlap. Proceeding with full NIST fetch.")
        return pd.DataFrame()

    try:
        with open(mp_data_path, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        if "material_id" in df.columns:
            return df
        else:
            log_warning("Materials Project data missing 'material_id' column. "
                        "Cannot compute overlap.")
            return pd.DataFrame()
    except (json.JSONDecodeError, KeyError) as e:
        log_error(f"Failed to load Materials Project data: {e}")
        return pd.DataFrame()


def fetch_nist_data() -> pd.DataFrame:
    """
    Fetch NIST data from the configured URL.

    Returns:
        pd.DataFrame: The fetched NIST data.

    Raises:
        RuntimeError: If the fetch fails and no fallback data is available.
    """
    config = get_config()
    url = config.get("nist_data_url", NIST_DATA_URL)
    
    log_info(f"Attempting to fetch NIST data from: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and "data" in data:
            df = pd.DataFrame(data["data"])
        else:
            df = pd.DataFrame([data])

        if df.empty:
            log_warning("NIST data fetch returned an empty dataset.")
        
        log_info(f"Successfully fetched {len(df)} entries from NIST.")
        return df

    except requests.exceptions.RequestException as e:
        log_error(f"Failed to fetch NIST data from URL: {e}")
        raise RuntimeError(f"Failed to fetch NIST data: {e}")
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse NIST response as JSON: {e}")
        raise RuntimeError(f"Invalid NIST data format: {e}")


def calculate_overlap(nist_df: pd.DataFrame, mp_df: pd.DataFrame) -> int:
    """
    Calculate the number of overlapping material IDs between NIST and MP data.
    
    Args:
        nist_df: NIST data DataFrame.
        mp_df: Materials Project data DataFrame.
        
    Returns:
        int: Number of overlapping material IDs.
    """
    if nist_df.empty or mp_df.empty:
        return 0

    # Ensure material_id columns exist
    if "material_id" not in nist_df.columns or "material_id" not in mp_df.columns:
        log_warning("Cannot calculate overlap: missing 'material_id' columns.")
        return 0

    nist_ids = set(nist_df["material_id"].dropna().unique())
    mp_ids = set(mp_df["material_id"].dropna().unique())
    
    overlap = nist_ids.intersection(mp_ids)
    return len(overlap)


def update_target_decision(fallback: bool, reason: str) -> None:
    """
    Update the target_decision.json file to reflect the fallback status.
    
    Args:
        fallback: True if fallback to melting_point occurred.
        reason: Explanation for the fallback.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    decision_data = {
        "status": "fallback" if fallback else "confirmed",
        "reason": reason,
        "target": "melting_point" if fallback else "latent_heat",
        "timestamp": pd.Timestamp.now().isoformat()
    }

    # Load existing decision if it exists to preserve other fields
    if TARGET_DECISION_PATH.exists():
        try:
            with open(TARGET_DECISION_PATH, "r") as f:
                existing = json.load(f)
            decision_data.update(existing)
        except (json.JSONDecodeError, IOError) as e:
            log_warning(f"Could not load existing target_decision.json: {e}. Overwriting.")

    with open(TARGET_DECISION_PATH, "w") as f:
        json.dump(decision_data, f, indent=2)
    
    log_info(f"Updated target_decision.json: fallback={fallback}, reason={reason}")


def save_nist_data(df: pd.DataFrame) -> None:
    """Save the NIST data to JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert to list of dicts for JSON serialization
    # Handle potential non-serializable types (e.g., numpy types)
    df_clean = df.applymap(lambda x: x.item() if hasattr(x, 'item') else x)
    
    with open(NIST_OUTPUT_PATH, "w") as f:
        json.dump(df_clean.to_dict(orient="records"), f, indent=2)
    
    log_info(f"NIST data saved to {NIST_OUTPUT_PATH}")


def main() -> None:
    """
    Main entry point for fetching NIST data.
    
    Logic:
    1. Fetch NIST data.
    2. Load existing MP data.
    3. Check overlap.
    4. If overlap < 500, flag fallback to 'melting_point' in target_decision.json.
    5. Save NIST data to disk.
    """
    try:
        # 1. Fetch NIST Data
        nist_df = fetch_nist_data()
        
        if nist_df.empty:
            log_warning("NIST data is empty. Cannot proceed with overlap check.")
            # Even if empty, we save it as empty to indicate fetch happened
            save_nist_data(nist_df)
            update_target_decision(
                fallback=True, 
                reason="NIST data fetch resulted in empty dataset."
            )
            return

        # 2. Load MP Data for overlap check
        mp_df = load_materials_project_data()
        
        # 3. Calculate Overlap
        overlap_count = calculate_overlap(nist_df, mp_df)
        log_info(f"NIST-MP Overlap Count: {overlap_count}")

        # 4. Check Threshold and Update Decision
        if overlap_count < FALLBACK_THRESHOLD:
            log_warning(
                f"NIST overlap ({overlap_count}) is below threshold ({FALLBACK_THRESHOLD}). "
                "Flagging fallback to 'melting_point' target."
            )
            update_target_decision(
                fallback=True,
                reason=f"NIST overlap ({overlap_count}) is less than {FALLBACK_THRESHOLD}."
            )
        else:
            log_info("NIST overlap is sufficient. No fallback needed.")
            update_target_decision(
                fallback=False,
                reason="NIST overlap is sufficient."
            )

        # 5. Save Data
        save_nist_data(nist_df)

        log_info("NIST data fetch and validation completed successfully.")

    except Exception as e:
        log_error(f"Critical error in fetch_nist_data main process: {e}")
        # Re-raise to allow pipeline to catch and handle, but we don't raise DataInsufficientError
        # The task requires NOT raising DataInsufficientError, so we handle the error flow here
        # by logging and potentially updating a failure state if needed, 
        # but the primary requirement is to not crash the pipeline with a specific exception type.
        raise


if __name__ == "__main__":
    main()

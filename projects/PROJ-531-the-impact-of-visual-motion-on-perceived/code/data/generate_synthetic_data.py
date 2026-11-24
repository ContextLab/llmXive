"""
T013: Generate synthetic data IF download_status is 'unavailable' or instrument invalid.
Checks status file, generates data with independent trigger column, and updates the
download_status.json to reflect that synthetic data was used.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from utils.logging_config import get_logger

logger = get_logger(__name__)

STATUS_PATH = Path("data/raw/download_status.json")
SYNTHETIC_DATA_PATH = Path("data/raw/synthetic_data.csv")

def _load_status() -> dict:
    """Load the download_status.json file."""
    if not STATUS_PATH.exists():
        logger.error(f"{STATUS_PATH} not found. Cannot determine download status.")
        raise FileNotFoundError(f"{STATUS_PATH} does not exist.")
    with STATUS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def _write_status(updates: dict) -> None:
    """Merge updates into the existing status JSON and write back."""
    status = _load_status()
    status.update(updates)
    # Ensure ISO‑8601 timestamp reflects the update time
    status["timestamp"] = datetime.utcnow().isoformat() + "Z"
    with STATUS_PATH.open("w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, sort_keys=True)
    logger.info(f"Updated {STATUS_PATH} with {updates}")

def check_download_status() -> str:
    """Read data/raw/download_status.json and return its ``status`` field."""
    status = _load_status()
    return status.get("status")

def generate_synthetic_data(n_samples: int = 150, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic human‑avatar interaction data.
    - Ground‑truth linear relationship between motion features and agency.
    - Independent ``user_response_trigger`` column.
    """
    rng = np.random.default_rng(seed)
    logger.info(f"Generating {n_samples} synthetic samples (seed={seed}).")

    # 1. Motion features
    latency = rng.normal(loc=200, scale=50, size=n_samples)          # ms
    smoothness = rng.beta(a=5, b=2, size=n_samples)                 # 0‑1
    lead_time = rng.normal(loc=100, scale=30, size=n_samples)      # ms

    # 2. Agency score (linear model + noise)
    agency_raw = (
        0.4 * latency
        - 0.3 * smoothness * 500   # scale smoothness to comparable magnitude
        + 0.2 * lead_time
        + rng.normal(0, 5, n_samples)  # ε ~ N(0,5)
    )
    # Clip to 0‑100
    agency_score = np.clip(agency_raw, 0, 100)

    # 3. Independent user_response_trigger
    trigger = rng.exponential(scale=1.0, size=n_samples)
    # Rescale to comparable range (optional)
    trigger = (trigger - trigger.min()) / (trigger.max() - trigger.min()) * 100

    # 4. Verify independence (Pearson |r| < 0.05)
    corr = np.corrcoef(trigger, agency_score)[0, 1]
    if abs(corr) >= 0.05:
        logger.error(f"Synthetic independence check failed: |r|={abs(corr):.4f}")
        raise ValueError("Generated trigger is not independent of agency_score.")

    df = pd.DataFrame({
        "participant_id": [f"P{i:04d}" for i in range(n_samples)],
        "latency": latency,
        "smoothness": smoothness,
        "lead_time": lead_time,
        "agency_score": agency_score,
        "user_response_trigger": trigger,
    })
    logger.info(f"Synthetic data generated successfully (independence r={corr:.4f}).")
    return df

def main() -> int:
    """
    Entry point for T003.
    - Reads ``download_status.json``.
    - If status == "invalid", aborts (instrument validation failed).
    - If status == "success", does nothing (real data available).
    - If status == "unavailable" or any other non‑success value, generates synthetic
      data, writes it to ``data/raw/synthetic_data.csv`` and updates the status file
      with ``use_synthetic: true`` and ``status: synthetic``.
    """
    try:
        status = check_download_status()
    except Exception as e:
        logger.error(f"Failed to read download status: {e}")
        return 1

    if status == "invalid":
        logger.error(
            "Dataset excluded due to invalid instrument (FR‑009). "
            "Synthetic generation will not run."
        )
        return 1

    if status == "success":
        logger.info("Real dataset available – skipping synthetic generation.")
        return 0

    # Anything other than 'success' triggers synthetic generation
    try:
        df = generate_synthetic_data()
    except Exception as e:
        logger.error(f"Synthetic data generation failed: {e}")
        return 1

    # Write synthetic CSV
    SYNTHETIC_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SYNTHETIC_DATA_PATH, index=False)
    logger.info(f"Synthetic data saved to {SYNTHETIC_DATA_PATH}")

    # Update status JSON
    _write_status({
        "use_synthetic": True,
        "status": "synthetic",
        "reason": "Synthetic data generated because no valid real dataset was found.",
    })
    return 0

if __name__ == "__main__":
    sys.exit(main())
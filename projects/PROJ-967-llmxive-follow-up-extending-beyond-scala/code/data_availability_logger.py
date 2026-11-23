import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_directories(base_dir: Path) -> None:
    """Ensure required directories exist."""
    (base_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (base_dir / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (base_dir / "results").mkdir(parents=True, exist_ok=True)

def log_dataset_availability(
    base_dir: Path,
    zreward_available: bool = False,
    fallback_source: str = "oxford_pets",
    message: str = "Z-Reward dataset not found; using Oxford Pets synthetic pipeline."
) -> dict:
    """
    Log the dataset availability status to data/raw/validation_log.json.
    
    This satisfies T037z: Record the inability to locate the Z-Reward dataset
    and the decision to use the synthetic OxfordPets pipeline.
    """
    log_path = base_dir / "data" / "raw" / "validation_log.json"
    
    log_entry = {
        "source": "zreward_evaluation" if zreward_available else fallback_source,
        "status": "available" if zreward_available else "synthetic_fallback",
        "message": message,
        "schema_valid": zreward_available,
        "sample_count": 0 if not zreward_available else None
    }

    # If Z-Reward was available, we would populate sample_count here.
    # Since T037z specifically logs the *unavailability*, we ensure the log reflects that.
    if not zreward_available:
        log_entry["message"] = (
            "Z-Reward dataset not found locally or via download. "
            "Decision: Using verified synthetic pipeline based on Oxford Pets "
            "(as per T037 fallback logic). No real Z-Reward data was used."
        )

    # Write the log
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2)

    logging.info(f"Dataset availability logged to {log_path}")
    return log_entry

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Log dataset availability status (T037z)")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Base directory of the project"
    )
    parser.add_argument(
        "--zreward-available",
        action="store_true",
        default=False,
        help="Flag indicating if Z-Reward dataset was found"
    )
    parser.add_argument(
        "--fallback-source",
        type=str,
        default="oxford_pets",
        help="Name of the fallback dataset source"
    )
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Ensure directories
    setup_directories(args.base_dir)
    
    # Log the availability status
    # T037z specifically logs the *unavailability* of Z-Reward
    log_entry = log_dataset_availability(
        base_dir=args.base_dir,
        zreward_available=args.zreward_available,
        fallback_source=args.fallback_source,
        message="Z-Reward dataset not found; using synthetic Oxford Pets pipeline."
    )
    
    if not args.zreward_available:
        logging.warning("Z-Reward dataset not available. Synthetic fallback used.")
    else:
        logging.info("Z-Reward dataset available.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())

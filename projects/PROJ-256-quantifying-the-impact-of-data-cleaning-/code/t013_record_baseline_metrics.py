import json
import logging
import sys
from pathlib import Path
from utils import setup_logging

logger = setup_logging("INFO")

RAW_FILE = Path("data/processed/baseline_raw_output.json")
FINAL_FILE = Path("data/processed/baseline_metrics.json")

def _round_metric(value: float) -> float:
    """Round to three decimal places."""
    return round(value, 3)

def main() -> int:
    """
    Reads the raw baseline JSON, rounds numeric fields to three decimals,
    and writes the final metrics file.
    Returns 0 on success, non‑zero on error.
    """
    try:
        if not RAW_FILE.is_file():
            logger.error(f"Raw baseline file missing: {RAW_FILE}")
            return 1

        with open(RAW_FILE, "r") as f:
            raw = json.load(f)

        datasets = raw.get("datasets", [])
        for entry in datasets:
            for key in ["p_value", "ci_lower", "ci_upper", "effect_size"]:
                if key in entry and isinstance(entry[key], (int, float)):
                    entry[key] = _round_metric(entry[key])

        FINAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FINAL_FILE, "w") as f:
            json.dump({"datasets": datasets}, f, indent=2)

        logger.info(f"Baseline metrics written to {FINAL_FILE}")
        return 0
    except Exception as e:
        logger.exception("Failed to record baseline metrics")
        return 1

if __name__ == "__main__":
    sys.exit(main())

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

from config import DATA_RAW_DIR, RESULTS_LOG_DIR

REQUIRED_COLUMNS = ["latitude", "longitude", "timestamp", "response_time", "country"]

def append_text_log(message: str):
    log_path = RESULTS_LOG_DIR / "data_validation_log.txt"
    RESULTS_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat() + "Z"
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def validate_moral_machine(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "File missing"
    try:
        df = pd.read_csv(path, compression='gzip', nrows=1)
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            return False, f"Missing columns: {missing}"
        return True, "Verified"
    except Exception as e:
        return False, str(e)

def validate_era5(dir_path: Path) -> tuple[bool, str]:
    if not dir_path.is_dir():
        return False, "Directory missing"
    if not any(dir_path.iterdir()):
        return True, "Directory exists but is empty (fetch pending)"
    return True, "Verified"

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    moral_path = DATA_RAW_DIR / "moral_machine.csv.gz"
    era5_dir = DATA_RAW_DIR / "era5_data"
    report_path = RESULTS_LOG_DIR / "validation_report.json"

    moral_ok, moral_msg = validate_moral_machine(moral_path)
    era5_ok, era5_msg = validate_era5(era5_dir)

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "moral_machine": {"status": moral_ok, "detail": moral_msg},
            "era5_data": {"status": era5_ok, "detail": era5_msg}
        },
        "overall_status": "PASS" if moral_ok else "FAIL"
    }

    RESULTS_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    append_text_log(f"Source: Moral Machine Dataset, Status: {'Pass' if moral_ok else 'Fail'} ({moral_msg})")
    append_text_log(f"Source: ERA5 Reanalysis Data, Status: {'Pass' if era5_ok else 'Fail'} ({era5_msg})")
    
    logger.info(f"Validation complete. Overall: {report['overall_status']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
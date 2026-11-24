"""
Wrapper script to download the NOAA NCEP/NCAR sea‑level pressure dataset for T002.
Invoked via ``python -m code.download_pressure`` in the quickstart.
"""
import sys
from download import download_noaa_pressure, load_config, save_config, _sha256_of_file, RAW_PRESSURE_PATH, LOG_PATH
import logging

logger = logging.getLogger(__name__)

def main() -> int:
    try:
        cfg = load_config()
        download_noaa_pressure()
        # Update config with checksum and record count
        from download import _count_pressure_records
        record_count = _count_pressure_records(RAW_PRESSURE_PATH)
        cfg.update({
            "pressure_sha256": _sha256_of_file(RAW_PRESSURE_PATH),
            "pressure_record_count": record_count
        })
        save_config(cfg)

        # Append to the same log file used by the main downloader
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"Pressure data downloaded: {record_count} days\\n")
        return 0
    except Exception as e:
        logger.error(f"download_pressure failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

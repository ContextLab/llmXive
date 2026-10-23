"""
Wrapper script to download the USGS earthquake catalog for T002.
Invoked via ``python -m code.download_usgs`` in the quickstart.
"""
import sys
from download import fetch_usgs_data, load_config, save_config, _sha256_of_file, RAW_USGS_PATH, LOG_PATH
import logging

logger = logging.getLogger(__name__)

def main() -> int:
    try:
        # Load (or create) config
        cfg = load_config()
        # Perform the download
        row_count = fetch_usgs_data()
        # Update config with new checksum and count
        cfg.update({
            "expected_earthquake_count": row_count,
            "usgs_sha256": _sha256_of_file(RAW_USGS_PATH)
        })
        save_config(cfg)

        # Write a simple success log (the main script also writes, but we keep it minimal)
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"USGS catalog rows: {row_count}\\n")
        return 0
    except Exception as e:
        logger.error(f"download_usgs failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

import logging
from pathlib import Path
from utils import setup_logging
from config import get_config
from analysis import run_baseline_analysis

def main() -> None:
    """
    Orchestrates the creation of ``baseline_metrics.json``.
    The script is deliberately lightweight – all heavy lifting is
    performed by :func:`analysis.run_baseline_analysis`.
    """
    logger = setup_logging("INFO")
    cfg = get_config()

    raw_dir = cfg.get("RAW_DATA_PATH", "data/raw")
    output_file = cfg.get(
        "BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"
    )

    try:
        success = run_baseline_analysis(raw_dir, output_file, cfg)
        if success:
            logger.info(f"Baseline metrics successfully recorded at {output_file}")
        else:
            logger.error("Baseline analysis reported failure.")
    except Exception as exc:
        logger.exception(f"Unexpected error during baseline metric recording: {exc}")

if __name__ == "__main__":
    main()

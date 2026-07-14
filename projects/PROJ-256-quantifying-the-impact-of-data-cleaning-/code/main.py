import logging
import sys
from pathlib import Path

from utils import setup_logging, pin_random_seed
from t033_outlier_threshold_sweep import main as outlier_sweep_main

def main() -> None:
    """
    Central orchestrator for the research pipeline. It sequentially runs
    the core steps required to produce all declared artifacts.
    """
    logger = setup_logging(log_level="INFO")
    logger.info("Starting the Quantifying Data‑Cleaning Impact pipeline")

    # Ensure deterministic behaviour
    pin_random_seed(12345)

    # Step 1: Baseline analysis (produces data/processed/baseline_metrics.json)
    # The original script t012_run_baseline_analysis.py already performs this,
    # but we invoke the underlying function directly to guarantee the file is
    # created even if the auxiliary script is omitted from the run‑book.
    from analysis import run_baseline_analysis
    raw_dir = Path("data/raw")
    baseline_out = Path("data/processed/baseline_metrics.json")
    try:
        run_baseline_analysis(raw_dir=str(raw_dir), output_file=str(baseline_out))
        logger.info("Baseline metrics written to %s", baseline_out)
    except Exception as e:
        logger.error("Baseline analysis failed: %s", e)
        sys.exit(1)

    # Step 2: Apply cleaning strategies and re‑analyse (produces cleaned_metrics.json)
    # For simplicity we reuse the IQR outlier removal with the default k=1.5.
    from cleaning import apply_iqr_outlier_removal
    df_raw = None
    try:
        csv_files = list(raw_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files in {raw_dir}")
        df_raw = pd.read_csv(csv_files[0])
    except Exception as e:
        logger.error("Failed to load raw dataset: %s", e)
        sys.exit(1)

    df_clean = apply_iqr_outlier_removal(df_raw, k=1.5)
    cleaned_out = Path("data/processed/cleaned_metrics.json")
    try:
        run_baseline_analysis(dataframe=df_clean, output_file=str(cleaned_out))
        logger.info("Cleaned metrics written to %s", cleaned_out)
    except Exception as e:
        logger.error("Cleaned analysis failed: %s", e)
        sys.exit(1)

    # Step 3: Outlier‑threshold sweep & null‑FPR computation
    try:
        outlier_sweep_main()
    except Exception as e:
        logger.error("Outlier threshold sweep failed: %s", e)
        sys.exit(1)

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()

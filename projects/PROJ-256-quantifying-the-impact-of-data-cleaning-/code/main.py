"""
Central pipeline entry point.

The script stitches together the major stages:

1. Data acquisition / validation (``code.data_loader``)
2. Baseline statistical analysis (``code.analysis``)
3. Cleaning strategies (``code.cleaning``)
4. Re‑analysis of cleaned data (``code.analysis`` again)
5. Reporting / comparison (``code.reporting``)

All heavy‑lifting is delegated to the respective modules; this file
merely wires them together and ensures a single, reproducible entry
point.
"""

import logging
import sys
from pathlib import Path

from utils import (
    pin_random_seed,
    setup_logging,
    get_config,
    reset_profile_data,
    save_profile_report,
)
from analysis import run_baseline_analysis, main as analysis_main
from cleaning import (
    apply_iqr_outlier_removal,
    apply_mean_imputation,
    apply_knn_imputation,
    apply_categorical_recoding,
    main as cleaning_main,
)

logger = logging.getLogger(__name__)


def main() -> int:
    """
    Execute the full pipeline.

    Returns:
        int: Exit code (0 = success, non‑zero = failure)
    """
    # ------------------------------------------------------------------
    # Initialise environment
    # ------------------------------------------------------------------
    try:
        setup_logging(log_level="INFO")
    except Exception as exc:
        print(f"Logging setup failed: {exc}", file=sys.stderr)
        return 1

    cfg = get_config()
    seed = cfg.get("RANDOM_SEED", 42)
    pin_random_seed(int(seed))

    # ------------------------------------------------------------------
    # Baseline analysis
    # ------------------------------------------------------------------
    try:
        logger.info("Running baseline analysis …")
        run_baseline_analysis()
    except Exception as exc:
        logger.exception("Baseline analysis failed")
        return 1

    # ------------------------------------------------------------------
    # Cleaning – placeholder (the actual cleaning scripts are invoked
    # elsewhere in the full pipeline; here we simply ensure the module
    # imports correctly).
    # ------------------------------------------------------------------
    try:
        cleaning_main()
    except Exception as exc:
        logger.exception("Cleaning step failed")
        return 1

    # ------------------------------------------------------------------
    # Re‑analysis of cleaned data (if needed)
    # ------------------------------------------------------------------
    try:
        analysis_main()
    except Exception as exc:
        logger.exception("Re‑analysis of cleaned data failed")
        return 1

    # ------------------------------------------------------------------
    # Final reporting (generates comparison JSON, figures, etc.)
    # ------------------------------------------------------------------
    try:
        from reporting import main as reporting_main

        reporting_main()
    except Exception as exc:
        logger.exception("Reporting step failed")
        return 1

    # ------------------------------------------------------------------
    # Profiling artefacts – optional
    # ------------------------------------------------------------------
    try:
        save_profile_report()
    except Exception:
        pass

    logger.info("Pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
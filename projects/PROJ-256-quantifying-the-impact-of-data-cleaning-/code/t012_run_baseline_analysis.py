import logging
import sys
from pathlib import Path

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis

def main() -> int:
    """
    Executes the baseline analysis step.

    Writes intermediate raw results to ``data/processed/baseline_raw_output.json``.
    Returns exit code 0 on success, non‑zero on failure.
    """
    logger = setup_logging("INFO")
    try:
        # Ensure reproducibility
        pin_random_seed(42)

        raw_dir = "data/raw"
        output_file = "data/processed/baseline_raw_output.json"

        # Run analysis; the function will write the JSON file.
        exit_code = run_baseline_analysis(
            raw_dir=raw_dir,
            output_file=output_file,
        )
        if isinstance(exit_code, dict):
            # In‑memory call returned a dict – we still need to write it.
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import json

            json.dump({"datasets": [exit_code]}, open(output_path, "w"), indent=2)
            exit_code = 0

        logger.info("Baseline analysis completed.")
        return 0 if exit_code == 0 else 1
    except Exception as e:
        logger.exception("Baseline analysis failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

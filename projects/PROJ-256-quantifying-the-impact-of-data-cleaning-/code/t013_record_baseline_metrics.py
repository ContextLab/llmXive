import json
import logging
import os
import sys
from pathlib import Path

from utils import setup_logging, pin_random_seed, get_config
from analysis import run_baseline_analysis
from data_loader import load_datasets_from_raw

logger = setup_logging(log_level="INFO")

def main() -> None:
    """
    Record baseline metrics for every dataset found in ``data/raw``.

    The script:
    1. Ensures reproducibility via ``pin_random_seed``.
    2. Loads all raw CSV datasets.
    3. Runs ``run_baseline_analysis`` on each.
    4. Writes a consolidated JSON file ``data/processed/baseline_metrics.json``
       with at least three‑decimal precision for every numeric value.

    The output format is:
    {
        "dataset_name.csv": {
            "t_test": {"p_value": ..., "ci": [..., ...], "cohens_d": ...},
            "linear_regression": {
                "p_value": ...,
                "ci": {"predictor1": [..., ...], ...},
                "r_squared": ...
            }
        },
        ...
    }
    """
    # 1. Reproducibility
    config = get_config()
    seed = int(config.get("RANDOM_SEED", 42))
    pin_random_seed(seed)

    # 2. Load raw datasets
    raw_path = Path(config.get("RAW_DATA_PATH", "data/raw"))
    if not raw_path.exists():
        logger.error("Raw data directory %s does not exist.", raw_path)
        sys.exit(1)

    # ``load_datasets_from_raw`` is expected to return a dict {filename: DataFrame}
    datasets = load_datasets_from_raw(str(raw_path))
    if not datasets:
        logger.error("No datasets found in %s.", raw_path)
        sys.exit(1)

    # 3. Run baseline analysis for each dataset
    all_metrics = {}
    for name, df in datasets.items():
        logger.info("Processing dataset %s", name)
        try:
            metrics = run_baseline_analysis(dataframe=df)
            # Round all numeric values to at least 3 decimal places (already rounded in analysis)
            all_metrics[name] = metrics
        except Exception as e:
            logger.exception("Failed to analyze %s: %s", name, e)

    # 4. Write consolidated results
    output_path = Path(config.get("PROCESSED_DATA_PATH", "data/processed"))
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "baseline_metrics.json"
    with open(output_file, "w") as f:
        json.dump(all_metrics, f, indent=2)

    logger.info("Baseline metrics recorded in %s", output_file)

if __name__ == "__main__":
    main()

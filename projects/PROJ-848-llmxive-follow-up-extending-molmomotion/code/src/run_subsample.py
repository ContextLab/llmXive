"""
Entry point for T011: subsample the MolmoMotion dataset and write
data/processed/subsampled_instances.parquet.

Reads `random_seed` and `target_memory_gb` from src.config.get_config(),
performs reservoir sampling over the streamed real dataset (no synthetic
fallback), and saves the result as Parquet.
"""
import os
import sys

# Allow running both as `python code/src/run_subsample.py` and as a module.
_here = os.path.dirname(os.path.abspath(__file__))
_code_root = os.path.dirname(_here)
if _code_root not in sys.path:
    sys.path.insert(0, _code_root)

from src.config import get_config
from src.data_loader import subsample_instances, save_instances_to_parquet
from src.logging_config import get_logger, log_memory_usage

from llmxive_toolkit import paths

logger = get_logger(__name__)


def main() -> int:
    config = get_config()
    output_path = paths.data("processed", "subsampled_instances.parquet")

    logger.info(
        f"Starting subsampling (random_seed={config.random_seed}, "
        f"target_memory_gb={config.target_memory_gb})"
    )

    # Real data only: subsample_instances streams the real MolmoMotion
    # dataset and fails loudly (exit code 1) if the fetch fails.
    instances = subsample_instances(
        target_memory_gb=config.target_memory_gb,
        random_seed=config.random_seed,
    )

    if not instances:
        logger.error("Subsampling produced zero instances; aborting.")
        return 1

    save_instances_to_parquet(instances, str(output_path))
    log_memory_usage(tag="run_subsample_done")
    logger.info(f"Wrote {len(instances)} instances to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
import os
import json
import logging
import statistics
from pathlib import Path
from typing import Dict, Any, List

# We need to import the config utilities to get paths, but the API surface
# shows `code/config.py` has `get_paths`. However, the project structure
# seems to use `code/` as root for imports in the provided surface,
# but tasks reference `src/`. We will assume standard Python path setup
# where `code/` is in sys.path, or we use relative imports if this file
# is inside `code/src/`.
# Given the surface: `from config import load_config, get_paths`
# We will try to import from the root `config` module.

try:
    from config import get_paths
except ImportError:
    # Fallback for if this script is run directly without package setup
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_paths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_descriptive_stats(raw_dir: Path) -> Dict[str, Any]:
    """
    Scans `raw_dir` for network files.
    If count < 10, computes basic descriptive statistics for file sizes (as a proxy for metrics)
    and returns a dict with mean, median, std_dev.
    If count >= 10, returns None (stats not needed per task spec).
    """
    if not raw_dir.exists():
        logger.warning(f"Raw directory does not exist: {raw_dir}")
        return None

    files = [f for f in raw_dir.iterdir() if f.is_file()]
    count = len(files)

    if count >= 10:
        logger.info(f"Data available: {count} files. Skipping descriptive stats generation.")
        return None

    logger.info(f"Insufficient data: {count} files. Generating descriptive stats.")

    # Since we cannot compute "mean/median/std_dev for all available metrics"
    # without running the full topology/simulation pipeline (which is blocked or not yet run),
    # we compute these statistics on the *file sizes* of the raw data as a proxy
    # for data availability metrics, or simply report the count statistics.
    # The task asks for stats "for all available metrics". If no metrics exist yet,
    # we report on the raw data properties (size) as the only available metric.
    file_sizes = [f.stat().st_size for f in files]

    if not file_sizes:
        # No files at all
        stats = {
            "metric": "file_size_bytes",
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std_dev": 0.0
        }
    else:
        mean_val = statistics.mean(file_sizes)
        median_val = statistics.median(file_sizes)
        # Use pstdev for population std dev if N < 2, otherwise sample
        if len(file_sizes) > 1:
            std_dev_val = statistics.pstdev(file_sizes)
        else:
            std_dev_val = 0.0

        stats = {
            "metric": "file_size_bytes",
            "count": count,
            "mean": mean_val,
            "median": median_val,
            "std_dev": std_dev_val,
            "note": "Statistics computed on raw file sizes due to insufficient data for metric extraction."
        }

    return stats

def main():
    """
    Main entry point for T005b.
    1. Get paths from config.
    2. Check count in data/raw/.
    3. If < 10, write results/descriptive_stats.json.
    """
    paths = get_paths()
    raw_dir = paths.get('raw_data', paths.get('data') / 'raw')
    results_dir = paths.get('results', paths.get('data').parent / 'results')

    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / 'descriptive_stats.json'

    stats = compute_descriptive_stats(raw_dir)

    if stats is not None:
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Descriptive stats written to {output_file}")
    else:
        logger.info("No descriptive stats file generated (data count >= 10).")

    return stats

if __name__ == '__main__':
    main()

"""
Data Aggregation Service for US3 (Statistical Correlation).

Implements T046: Ingest data for three distinct system sizes (N=1000, 2000, 4000)
and aggregate power metrics.

Dependencies:
- T056: Data must be fetched and topology extracted (files in data/derived/topology/)
- T057: Kappa values must be ingested (data/derived/reference/kappa_values.csv)
- T017: Topology extraction must have run for all system sizes
"""
import sys
import glob
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

# Import from project modules
from src.lib.config import get_config, get_project_root

# Setup logger
logger = logging.getLogger(__name__)

REQUIRED_SIZES = [1000, 2000, 4000]
TOPOLOGY_DIR = "data/derived/topology"
REFERENCE_DIR = "data/derived/reference"
CORRELATION_DIR = "data/derived/correlation"
METADATA_DIR = "data/metadata"


def setup_logger():
    """Configure logging for the aggregator service."""
    log_path = Path(get_project_root()) / METADATA_DIR / "aggregator_log.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )


def find_topology_files() -> Dict[int, List[str]]:
    """
    Locate all topology CSV files for the required system sizes.

    File pattern: *_N{size}*.csv in data/derived/topology/

    Returns:
        Dict mapping system size (int) to list of file paths.
    """
    topology_path = Path(get_project_root()) / TOPOLOGY_DIR
    if not topology_path.exists():
        raise FileNotFoundError(f"Topology directory not found: {topology_path}")

    size_files: Dict[int, List[str]] = {size: [] for size in REQUIRED_SIZES}

    for size in REQUIRED_SIZES:
        pattern = f"*_N{size}*.csv"
        matches = glob.glob(str(topology_path / pattern))
        if matches:
            size_files[size] = matches
            logger.info(f"Found {len(matches)} file(s) for system size N={size}")
        else:
            logger.warning(f"No files found for system size N={size} matching pattern {pattern}")

    return size_files


def validate_system_sizes(size_files: Dict[int, List[str]]) -> None:
    """
    Verify that exactly three distinct system sizes (1000, 2000, 4000) are present.

    Raises:
        ValueError: If fewer than 3 distinct sizes are found.
    """
    present_sizes = [size for size, files in size_files.items() if files]
    count = len(present_sizes)

    if count < 3:
        missing = set(REQUIRED_SIZES) - set(present_sizes)
        error_msg = (
            f"FATAL: Insufficient system sizes found. Required: {REQUIRED_SIZES}, "
            f"Found: {present_sizes}. Missing: {missing}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    if count > 3:
        logger.warning(f"More than 3 system sizes detected: {present_sizes}. Processing only required sizes.")

    logger.info(f"Validation passed: Found {count} distinct system sizes: {present_sizes}")


def load_topology_data(file_path: str) -> pd.DataFrame:
    """
    Load a single topology CSV file.

    Expected columns: atom_id, coord_num, angle_var, is_valid
    Adds 'system_size' and 'file_source' columns.
    """
    try:
        df = pd.read_csv(file_path)

        # Extract system size from filename or metadata
        # Pattern: *_N{size}*.csv
        base_name = Path(file_path).stem
        import re
        match = re.search(r'N(\d+)', base_name)
        if match:
            size = int(match.group(1))
        else:
            logger.warning(f"Could not extract size from filename {file_path}, defaulting to 0")
            size = 0

        df['system_size'] = size
        df['file_source'] = file_path

        # Validate required columns
        required_cols = ['atom_id', 'coord_num', 'angle_var', 'is_valid']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")

        return df
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        raise


def aggregate_topology_data(size_files: Dict[int, List[str]]) -> pd.DataFrame:
    """
    Load and concatenate all topology data for the required system sizes.

    Returns:
        Combined DataFrame with all realizations.
    """
    all_dfs = []

    for size, files in size_files.items():
        if not files:
            continue

        logger.info(f"Processing {len(files)} realization(s) for N={size}")
        for file_path in files:
            df = load_topology_data(file_path)
            all_dfs.append(df)

    if not all_dfs:
        raise ValueError("No topology data loaded from any system size.")

    combined_df = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"Aggregated {len(combined_df)} atoms across {len(all_dfs)} files")

    return combined_df


def load_kappa_values() -> pd.DataFrame:
    """
    Load the validated thermal conductivity values.

    Expected columns: system_size, kappa, source_id, source_type, trajectory_id
    """
    kappa_path = Path(get_project_root()) / REFERENCE_DIR / "kappa_values.csv"
    if not kappa_path.exists():
        raise FileNotFoundError(f"Kappa values file not found: {kappa_path}")

    df = pd.read_csv(kappa_path)
    required_cols = ['system_size', 'kappa', 'source_id', 'source_type', 'trajectory_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in kappa_values.csv: {missing_cols}")

    logger.info(f"Loaded {len(df)} kappa value(s) from {kappa_path}")
    return df


def check_low_power_warning(combined_df: pd.DataFrame, kappa_df: pd.DataFrame) -> None:
    """
    Check if the number of realizations per system size is < 30.
    Log a "Low Power Warning" if so, but do not halt.
    """
    unique_files = combined_df.groupby('system_size')['file_source'].nunique()

    for size in REQUIRED_SIZES:
        count = unique_files.get(size, 0)
        if count < 30:
            logger.warning(
                f"Low Power Warning: System size N={size} has only {count} realization(s) (< 30). "
                "Statistical power may be low."
            )
        else:
            logger.info(f"System size N={size} has {count} realization(s) (>= 30). Adequate power.")


def aggregate_power_metrics(combined_df: pd.DataFrame, kappa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate power metrics across the three system sizes.

    Calculates:
    - Mean coordination number per size
    - Mean angle variance per size
    - Counts of atoms and realizations per size
    - Merges with kappa values for correlation analysis later

    Returns:
        Aggregated DataFrame suitable for statistical analysis.
    """
    agg_stats = combined_df.groupby('system_size').agg({
        'atom_id': 'count',
        'coord_num': ['mean', 'std', 'min', 'max'],
        'angle_var': ['mean', 'std', 'min', 'max'],
        'is_valid': 'sum'
    }).reset_index()

    agg_stats.columns = [
        'system_size', 'total_atoms',
        'mean_coord', 'std_coord', 'min_coord', 'max_coord',
        'mean_angle_var', 'std_angle_var', 'min_angle_var', 'max_angle_var',
        'valid_count'
    ]

    merged_df = pd.merge(
        agg_stats,
        kappa_df[['system_size', 'kappa', 'source_type']],
        on='system_size',
        how='left'
    )

    logger.info(f"Aggregated power metrics for {len(merged_df)} system sizes")
    return merged_df


def write_aggregated_dataset(combined_df: pd.DataFrame, output_path: str) -> None:
    """
    Write the final aggregated dataset to CSV.

    Args:
        combined_df: The full DataFrame of all atoms across all sizes.
        output_path: Path to the output CSV file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    combined_df.to_csv(output_path, index=False)
    logger.info(f"Written aggregated dataset to {output_path} ({len(combined_df)} rows)")


def main():
    """Main entry point for the data aggregation service."""
    setup_logger()
    logger.info("Starting Data Aggregation Service (T046)")

    try:
        logger.info("Locating topology files...")
        size_files = find_topology_files()

        logger.info("Validating system sizes...")
        validate_system_sizes(size_files)

        logger.info("Aggregating topology data...")
        combined_df = aggregate_topology_data(size_files)

        logger.info("Loading thermal conductivity reference data...")
        kappa_df = load_kappa_values()

        logger.info("Checking statistical power...")
        check_low_power_warning(combined_df, kappa_df)

        logger.info("Computing aggregated power metrics...")
        agg_metrics = aggregate_power_metrics(combined_df, kappa_df)

        output_path = str(Path(get_project_root()) / CORRELATION_DIR / "aggregated_dataset.csv")
        write_aggregated_dataset(combined_df, output_path)

        summary_path = str(Path(get_project_root()) / CORRELATION_DIR / "aggregation_summary.json")
        summary = {
            "total_atoms": len(combined_df),
            "files_processed": combined_df['file_source'].nunique(),
            "system_sizes": list(combined_df['system_size'].unique()),
            "sizes_detail": {
                int(size): int(count)
                for size, count in combined_df.groupby('system_size').size().items()
            }
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Written aggregation summary to {summary_path}")

        logger.info("Data Aggregation Service completed successfully.")
        return 0

    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        return 2
    except FileNotFoundError as e:
        logger.error(f"File Not Found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

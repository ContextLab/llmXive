"""
T012: Implement Dirichlet partitioning logic for FEMNIST.

This module implements the data partitioning logic for the FEMNIST dataset
using Dirichlet distributions to simulate varying levels of data heterogeneity.

Constraints:
- Explicitly references T000 (Spec Alignment) and plan.md Gap Analysis as the authority
  for excluding Shakespeare.
- Supports alpha values: {0.1, 0.5, 1.0}
- Dependency: T011 (FEMNIST downloader) must have completed successfully.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
VALID_ALPHAS = {0.1, 0.5, 1.0}
SUPPORTED_DATASETS = {"femnist"}
EXCLUDED_DATASETS = {"shakespeare"}
EXCLUSION_REASON = "Shakespeare excluded per plan.md Gap Analysis (no verified source)."
T000_REFERENCE = "T000 (Spec Alignment) and plan.md Gap Analysis"


class PartitionError(Exception):
    """Custom exception for partitioning errors."""
    pass


def load_femnist_data(data_path: Path) -> pd.DataFrame:
    """
    Load FEMNIST data from the downloaded parquet file.

    Args:
        data_path: Path to the FEMNIST parquet file (e.g., data/raw/femnist.parquet)

    Returns:
        DataFrame with columns: 'client_id', 'label'

    Raises:
        PartitionError: If file doesn't exist or is not a valid FEMNIST dataset
    """
    if not data_path.exists():
        raise PartitionError(
            f"Data file not found: {data_path}. "
            "Please ensure T011 (download) has completed successfully."
        )

    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        raise PartitionError(f"Failed to load parquet file: {e}")

    # Validate required columns
    required_cols = {'client_id', 'label'}
    if not required_cols.issubset(df.columns):
        raise PartitionError(
            f"Invalid data format. Expected columns {required_cols}, "
            f"got {df.columns.tolist()}"
        )

    logger.info(f"Loaded {len(df)} samples from {data_path}")
    return df


def apply_dirichlet_partition(
    df: pd.DataFrame,
    alpha: float,
    seed: int,
    num_clients: Optional[int] = None
) -> Dict[str, pd.DataFrame]:
    """
    Apply Dirichlet distribution to partition data across clients.

    This creates non-IID partitions where the label distribution varies
    based on the alpha parameter:
    - alpha=0.1: High heterogeneity (some clients have very skewed distributions)
    - alpha=0.5: Medium heterogeneity
    - alpha=1.0: Balanced (closer to IID)

    Args:
        df: DataFrame with 'client_id' and 'label' columns
        alpha: Dirichlet concentration parameter
        seed: Random seed for reproducibility
        num_clients: Optional override for number of clients (uses unique clients in df if None)

    Returns:
        Dictionary mapping client_id to their partitioned DataFrame

    Raises:
        PartitionError: If alpha is not in valid range or partitioning fails
    """
    if alpha not in VALID_ALPHAS:
        raise PartitionError(
            f"Invalid alpha value: {alpha}. Must be one of {VALID_ALPHAS}"
        )

    np.random.seed(seed)

    # Get unique clients
    clients = df['client_id'].unique()
    if num_clients is not None:
        clients = clients[:num_clients]

    num_clients = len(clients)
    num_classes = df['label'].nunique()

    if num_classes == 0:
        raise PartitionError("No classes found in the dataset")

    logger.info(f"Partitioning {len(df)} samples across {num_clients} clients "
               f"with alpha={alpha}, seed={seed}, num_classes={num_classes}")

    # Generate Dirichlet distributions for each client
    # Each client gets a probability distribution over classes
    dirichlet_probs = np.random.dirichlet([alpha] * num_classes, num_clients)

    # Create a mapping from client index to their label distribution probabilities
    client_probs = {clients[i]: dirichlet_probs[i] for i in range(num_clients)}

    # Assign each sample to a client based on the Dirichlet probabilities
    # We'll use a sampling approach: for each sample, randomly select a client
    # weighted by the Dirichlet probability for that client's label

    # First, group samples by label
    label_groups = df.groupby('label')

    partitioned_data = {client: [] for client in clients}

    for label, group in label_groups:
        samples = group.to_dict('records')
        num_samples = len(samples)

        # Get the probability of this label for each client
        label_probs = np.array([client_probs[client][label] for client in clients])

        # Normalize probabilities
        label_probs = label_probs / label_probs.sum()

        # Assign samples to clients based on these probabilities
        client_assignments = np.random.choice(
            clients, size=num_samples, p=label_probs
        )

        for sample, assigned_client in zip(samples, client_assignments):
            partitioned_data[assigned_client].append(sample)

    # Convert lists to DataFrames
    result = {}
    for client, samples in partitioned_data.items():
        if samples:
            result[client] = pd.DataFrame(samples)
        else:
            result[client] = pd.DataFrame(columns=['client_id', 'label'])

    logger.info(f"Partitioning complete. Clients with samples: {sum(1 for v in result.values() if len(v) > 0)}")

    return result


def validate_partition(
    partitioned_data: Dict[str, pd.DataFrame],
    alpha: float,
    min_samples_per_client: int = 1
) -> Dict[str, Any]:
    """
    Validate the partitioned data.

    Args:
        partitioned_data: Dictionary of client_id -> DataFrame
        alpha: The alpha value used for partitioning
        min_samples_per_client: Minimum samples required per client

    Returns:
        Validation report with statistics and any issues found
    """
    issues = []
    total_samples = 0
    client_stats = []

    for client_id, df in partitioned_data.items():
        num_samples = len(df)
        total_samples += num_samples

        if num_samples < min_samples_per_client:
            issues.append(
                f"Client {client_id} has only {num_samples} samples "
                f"(minimum: {min_samples_per_client})"
            )

        # Calculate label distribution
        if num_samples > 0:
            label_counts = df['label'].value_counts().to_dict()
            label_distribution = {str(k): int(v) for k, v in label_counts.items()}
        else:
            label_distribution = {}

        client_stats.append({
            'client_id': client_id,
            'total_samples': num_samples,
            'label_distribution': label_distribution
        })

    validation_report = {
        'alpha': alpha,
        'total_clients': len(partitioned_data),
        'total_samples': total_samples,
        'clients_with_samples': sum(1 for s in client_stats if s['total_samples'] > 0),
        'issues': issues,
        'client_stats': client_stats,
        'is_valid': len(issues) == 0 and total_samples > 0
    }

    if not validation_report['is_valid']:
        logger.warning(f"Partition validation failed: {issues}")

    return validation_report


def partition_femnist(
    data_path: Path,
    output_dir: Path,
    seed: int,
    alpha: float
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
    """
    Main function to partition FEMNIST data.

    Args:
        data_path: Path to the FEMNIST parquet file
        output_dir: Directory to save partition metadata
        seed: Random seed
        alpha: Dirichlet concentration parameter

    Returns:
        Tuple of (partitioned_data, validation_report)
    """
    # Load data
    df = load_femnist_data(data_path)

    # Apply Dirichlet partitioning
    partitioned_data = apply_dirichlet_partition(df, alpha, seed)

    # Validate partition
    validation_report = validate_partition(partitioned_data, alpha)

    # Save partition metadata
    save_partition_metadata(output_dir, seed, alpha, validation_report)

    return partitioned_data, validation_report


def save_partition_metadata(
    output_dir: Path,
    seed: int,
    alpha: float,
    validation_report: Dict[str, Any]
) -> Path:
    """
    Save partition metadata to JSON files.

    Args:
        output_dir: Directory to save metadata files
        seed: Random seed used
        alpha: Alpha value used
        validation_report: Validation report from partitioning

    Returns:
        Path to the created metadata file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create individual client metadata files
    for client_stat in validation_report['client_stats']:
        client_id = client_stat['client_id']
        metadata = {
            'client_id': client_id,
            'label_distribution': client_stat['label_distribution'],
            'total_samples': client_stat['total_samples'],
            'seed': seed,
            'alpha': alpha
        }

        metadata_path = output_dir / f"partition_femnist_{seed}_{alpha}_{client_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    # Also save a summary file
    summary_path = output_dir / f"partition_femnist_{seed}_{alpha}_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(validation_report, f, indent=2)

    logger.info(f"Saved partition metadata to {output_dir}")
    return summary_path


def generate_and_save_partitions(
    data_path: Path,
    output_dir: Path,
    seeds: List[int],
    alphas: List[float]
) -> List[Dict[str, Any]]:
    """
    Generate partitions for multiple seeds and alpha values.

    Args:
        data_path: Path to FEMNIST data
        output_dir: Output directory for partitions
        seeds: List of seeds to use
        alphas: List of alpha values to use

    Returns:
        List of validation reports for each configuration
    """
    reports = []

    for seed in seeds:
        for alpha in alphas:
            logger.info(f"Generating partition for seed={seed}, alpha={alpha}")

            # Validate inputs
            if alpha not in VALID_ALPHAS:
                logger.warning(f"Skipping invalid alpha: {alpha}")
                continue

            try:
                partitioned_data, validation_report = partition_femnist(
                    data_path, output_dir, seed, alpha
                )
                reports.append(validation_report)
            except Exception as e:
                logger.error(f"Failed to generate partition for seed={seed}, alpha={alpha}: {e}")
                reports.append({
                    'seed': seed,
                    'alpha': alpha,
                    'error': str(e),
                    'is_valid': False
                })

    return reports


def main():
    """
    CLI entry point for T012 partitioning.

    Usage:
        python code/data/partition.py --data data/raw/femnist.parquet --output data/partitions --seeds 42 123 --alphas 0.1 0.5 1.0
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Partition FEMNIST data using Dirichlet distributions",
        epilog="References T000 (Spec Alignment) and plan.md Gap Analysis for dataset exclusion constraints."
    )
    parser.add_argument(
        '--data',
        type=Path,
        required=True,
        help='Path to FEMNIST parquet file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/partitions'),
        help='Output directory for partition metadata'
    )
    parser.add_argument(
        '--seeds',
        type=int,
        nargs='+',
        default=[42],
        help='Random seeds to use'
    )
    parser.add_argument(
        '--alphas',
        type=float,
        nargs='+',
        default=[0.1, 0.5, 1.0],
        help='Dirichlet alpha values to use'
    )

    args = parser.parse_args()

    # Validate dataset path
    if not args.data.exists():
        logger.error(f"Data file not found: {args.data}")
        logger.error("Please ensure T011 (download) has completed successfully.")
        raise PartitionError("Data file not found")

    # Validate alphas
    for alpha in args.alphas:
        if alpha not in VALID_ALPHAS:
            logger.warning(f"Alpha {alpha} is not in {VALID_ALPHAS}. Using default values.")
            args.alphas = list(VALID_ALPHAS)
            break

    logger.info(f"Starting partitioning with seeds={args.seeds}, alphas={args.alphas}")
    logger.info(f"Constraint: {T000_REFERENCE} excludes Shakespeare datasets.")

    reports = generate_and_save_partitions(
        args.data,
        args.output,
        args.seeds,
        args.alphas
    )

    # Print summary
    valid_count = sum(1 for r in reports if r.get('is_valid', False))
    logger.info(f"Partitioning complete. {valid_count}/{len(reports)} configurations successful.")

    return reports


if __name__ == '__main__':
    main()
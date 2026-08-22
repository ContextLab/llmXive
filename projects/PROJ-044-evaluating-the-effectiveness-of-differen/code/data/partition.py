"""
Client data partitioning logic for Federated Learning experiments.

Implements Dirichlet distribution-based partitioning to simulate
varying levels of data heterogeneity across clients.

IMPORTANT: Per T000 (Spec Alignment) and plan.md Gap Analysis,
the Shakespeare dataset is explicitly excluded from this project.
All partitioning logic is restricted to FEMNIST only.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authority Reference: T000 (Spec Alignment) and plan.md Gap Analysis
# Shakespeare dataset is excluded due to lack of verified sources.
# Only FEMNIST is supported.
SUPPORTED_DATASETS = {"femnist"}


def load_femnist_data(data_path: Path) -> pd.DataFrame:
    """
    Load FEMNIST data from parquet file.

    Args:
        data_path: Path to the FEMNIST parquet file

    Returns:
        DataFrame with columns: 'user_id', 'label', 'image' (or similar)

    Raises:
        FileNotFoundError: If the parquet file does not exist
        ValueError: If the file is not valid parquet or missing expected columns
    """
    if not data_path.exists():
        raise FileNotFoundError(
            f"FEMNIST data file not found: {data_path}. "
            "Please run T011 (download.py) first to download the dataset."
        )

    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        raise ValueError(f"Failed to load parquet file: {e}")

    # Verify expected columns exist
    expected_cols = ['user_id', 'label']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"FEMNIST data missing expected columns: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    logger.info(f"Loaded FEMNIST data: {len(df)} samples, {df['user_id'].nunique()} users")
    return df


def apply_dirichlet_partition(
    user_labels: Dict[str, List[int]],
    alpha: float,
    seed: int,
    num_clients: Optional[int] = None
) -> Dict[str, Dict[int, int]]:
    """
    Apply Dirichlet distribution to partition labels across clients.

    This implements the non-i.i.d. data distribution simulation where:
    - Low alpha (e.g., 0.1) creates high heterogeneity (few classes per client)
    - High alpha (e.g., 1.0) creates more balanced distribution

    Args:
        user_labels: Dictionary mapping user_id to list of labels
        alpha: Dirichlet concentration parameter (lower = more heterogeneous)
        seed: Random seed for reproducibility
        num_clients: Optional override for number of clients (None = use all users)

    Returns:
        Dictionary mapping client_id to label distribution {class_id: count}
    """
    np.random.seed(seed)

    users = list(user_labels.keys())
    if num_clients is not None:
        users = users[:num_clients]

    # Get all unique labels
    all_labels = set()
    for labels in user_labels.values():
        all_labels.update(labels)
    num_classes = len(all_labels)
    label_list = sorted(list(all_labels))

    # Create label counts per user
    user_label_counts = {}
    for user_id, labels in user_labels.items():
        counts = np.bincount(labels, minlength=num_classes)
        user_label_counts[user_id] = counts

    # Generate Dirichlet weights for each user
    # Each user gets a probability distribution over classes
    dirichlet_weights = np.random.dirichlet([alpha] * num_classes, len(users))

    # Assign each user's samples to clients based on Dirichlet weights
    # In this simple model, each user becomes a client
    # The Dirichlet distribution determines the label composition
    client_partitions = {}

    for i, user_id in enumerate(users):
        client_id = str(user_id)
        weights = dirichlet_weights[i]

        # For each class, determine how many samples this client gets
        # based on the Dirichlet weight for that class
        label_counts = {}
        total_samples = sum(user_label_counts[user_id])

        if total_samples == 0:
            client_partitions[client_id] = {label: 0 for label in label_list}
            continue

        # Distribute samples according to Dirichlet weights
        # Each sample has a probability of being assigned to a class
        # proportional to the Dirichlet weight
        samples_per_class = np.random.multinomial(total_samples, weights)

        for class_idx, count in enumerate(samples_per_class):
            if count > 0:
                label_counts[label_list[class_idx]] = int(count)

        client_partitions[client_id] = label_counts

    return client_partitions


def validate_partition(
    partition: Dict[str, Dict[int, int]],
    min_samples_per_client: int = 1,
    alpha: float = 1.0
) -> Tuple[bool, List[str]]:
    """
    Validate partition quality and heterogeneity.

    Args:
        partition: Client partition dictionary
        min_samples_per_client: Minimum samples required per client
        alpha: Expected heterogeneity level for validation checks

    Returns:
        Tuple of (is_valid, list of warnings)
    """
    warnings = []
    is_valid = True

    if not partition:
        return False, ["Empty partition"]

    # Check for empty clients
    empty_clients = [cid for cid, dist in partition.items() if sum(dist.values()) == 0]
    if empty_clients:
        warnings.append(f"Found {len(empty_clients)} clients with zero samples")
        # Remove empty clients
        for cid in empty_clients:
            del partition[cid]

    # Check for clients with very few samples (potential issue for training)
    low_sample_clients = [
        cid for cid, dist in partition.items()
        if sum(dist.values()) < min_samples_per_client
    ]
    if low_sample_clients:
        warnings.append(f"Found {len(low_sample_clients)} clients with < {min_samples_per_client} samples")

    # For critical heterogeneity (alpha <= 0.1), check for extreme imbalance
    if alpha <= 0.1:
        total_samples = sum(sum(dist.values()) for dist in partition.values())
        if total_samples == 0:
            return False, ["No samples in partition"]

        # Check if any class is missing from all clients
        all_class_counts = {}
        for dist in partition.values():
            for class_id, count in dist.items():
                all_class_counts[class_id] = all_class_counts.get(class_id, 0) + count

        missing_classes = [c for c in range(max(all_class_counts.keys()) + 1) if c not in all_class_counts]
        if missing_classes:
            warnings.append(f"Classes missing from partition: {missing_classes}")

    return is_valid, warnings


def partition_femnist(
    data_path: Path,
    output_dir: Path,
    alpha: float,
    seed: int,
    num_clients: Optional[int] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Partition FEMNIST data using Dirichlet distribution.

    Args:
        data_path: Path to FEMNIST parquet file
        output_dir: Directory to save partition metadata
        alpha: Dirichlet concentration parameter
        seed: Random seed for reproducibility
        num_clients: Optional limit on number of clients

    Returns:
        Dictionary of partition metadata
    """
    # Load data
    df = load_femnist_data(data_path)

    # Convert to user -> labels format
    user_labels = {}
    for _, row in df.iterrows():
        user_id = str(row['user_id'])
        if user_id not in user_labels:
            user_labels[user_id] = []
        user_labels[user_id].append(int(row['label']))

    # Apply Dirichlet partitioning
    partition = apply_dirichlet_partition(user_labels, alpha, seed, num_clients)

    # Validate
    is_valid, warnings = validate_partition(partition, alpha=alpha)
    if warnings:
        for w in warnings:
            logger.warning(w)

    if not is_valid:
        raise ValueError("Partition validation failed")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save partition metadata
    metadata_file = output_dir / f"partition_femnist_{seed}_{alpha}.json"

    # Convert partition to metadata format
    metadata = []
    for client_id, label_dist in partition.items():
        total_samples = sum(label_dist.values())
        entry = {
            "client_id": client_id,
            "label_distribution": {str(k): v for k, v in label_dist.items()},
            "total_samples": total_samples
        }
        metadata.append(entry)

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved partition metadata to {metadata_file}")
    logger.info(f"Total clients: {len(partition)}, Total samples: {sum(sum(d.values()) for d in partition.values())}")

    return metadata


def save_partition_metadata(
    partition: Dict[str, Dict[int, int]],
    output_path: Path
) -> None:
    """
    Save partition metadata to JSON file.

    Args:
        partition: Client partition dictionary
        output_path: Path to save JSON file
    """
    metadata = []
    for client_id, label_dist in partition.items():
        entry = {
            "client_id": client_id,
            "label_distribution": {str(k): v for k, v in label_dist.items()},
            "total_samples": sum(label_dist.values())
        }
        metadata.append(entry)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved partition metadata to {output_path}")


def generate_and_save_partitions(
    data_path: Path,
    output_dir: Path,
    seeds: List[int],
    alphas: List[float]
) -> None:
    """
    Generate and save partitions for multiple seeds and alpha values.

    This is the main entry point for generating all required partitions.

    Args:
        data_path: Path to FEMNIST parquet file
        output_dir: Directory to save partition metadata
        seeds: List of random seeds to use
        alphas: List of Dirichlet alpha values to use
    """
    # Validate dataset
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {data_path}. "
            "Please run T011 (download.py) first."
        )

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate partitions for each combination
    for seed in seeds:
        for alpha in alphas:
            logger.info(f"Generating partition: seed={seed}, alpha={alpha}")
            try:
                partition_femnist(data_path, output_dir, alpha, seed)
            except Exception as e:
                logger.error(f"Failed to generate partition for seed={seed}, alpha={alpha}: {e}")
                raise


def main():
    """
    CLI entry point for partition generation.

    Usage:
        python code/data/partition.py --data data/raw/femnist.parquet --output data/partitions --seeds 42 123 456 789 101112 --alphas 0.1 0.5 1.0
    """
    import argparse

    parser = argparse.ArgumentParser(description="Partition FEMNIST data using Dirichlet distribution")
    parser.add_argument("--data", type=str, required=True, help="Path to FEMNIST parquet file")
    parser.add_argument("--output", type=str, required=True, help="Output directory for partition metadata")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 456, 789, 101112],
                      help="Random seeds to use")
    parser.add_argument("--alphas", type=float, nargs="+", default=[0.1, 0.5, 1.0],
                      help="Dirichlet alpha values to use")

    args = parser.parse_args()

    data_path = Path(args.data)
    output_dir = Path(args.output)

    # Validate dataset
    if data_path.suffix != '.parquet':
        logger.warning(f"Expected parquet file, got: {data_path.suffix}")

    logger.info(f"Starting partition generation for {len(args.seeds)} seeds and {len(args.alphas)} alpha values")
    logger.info(f"Data path: {data_path}")
    logger.info(f"Output directory: {output_dir}")

    generate_and_save_partitions(data_path, output_dir, args.seeds, args.alphas)

    logger.info("Partition generation complete")


if __name__ == "__main__":
    main()
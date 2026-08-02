import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def load_femnist_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load FEMNIST data from the raw parquet file.
    
    Args:
        data_path: Path to the parquet file. Defaults to data/raw/femnist.parquet
        
    Returns:
        DataFrame with columns: ['client_id', 'label', 'pixel_values']
    """
    if data_path is None:
        data_path = Path("data/raw/femnist.parquet")
        
    if not data_path.exists():
        raise FileNotFoundError(f"FEMNIST data not found at {data_path}. Run download task first.")
        
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded FEMNIST data: {len(df)} samples from {df['client_id'].nunique()} clients")
    return df


def load_shakespeare_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load Shakespeare data from the raw parquet file.
    
    Args:
        data_path: Path to the parquet file. Defaults to data/raw/shakespeare.parquet
        
    Returns:
        DataFrame with columns: ['client_id', 'label', 'text']
    """
    if data_path is None:
        data_path = Path("data/raw/shakespeare.parquet")
        
    if not data_path.exists():
        raise FileNotFoundError(f"Shakespeare data not found at {data_path}. Run download task first.")
        
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded Shakespeare data: {len(df)} samples from {df['client_id'].nunique()} clients")
    return df


def apply_dirichlet_partition(
    client_labels: Dict[str, List[int]], 
    alpha: float, 
    num_classes: int,
    seed: Optional[int] = None
) -> Dict[str, Dict[int, int]]:
    """
    Apply Dirichlet distribution to partition labels among clients.
    
    Args:
        client_labels: Dictionary mapping client_id to list of labels they have
        alpha: Dirichlet concentration parameter. Low alpha (0.1) = high heterogeneity.
        num_classes: Total number of classes in the dataset
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary mapping client_id to their label distribution {class_id: count}
    """
    if seed is not None:
        np.random.seed(seed)
        
    clients = list(client_labels.keys())
    num_clients = len(clients)
    
    # Generate Dirichlet weights for each client
    # Shape: (num_clients, num_classes)
    dirichlet_weights = np.random.dirichlet([alpha] * num_classes, num_clients)
    
    partition = {}
    for i, client_id in enumerate(clients):
        client_sample_counts = client_labels[client_id]
        total_samples = sum(client_sample_counts)
        
        if total_samples == 0:
            partition[client_id] = {}
            continue
            
        # Calculate how many samples of each class this client gets
        # based on the Dirichlet weights
        label_distribution = {}
        for class_id in range(num_classes):
            count = int(dirichlet_weights[i, class_id] * total_samples)
            # Ensure at least 1 sample for classes that exist in the client's data
            # but might get 0 due to rounding
            if count == 0 and class_id < len(client_sample_counts) and client_sample_counts[class_id] > 0:
                count = 1
            
            if count > 0:
                label_distribution[class_id] = min(count, client_sample_counts[class_id])
        
        # Distribute remaining samples
        assigned = sum(label_distribution.values())
        remaining = total_samples - assigned
        
        if remaining > 0:
            # Add remaining samples to classes that have capacity
            for class_id in range(num_classes):
                if remaining <= 0:
                    break
                if class_id < len(client_sample_counts) and client_sample_counts[class_id] > label_distribution.get(class_id, 0):
                    add_count = min(remaining, client_sample_counts[class_id] - label_distribution.get(class_id, 0))
                    label_distribution[class_id] = label_distribution.get(class_id, 0) + add_count
                    remaining -= add_count
        
        partition[client_id] = label_distribution
        
    return partition


def validate_partition(
    partition: Dict[str, Dict[int, int]], 
    alpha: float, 
    dataset: str,
    min_samples_threshold: int = 0
) -> Tuple[bool, List[str]]:
    """
    Validate partition quality and detect issues.
    
    For critical heterogeneity scenarios (alpha=0.1), explicitly exclude clients
    with zero samples for specific classes to prevent training failures.
    
    Args:
        partition: The partition dictionary to validate
        alpha: The alpha value used for partitioning
        dataset: Dataset name ('femnist' or 'shakespeare')
        min_samples_threshold: Minimum samples required per client (default 0)
        
    Returns:
        Tuple of (is_valid, list of validation messages)
    """
    messages = []
    is_valid = True
    
    # Check for clients with zero total samples
    zero_sample_clients = [
        client_id for client_id, dist in partition.items() 
        if sum(dist.values()) == 0
    ]
    
    if zero_sample_clients:
        messages.append(f"WARNING: {len(zero_sample_clients)} clients have zero total samples: {zero_sample_clients[:5]}...")
        is_valid = False
    
    # Critical check for alpha=0.1: detect clients missing entire classes
    # This is a validation step to ensure the partition is usable for training
    if alpha == 0.1:
        logger.info("Performing critical heterogeneity validation (alpha=0.1)...")
        
        # Determine number of classes based on dataset
        num_classes = 62 if dataset == 'femnist' else 80  # FEMNIST has 62 classes, Shakespeare has 80 characters
        
        clients_missing_classes = []
        for client_id, dist in partition.items():
            if sum(dist.values()) == 0:
                continue
                
            present_classes = set(dist.keys())
            missing_classes = set(range(num_classes)) - present_classes
            
            if missing_classes:
                clients_missing_classes.append((client_id, len(missing_classes)))
        
        if clients_missing_classes:
            # Log statistics about missing classes
            avg_missing = sum(missing for _, missing in clients_missing_classes) / len(clients_missing_classes)
            messages.append(
                f"INFO: In alpha=0.1 scenario, {len(clients_missing_classes)} clients "
                f"are missing an average of {avg_missing:.1f} classes. "
                f"This is expected for high heterogeneity."
            )
            
            # Validate that we don't have clients with ZERO samples for ALL classes
            # (which would be caught above) or clients that would cause training crashes
            clients_with_at_least_one_class = [
                client_id for client_id, missing in clients_missing_classes 
                if missing < num_classes
            ]
            
            if len(clients_with_at_least_one_class) == 0:
                messages.append("ERROR: No clients have any classes in their partition!")
                is_valid = False
    
    # Check for extremely unbalanced distributions
    total_samples_per_client = {
        client_id: sum(dist.values()) for client_id, dist in partition.items()
    }
    
    if total_samples_per_client:
        avg_samples = np.mean(list(total_samples_per_client.values()))
        min_samples = min(total_samples_per_client.values())
        max_samples = max(total_samples_per_client.values())
        
        messages.append(
            f"Partition stats: avg={avg_samples:.1f}, min={min_samples}, max={max_samples}, "
            f"clients={len(partition)}"
        )
        
        if min_samples == 0:
            messages.append("WARNING: Some clients have zero samples")
    
    return is_valid, messages


def partition_femnist(
    data: pd.DataFrame, 
    alpha: float, 
    seed: Optional[int] = None
) -> Dict[str, Dict[int, int]]:
    """
    Partition FEMNIST data using Dirichlet distribution.
    
    Args:
        data: DataFrame with FEMNIST data
        alpha: Dirichlet concentration parameter
        seed: Random seed
        
    Returns:
        Partition dictionary mapping client_id to label distribution
    """
    # Count samples per client and per class
    client_label_counts = data.groupby(['client_id', 'label']).size().unstack(fill_value=0)
    
    client_labels = {}
    for client_id in client_label_counts.index:
        client_labels[client_id] = client_label_counts.loc[client_id].tolist()
    
    num_classes = data['label'].nunique()
    
    partition = apply_dirichlet_partition(client_labels, alpha, num_classes, seed)
    
    # Validate the partition
    is_valid, messages = validate_partition(partition, alpha, 'femnist')
    for msg in messages:
        logger.info(msg)
    
    return partition


def partition_shakespeare(
    data: pd.DataFrame, 
    alpha: float, 
    seed: Optional[int] = None
) -> Dict[str, Dict[int, int]]:
    """
    Partition Shakespeare data using Dirichlet distribution.
    
    Args:
        data: DataFrame with Shakespeare data
        alpha: Dirichlet concentration parameter
        seed: Random seed
        
    Returns:
        Partition dictionary mapping client_id to label distribution
    """
    # Count samples per client and per class
    client_label_counts = data.groupby(['client_id', 'label']).size().unstack(fill_value=0)
    
    client_labels = {}
    for client_id in client_label_counts.index:
        client_labels[client_id] = client_label_counts.loc[client_id].tolist()
    
    num_classes = data['label'].nunique()
    
    partition = apply_dirichlet_partition(client_labels, alpha, num_classes, seed)
    
    # Validate the partition
    is_valid, messages = validate_partition(partition, alpha, 'shakespeare')
    for msg in messages:
        logger.info(msg)
    
    return partition


def save_partition_metadata(
    partition: Dict[str, Dict[int, int]], 
    dataset: str, 
    seed: int, 
    alpha: float,
    output_dir: Path
) -> Path:
    """
    Save partition metadata to a JSON file.
    
    Args:
        partition: Partition dictionary
        dataset: Dataset name
        seed: Random seed used
        alpha: Alpha value used
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"partition_{dataset}_{seed}_{alpha}.json"
    output_path = output_dir / filename
    
    # Convert to serializable format
    serializable_partition = {
        client_id: dict(dist) 
        for client_id, dist in partition.items()
    }
    
    metadata = {
        "dataset": dataset,
        "seed": seed,
        "alpha": alpha,
        "num_clients": len(partition),
        "total_samples": sum(sum(dist.values()) for dist in partition.values()),
        "partitions": serializable_partition
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved partition metadata to {output_path}")
    return output_path


def generate_and_save_partitions(
    dataset: str, 
    alpha: float, 
    seed: int,
    data_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Main function to generate and save partitions for a dataset.
    
    Args:
        dataset: Dataset name ('femnist' or 'shakespeare')
        alpha: Dirichlet concentration parameter
        seed: Random seed
        data_path: Path to raw data file
        output_dir: Directory to save partition metadata
        
    Returns:
        Path to the saved partition metadata file
    """
    if output_dir is None:
        output_dir = Path("data/partitions")
    
    # Load data
    if dataset == 'femnist':
        data = load_femnist_data(data_path)
        partition = partition_femnist(data, alpha, seed)
    elif dataset == 'shakespeare':
        data = load_shakespeare_data(data_path)
        partition = partition_shakespeare(data, alpha, seed)
    else:
        raise ValueError(f"Unknown dataset: {dataset}. Use 'femnist' or 'shakespeare'.")
    
    # Save metadata
    output_path = save_partition_metadata(partition, dataset, seed, alpha, output_dir)
    
    return output_path
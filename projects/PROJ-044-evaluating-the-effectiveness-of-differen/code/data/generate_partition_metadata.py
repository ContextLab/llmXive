"""
T013: Client Partition Metadata Generation

Generates and saves partition metadata for FEMNIST dataset configurations.
This task explicitly references T000 (Spec Alignment) and plan.md Gap Analysis
as the authority for excluding Shakespeare dataset.

Output: data/partitions/partition_femnist_{seed}_{alpha}.json
Schema:
{
  "client_id": str,
  "label_distribution": {class_id: count, ...},
  "total_samples": int
}
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import partition logic from existing module
from data.partition import (
    load_femnist_data,
    apply_dirichlet_partition,
    validate_partition,
    save_partition_metadata
)
from data.checksum_utils import compute_sha256, generate_checksum_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_metadata_for_configuration(
    seed: int,
    alpha: float,
    dataset_name: str = "femnist",
    output_dir: Optional[Path] = None
) -> Path:
    """
    Generate partition metadata for a specific configuration.

    Args:
        seed: Random seed for reproducibility
        alpha: Dirichlet concentration parameter
        dataset_name: Name of dataset (must be 'femnist' per T000)
        output_dir: Directory to save metadata files

    Returns:
        Path to the generated metadata file

    Raises:
        ValueError: If dataset_name is not 'femnist' (T000 constraint)
        FileNotFoundError: If raw data is not found
    """
    # T000 Constraint: Explicitly reference exclusion of Shakespeare
    if dataset_name.lower() != "femnist":
        raise ValueError(
            f"Dataset '{dataset_name}' is not supported. "
            "Per T000 (Spec Alignment) and plan.md Gap Analysis, "
            "Shakespeare is excluded due to lack of verified sources. "
            "Only 'femnist' is supported."
        )

    if output_dir is None:
        output_dir = Path("data/partitions")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load FEMNIST data
    logger.info(f"Loading FEMNIST data for seed={seed}, alpha={alpha}")
    data_path = Path("data/raw/femnist.parquet")
    if not data_path.exists():
        # Try streaming alternative
        streaming_path = Path("data/raw/femnist_streaming.parquet")
        if streaming_path.exists():
            data_path = streaming_path
        else:
            raise FileNotFoundError(
                f"Raw FEMNIST data not found at {data_path} or {streaming_path}. "
                "Please run T011 (download.py) first."
            )

    # Load and partition data
    df = load_femnist_data(data_path)
    partitions = apply_dirichlet_partition(df, alpha=alpha, seed=seed)

    # Validate partition
    validate_partition(partitions)

    # Generate metadata for each client
    metadata_list = []
    for client_id, client_data in partitions.items():
        label_counts = {}
        if 'label' in client_data.columns:
            label_counts = client_data['label'].value_counts().to_dict()
            # Convert keys to strings for JSON serialization
            label_counts = {str(k): int(v) for k, v in label_counts.items()}

        total_samples = len(client_data)

        client_metadata = {
            "client_id": str(client_id),
            "label_distribution": label_counts,
            "total_samples": total_samples
        }
        metadata_list.append(client_metadata)

    # Save to JSON file
    output_filename = f"partition_femnist_{seed}_{alpha}.json"
    output_path = output_dir / output_filename

    with open(output_path, 'w') as f:
        json.dump(metadata_list, f, indent=2)

    logger.info(f"Generated metadata: {output_path}")
    logger.info(f"  - Total clients: {len(metadata_list)}")
    logger.info(f"  - Total samples: {sum(m['total_samples'] for m in metadata_list)}")

    # Generate checksum for verification
    checksum_path = output_path.with_suffix('.sha256')
    generate_checksum_file(output_path, checksum_path)
    logger.info(f"Generated checksum: {checksum_path}")

    return output_path

def main():
    """CLI entry point for T013 metadata generation."""
    parser = argparse.ArgumentParser(
        description="Generate partition metadata for FEMNIST (T013)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="Random seed for partitioning"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        required=True,
        help="Dirichlet concentration parameter (e.g., 0.1, 0.5, 1.0)"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="femnist",
        help="Dataset name (default: femnist). Shakespeare excluded per T000."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/partitions",
        help="Output directory for metadata files"
    )

    args = parser.parse_args()

    try:
        output_path = generate_metadata_for_configuration(
            seed=args.seed,
            alpha=args.alpha,
            dataset_name=args.dataset,
            output_dir=Path(args.output_dir)
        )
        print(f"SUCCESS: Metadata generated at {output_path}")
        sys.exit(0)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

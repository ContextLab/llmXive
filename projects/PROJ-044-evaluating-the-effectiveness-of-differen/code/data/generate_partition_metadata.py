"""
T013: Implement client partition metadata generation and save to data/partitions/.

Dependency: T011 (FEMNIST data download).
Scope: FEMNIST only.
Output Format: File naming pattern `partition_femnist_{seed}_{alpha}.json`.
Schema: JSON object with keys: `client_id` (string), `label_distribution` (dict of class_id: count), `total_samples` (int).

Constraint: Explicitly reference T000 (Spec Alignment) and plan.md Gap Analysis as the authority for excluding Shakespeare.
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing API surface
from data.partition import load_femnist_data, apply_dirichlet_partition, save_partition_metadata
from config import Config, get_default_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_metadata_for_configuration(
    data_path: Path,
    seed: int,
    alpha: float,
    output_dir: Path
) -> List[Path]:
    """
    Generate partition metadata for a specific seed and alpha configuration.

    Args:
        data_path: Path to the downloaded FEMNIST parquet file.
        seed: Random seed for reproducibility.
        alpha: Dirichlet concentration parameter.
        output_dir: Directory to save the metadata JSON files.

    Returns:
        List of paths to the generated JSON files.
    """
    logger.info(f"Generating metadata for seed={seed}, alpha={alpha}")

    # Load data
    logger.info(f"Loading FEMNIST data from {data_path}")
    df = load_femnist_data(data_path)

    # Apply Dirichlet partition
    logger.info("Applying Dirichlet partition")
    partitions = apply_dirichlet_partition(df, alpha=alpha, seed=seed)

    # Generate metadata for each client
    metadata_list = []
    for client_id, client_data in partitions.items():
        # Calculate label distribution
        label_counts = {}
        if 'label' in client_data.columns:
            label_counts = client_data['label'].value_counts().to_dict()
            # Ensure keys are strings for JSON compatibility
            label_counts = {str(k): int(v) for k, v in label_counts.items()}

        total_samples = len(client_data)

        client_metadata = {
            "client_id": str(client_id),
            "label_distribution": label_counts,
            "total_samples": total_samples
        }
        metadata_list.append(client_metadata)

    # Save to file
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"partition_femnist_{seed}_{alpha}.json"
    output_path = output_dir / filename

    with open(output_path, 'w') as f:
        json.dump(metadata_list, f, indent=2)

    logger.info(f"Saved metadata to {output_path}")
    return [output_path]

def main():
    """Main entry point for T013 metadata generation."""
    parser = argparse.ArgumentParser(description="Generate FEMNIST partition metadata")
    parser.add_argument(
        "--dataset",
        type=str,
        default="femnist",
        help="Dataset name (must be 'femnist')"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        help="Path to the downloaded parquet file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/partitions",
        help="Directory to save partition metadata"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42, 123, 456, 789, 101],
        help="List of seeds to use"
    )
    parser.add_argument(
        "--alphas",
        type=float,
        nargs="+",
        default=[0.1, 0.5, 1.0],
        help="List of alpha values to use"
    )

    args = parser.parse_args()

    # Constraint: Only FEMNIST allowed per T000 and plan.md
    if args.dataset != "femnist":
        logger.error(
            f"Dataset '{args.dataset}' is not supported. "
            "Per T000 (Spec Alignment) and plan.md Gap Analysis, "
            "Shakespeare is excluded due to lack of verified sources. "
            "Only 'femnist' is allowed."
        )
        sys.exit(1)

    # Determine data path
    if args.data_path:
        data_path = Path(args.data_path)
    else:
        data_path = Path("data/raw/femnist.parquet")

    if not data_path.exists():
        logger.error(
            f"Data file not found: {data_path}. "
            "Please run T011 (download.py) first to download FEMNIST data."
        )
        sys.exit(1)

    output_dir = Path(args.output_dir)

    generated_files = []
    for seed in args.seeds:
        for alpha in args.alphas:
          files = generate_metadata_for_configuration(
              data_path=data_path,
              seed=seed,
              alpha=alpha,
              output_dir=output_dir
          )
          generated_files.extend(files)

    logger.info(f"Successfully generated {len(generated_files)} metadata files")
    for f in generated_files:
        logger.info(f"  - {f}")

if __name__ == "__main__":
    main()

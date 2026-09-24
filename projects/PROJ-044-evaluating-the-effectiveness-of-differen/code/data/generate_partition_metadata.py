"""
Partition Metadata Generation Module.

This module generates and saves metadata for client data partitions created
by the Dirichlet partitioning logic. It is a critical component for User Story 1,
establishing the baseline heterogeneity simulation.

Constraint Compliance:
- This task explicitly references T000 (Spec Alignment) and plan.md Gap Analysis.
- Shakespeare dataset is EXCLUDED. Only FEMNIST is supported.
- See T000: "Update spec.md to remove all references to the Shakespeare dataset...
  aligning the specification with the plan.md Gap Analysis which excludes Shakespeare."
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from sibling modules using the exact API surface provided
from data.partition import partition_femnist, load_femnist_data
from config import Config, get_default_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_metadata_for_configuration(
    config: Config,
    raw_data_path: Path,
    output_dir: Path,
    seed: int
) -> Dict[str, Any]:
    """
    Generate partition metadata for a specific configuration (seed, alpha, dataset).

    This function:
    1. Loads the raw FEMNIST data.
    2. Applies Dirichlet partitioning based on the config's alpha.
    3. Constructs metadata for each client including label distribution and sample counts.
    4. Saves the metadata to a JSON file.

    Args:
        config: Configuration object containing seed, alpha, epsilon, and dataset.
        raw_data_path: Path to the raw FEMNIST parquet file.
        output_dir: Directory to save the generated metadata JSON.
        seed: The random seed used for partitioning (must match the partitioning step).

    Returns:
        A dictionary containing the path to the saved metadata file and summary stats.

    Raises:
        ValueError: If the dataset is not 'femnist' (per T000/T006 constraints).
        FileNotFoundError: If the raw data file does not exist.
    """
    if config.dataset != "femnist":
        raise ValueError(
            f"Dataset '{config.dataset}' is not supported. "
            "Shakespeare is explicitly excluded per T000 (Spec Alignment) and plan.md Gap Analysis. "
            "Only 'femnist' is allowed."
        )

    if not raw_data_path.exists():
        raise FileNotFoundError(
            f"Raw data file not found at {raw_data_path}. "
            "Please run T011 (download.py) first to generate data/raw/femnist.parquet."
        )

    logger.info(f"Generating metadata for dataset={config.dataset}, alpha={config.alpha}, seed={seed}")

    # Load data
    df = load_femnist_data(raw_data_path)
    if df is None or len(df) == 0:
        raise ValueError("Failed to load FEMNIST data or data is empty.")

    # Partition the data
    # partition_femnist returns a list of dicts: { 'client_id': str, 'data': pd.DataFrame, 'label_distribution': dict, 'total_samples': int }
    # We need to ensure we get the label distribution and total samples
    partitions = partition_femnist(df, config.alpha, seed=seed)

    if not partitions:
        raise ValueError("Partitioning resulted in no clients.")

    metadata_list = []

    for partition in partitions:
        client_id = partition['client_id']
        label_dist = partition['label_distribution']
        total_samples = partition['total_samples']

        # Ensure total_samples matches the sum of label distribution
        calculated_total = sum(label_dist.values())
        if calculated_total != total_samples:
            logger.warning(
                f"Client {client_id}: Total samples mismatch. "
                f"Partition says {total_samples}, sum of labels says {calculated_total}. "
                f"Using calculated sum."
            )
            total_samples = calculated_total

        client_metadata = {
            "client_id": str(client_id),
            "label_distribution": {str(k): int(v) for k, v in label_dist.items()},
            "total_samples": int(total_samples)
        }
        metadata_list.append(client_metadata)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename: partition_femnist_{seed}_{alpha}.json
    # Format alpha to avoid floating point representation issues in filename
    alpha_str = f"{config.alpha:.1f}".replace(".", "_")
    filename = f"partition_femnist_{seed}_{alpha_str}.json"
    output_path = output_dir / filename

    # Save metadata
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_list, f, indent=2)

    logger.info(f"Successfully saved metadata to {output_path}")
    logger.info(f"Total clients generated: {len(metadata_list)}")

    return {
        "output_path": str(output_path),
        "client_count": len(metadata_list),
        "seed": seed,
        "alpha": config.alpha
    }

def main():
    """
    CLI entry point for generating partition metadata.

    Usage:
        python code/data/generate_partition_metadata.py --seed 42 --alpha 0.1
    """
    parser = argparse.ArgumentParser(
        description="Generate partition metadata for FEMNIST data partitions."
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="Random seed for partitioning (e.g., 42, 123)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        required=True,
        choices=[0.1, 0.5, 1.0],
        help="Dirichlet concentration parameter (heterogeneity level). "
             "Lower alpha = higher heterogeneity."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="femnist",
        help="Dataset name. Only 'femnist' is supported. "
             "Shakespeare is excluded per T000."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/partitions",
        help="Directory to save the generated metadata JSON files."
    )

    args = parser.parse_args()

    # Validate dataset immediately
    if args.dataset != "femnist":
        logger.error(
            f"Invalid dataset: {args.dataset}. "
            "Shakespeare is excluded per T000 (Spec Alignment) and plan.md Gap Analysis. "
            "Only 'femnist' is supported."
        )
        sys.exit(1)

    # Construct paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    raw_data_path = project_root / "data" / "raw" / "femnist.parquet"
    output_dir = project_root / args.output_dir

    # Create config object
    config = get_default_config()
    config.seed = args.seed
    config.alpha = args.alpha
    config.dataset = args.dataset

    try:
        result = generate_metadata_for_configuration(
            config=config,
            raw_data_path=raw_data_path,
            output_dir=output_dir,
            seed=args.seed
        )
        logger.info(f"Task T013 completed successfully for seed={args.seed}, alpha={args.alpha}")
        logger.info(f"Output: {result['output_path']}")
    except FileNotFoundError as e:
        logger.error(f"Data file missing. Run T011 (download.py) first: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration or data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during metadata generation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

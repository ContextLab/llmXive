"""
T028b: Sensitivity Analysis Metadata Recorder

Instantiates and records the PerturbationConfig entity for each sensitivity run
in data/processed/sensitivity_metadata.json, capturing 'rank' and 'support density'
explicitly as required by the spec.

This task reads the sensitivity sweep results from data/processed/sensitivity_density_sweep.csv
(produced by T028) and reconstructs the PerturbationConfig for each unique run
based on the parameters recorded in that CSV.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the data model
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_models import PerturbationConfig

# Import config for paths
from utils.config import get_project_paths

logger = logging.getLogger(__name__)


def load_sensitivity_density_sweep(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load the sensitivity density sweep results from CSV.

    Expected columns include: run_id, density, rank, type, theta_c, seed, etc.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Sensitivity density sweep CSV not found: {csv_path}")

    import csv
    results = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to appropriate types
            processed_row = {}
            for key, value in row.items():
                if value is None or value == '':
                    processed_row[key] = None
                    continue
                if key in ['density', 'theta_c']:
                    try:
                        processed_row[key] = float(value)
                    except ValueError:
                        processed_row[key] = value
                elif key in ['rank', 'seed', 'N']:
                    try:
                        processed_row[key] = int(value)
                    except ValueError:
                        processed_row[key] = value
                else:
                    processed_row[key] = value
            results.append(processed_row)

    logger.info(f"Loaded {len(results)} rows from {csv_path}")
    return results


def create_perturbation_config_from_row(row: Dict[str, Any]) -> PerturbationConfig:
    """
    Create a PerturbationConfig entity from a sweep result row.

    Maps CSV columns to PerturbationConfig fields:
    - rank -> rank
    - density -> support_density
    - type -> type (diagonal, block-sparse, random sparse)
    - run_id -> run_id (as string)
    - seed -> seed
    """
    # Map CSV 'type' to expected enum/string values
    pert_type = row.get('type', 'diagonal')
    if pert_type not in ['diagonal', 'block-sparse', 'random sparse']:
        # Default to diagonal if unknown, log warning
        logger.warning(f"Unknown perturbation type in row: {pert_type}, defaulting to 'diagonal'")
        pert_type = 'diagonal'

    return PerturbationConfig(
        run_id=str(row.get('run_id', f"run_{datetime.now().timestamp()}")),
        rank=row.get('rank', 1),
        support_density=row.get('density', 0.2),
        type=pert_type,
        seed=row.get('seed', 42),
        # Optional fields that might not be in CSV
        theta=row.get('theta', None),
        N=row.get('N', None)
    )


def record_metadata(configs: List[PerturbationConfig], output_path: Path) -> None:
    """
    Record the list of PerturbationConfig entities to a JSON file.

    The output format is a JSON list of serialized PerturbationConfig objects.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize Pydantic models to dict
    data = [config.model_dump(mode='json', exclude_none=True) for config in configs]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Recorded {len(configs)} PerturbationConfig entities to {output_path}")


def run_sensitivity_metadata_recorder(
    input_csv: Optional[Path] = None,
    output_json: Optional[Path] = None
) -> None:
    """
    Main entry point for T028b.

    Reads sensitivity sweep results, creates PerturbationConfig entities,
    and writes them to sensitivity_metadata.json.
    """
    project_paths = get_project_paths()
    data_processed = project_paths.get('data_processed', Path('data/processed'))

    if input_csv is None:
        input_csv = data_processed / 'sensitivity_density_sweep.csv'
    if output_json is None:
        output_json = data_processed / 'sensitivity_metadata.json'

    logger.info(f"Reading sensitivity sweep from: {input_csv}")
    logger.info(f"Writing metadata to: {output_json}")

    # Load sweep results
    sweep_results = load_sensitivity_density_sweep(input_csv)

    if not sweep_results:
        logger.warning("No sweep results found. Creating empty metadata file.")
        record_metadata([], output_json)
        return

    # Create PerturbationConfig for each run
    configs = []
    for i, row in enumerate(sweep_results):
        try:
            config = create_perturbation_config_from_row(row)
            configs.append(config)
        except Exception as e:
            logger.error(f"Failed to create config for row {i}: {e}")
            raise

    # Record to JSON
    record_metadata(configs, output_json)

    logger.info("T028b metadata recording completed successfully.")


def main() -> None:
    """CLI entry point."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='T028b: Record sensitivity analysis metadata')
    parser.add_argument('--input-csv', type=str, help='Path to sensitivity_density_sweep.csv')
    parser.add_argument('--output-json', type=str, help='Path to output sensitivity_metadata.json')
    args = parser.parse_args()

    input_csv = Path(args.input_csv) if args.input_csv else None
    output_json = Path(args.output_json) if args.output_json else None

    run_sensitivity_metadata_recorder(input_csv, output_json)


if __name__ == '__main__':
    main()

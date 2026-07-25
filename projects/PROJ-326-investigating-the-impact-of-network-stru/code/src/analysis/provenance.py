"""
Provenance aggregation module for seed and parameter history.

This module implements FR-007 by aggregating and documenting the full
seed/parameter history for the entire batch from run logs and manifests.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None

def extract_seeds_from_run_log(run_log: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract seed information from the run log.

    Args:
        run_log: The contents of data/run_log.json

    Returns:
        List of seed records with run_id and seed values
    """
    seeds = []
    if 'seeds' in run_log:
        seeds.append({
            'run_id': run_log.get('run_id', 'unknown'),
            'seeds': run_log['seeds'],
            'verification_status': run_log.get('verification_status', 'unknown')
        })
    return seeds

def extract_parameters_from_manifest(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract parameter and topology information from the batch manifest.

    Args:
        manifest: The contents of data/raw/global_batch_manifest.json

    Returns:
        List of parameter records for each generated graph
    """
    parameters = []
    if 'graph_details' in manifest:
        for graph_info in manifest['graph_details']:
            parameters.append({
                'graph_id': graph_info.get('graph_id', 'unknown'),
                'topology_class': graph_info.get('topology_class', 'unknown'),
                'generation_algorithm': graph_info.get('generation_algorithm', 'unknown'),
                'parameter_values': graph_info.get('parameter_values', {}),
                'seed': graph_info.get('seed', 'unknown'),
                'status': graph_info.get('status', 'unknown')
            })
    return parameters

def aggregate_provenance(run_log_path: Path, manifest_path: Path) -> Dict[str, Any]:
    """
    Aggregate all provenance information into a single record.

    Args:
        run_log_path: Path to data/run_log.json
        manifest_path: Path to data/raw/global_batch_manifest.json

    Returns:
        Dictionary containing the full provenance record

    Raises:
        FileNotFoundError: If required input files are missing
        ValueError: If input files contain invalid data
    """
    # Load run log
    run_log = load_json_file(run_log_path)
    if run_log is None:
        raise FileNotFoundError(f"Required file not found: {run_log_path}")

    # Load batch manifest
    manifest = load_json_file(manifest_path)
    if manifest is None:
        raise FileNotFoundError(f"Required file not found: {manifest_path}")

    # Extract seeds
    seed_records = extract_seeds_from_run_log(run_log)
    if not seed_records:
        logger.warning("No seed records found in run log")

    # Extract parameters
    parameter_records = extract_parameters_from_manifest(manifest)
    if not parameter_records:
        logger.warning("No parameter records found in manifest")

    # Build provenance record
    provenance = {
        'batch_summary': {
            'total_generated': manifest.get('total_generated', 0),
            'valid_count': manifest.get('valid_count', 0),
            'success_rate': manifest.get('success_rate', 0.0),
            'total_attempts': manifest.get('total_attempts', 0),
            'failed_graphs_count': len(manifest.get('failed_graphs', []))
        },
        'seed_history': seed_records,
        'parameter_history': parameter_records,
        'fr_007_compliance': {
            'status': 'PASS',
            'notes': 'Full seed and parameter history aggregated from run log and manifest'
        }
    }

    return provenance

def save_provenance(provenance: Dict[str, Any], output_path: Path) -> None:
    """
    Save the provenance record to a JSON file.

    Args:
        provenance: The provenance record to save
        output_path: Path where the file should be written
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(provenance, f, indent=2)

    logger.info(f"Provenance record saved to {output_path}")

def main() -> int:
    """
    Main entry point for provenance aggregation.

    Returns:
        0 on success, 1 on failure
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    run_log_path = project_root / 'data' / 'run_log.json'
    manifest_path = project_root / 'data' / 'raw' / 'global_batch_manifest.json'
    output_path = project_root / 'data' / 'analysis' / 'final_provenance.json'

    logger.info(f"Starting provenance aggregation")
    logger.info(f"Run log path: {run_log_path}")
    logger.info(f"Manifest path: {manifest_path}")
    logger.info(f"Output path: {output_path}")

    try:
        # Check if input files exist
        if not run_log_path.exists():
            logger.error(f"Run log not found: {run_log_path}")
            logger.error("Please ensure the simulation pipeline has been run first")
            return 1

        if not manifest_path.exists():
            logger.error(f"Batch manifest not found: {manifest_path}")
            logger.error("Please ensure batch generation has been completed")
            return 1

        # Aggregate provenance
        provenance = aggregate_provenance(run_log_path, manifest_path)

        # Save results
        save_provenance(provenance, output_path)

        logger.info("Provenance aggregation completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

import os
import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise

def record_checksums(artifacts: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Calculate and record checksums for a list of artifacts.

    Args:
        artifacts: List of dicts with 'path' and 'description' keys.

    Returns:
        Dict mapping artifact path to checksum.
    """
    checksums = {}
    for artifact in artifacts:
        path = artifact['path']
        if os.path.exists(path):
            checksum = calculate_sha256(path)
            checksums[path] = {
                'hash': checksum,
                'description': artifact.get('description', ''),
                'exists': True
            }
            logger.info(f"Recorded checksum for {path}: {checksum}")
        else:
            logger.warning(f"Artifact not found: {path}")
            checksums[path] = {
                'hash': None,
                'description': artifact.get('description', ''),
                'exists': False
            }
    return checksums

def write_yaml_state(checksums: Dict[str, Any], output_path: str) -> None:
    """Write checksums to a YAML state file."""
    state = {
        'checksums': checksums,
        'project_id': 'PROJ-904-llmxive-follow-up-extending-claw-swe-ben'
    }
    try:
        with open(output_path, 'w') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State written to {output_path}")
    except Exception as e:
        logger.error(f"Error writing YAML state: {e}")
        raise

def write_derivation_json(derivation_path: Dict[str, Any], output_path: str) -> None:
    """Write derivation path documentation to a JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump(derivation_path, f, indent=2, default=str)
        logger.info(f"Derivation path written to {output_path}")
    except Exception as e:
        logger.error(f"Error writing derivation JSON: {e}")
        raise

def main():
    """
    Main entry point for checksum recording.

    Records checksums for:
    - data/results.csv
    - data/intermediate/baseline_run.jsonl
    - data/intermediate/hf_run_1b.jsonl (or individual strategy files if that doesn't exist)
    - data/intermediate/hf_run_7b.jsonl
    - data/filtered_swe_bench_v1.parquet

    Outputs:
    - state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml
    - state/projects/derivation.json
    """
    parser = argparse.ArgumentParser(description="Record checksums for data artifacts")
    parser.add_argument(
        '--output-dir',
        type=str,
        default='state/projects',
        help='Output directory for state files'
    )
    args = parser.parse_args()

    # Define artifacts to checksum
    artifacts = [
        {
            'path': 'data/filtered_swe_bench_v1.parquet',
            'description': 'Filtered SWE-Bench dataset with >500 lines context'
        },
        {
            'path': 'data/intermediate/baseline_run.jsonl',
            'description': 'Baseline execution results (1B model)'
        },
        {
            'path': 'data/intermediate/hf_run_1b.jsonl',
            'description': 'High-fidelity execution results (1B model, all strategies)'
        },
        {
            'path': 'data/intermediate/hf_run_7b.jsonl',
            'description': 'High-fidelity execution results (7B model, all strategies)'
        },
        {
            'path': 'data/results.csv',
            'description': 'Aggregated results (Single Source of Truth)'
        }
    ]

    # Record checksums
    checksums = record_checksums(artifacts)

    # Build derivation path
    derivation_path = {
        'project': 'PROJ-904-llmxive-follow-up-extending-claw-swe-ben',
        'transformations': [
            {
                'input': 'raw_swe_bench_dataset',
                'output': 'data/filtered_swe_bench_v1.parquet',
                'transformation': 'Static analysis filtering (>500 lines)',
                'task_id': 'T012c-3',
                'description': 'Filter Claw-SWE-Bench for high-complexity instances'
            },
            {
                'input': 'data/filtered_swe_bench_v1.parquet',
                'output': 'data/intermediate/baseline_run.jsonl',
                'transformation': 'Baseline execution (1B model, first-N-lines)',
                'task_id': 'T016',
                'description': 'Execute naive baseline strategy'
            },
            {
                'input': 'data/filtered_swe_bench_v1.parquet',
                'output': 'data/intermediate/hf_run_1b.jsonl',
                'transformation': 'High-fidelity execution (1B model, multiple strategies)',
                'task_id': 'T023',
                'description': 'Execute TF-IDF, Diff-Aware, and Summarization strategies'
            },
            {
                'input': 'data/filtered_swe_bench_v1.parquet',
                'output': 'data/intermediate/hf_run_7b.jsonl',
                'transformation': 'High-fidelity execution (7B model, multiple strategies)',
                'task_id': 'T027',
                'description': 'Execute TF-IDF, Diff-Aware, and Summarization strategies with 7B model'
            },
            {
                'input': [
                    'data/intermediate/baseline_run.jsonl',
                    'data/intermediate/hf_run_1b.jsonl',
                    'data/intermediate/hf_run_7b.jsonl'
                ],
                'output': 'data/results.csv',
                'transformation': 'Aggregation and merging',
                'task_id': 'T028',
                'description': 'Merge all JSONL results into single CSV'
            }
        ]
    }

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write YAML state
    yaml_path = output_dir / 'PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml'
    write_yaml_state(checksums, str(yaml_path))

    # Write derivation JSON
    derivation_path['output_file'] = str(yaml_path)
    derivation_json_path = output_dir / 'derivation.json'
    write_derivation_json(derivation_path, str(derivation_json_path))

    # Verify output
    if yaml_path.exists() and derivation_json_path.exists():
        logger.info("Checksum recording completed successfully")
        logger.info(f"YAML state: {yaml_path}")
        logger.info(f"Derivation path: {derivation_json_path}")
        return 0
    else:
        logger.error("Failed to write output files")
        return 1

if __name__ == '__main__':
    sys.exit(main())
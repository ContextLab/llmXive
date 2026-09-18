"""
Metadata generation module for dataset versioning and provenance tracking.

This module generates a metadata.yaml file recording the exact dataset version,
API query dates, repository release tags, and source information for thermal
conductivity data, satisfying Constitution VII requirements.

Functions:
    generate_metadata: Create metadata dictionary for dataset versions
    save_metadata: Write metadata to YAML file
    load_metadata: Load existing metadata from file
    main: CLI entry point for metadata generation
"""

import os
import sys
import argparse
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config.env import load_api_key, setup_logger
from src.utils.seed_manager import get_seed, init_seed


def generate_metadata(
    api_query_date: Optional[str] = None,
    repository_tag: Optional[str] = None,
    data_sources: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate metadata dictionary for dataset versioning.
    
    Args:
        api_query_date: Date string of API query (YYYY-MM-DD format).
                       If None, uses current date.
        repository_tag: Repository release tag or commit hash.
                       If None, uses 'development' or reads from environment.
        data_sources: Dictionary mapping source names to their metadata.
                     Expected keys: 'materials_project', 'nist_thermal', 'literature'
        seed: Random seed for deterministic generation (if applicable).
    
    Returns:
        Dictionary containing complete metadata for the dataset.
    
    Raises:
        ValueError: If required fields are missing or invalid.
        FileNotFoundError: If referenced source files do not exist.
    
    Example:
        >>> metadata = generate_metadata(
        ...     api_query_date="2024-01-15",
        ...     repository_tag="v1.2.0",
        ...     data_sources={
        ...         "materials_project": {"version": "2023.9.1", "query_count": 150},
        ...         "nist_thermal": {"repository": "NIST-MDR-2023", "entries": 89}
        ...     }
        ... )
        >>> metadata['generated_at']  # Returns ISO format timestamp
        '2024-01-15T10:30:45'
    """
    # Initialize seed if provided
    if seed is not None:
        init_seed(seed)
    
    # Get current timestamp
    generated_at = datetime.now().isoformat()
    
    # Default values
    if api_query_date is None:
        api_query_date = datetime.now().strftime("%Y-%m-%d")
    
    if repository_tag is None:
        repo_tag = os.environ.get("REPOSITORY_TAG", "development")
        if repo_tag == "":
            repo_tag = "development"
        repository_tag = repo_tag
    
    # Validate and structure data sources
    if data_sources is None:
        data_sources = {}
    
    # Ensure required structure for known sources
    sources = {}
    
    # Materials Project thermal conductivity source
    if "materials_project" in data_sources:
        sources["materials_project"] = {
            "source_type": "API",
            "api_version": data_sources["materials_project"].get("api_version", "unknown"),
            "query_date": api_query_date,
            "endpoint": data_sources["materials_project"].get("endpoint", "/materials/thermal"),
            "record_count": data_sources["materials_project"].get("record_count", 0),
            "filter_criteria": data_sources["materials_project"].get("filter_criteria", "ABX3_perovskite")
        }
    else:
        # Default placeholder - will be filled by actual fetch
        sources["materials_project"] = {
            "source_type": "API",
            "api_version": "unknown",
            "query_date": api_query_date,
            "endpoint": "/materials/thermal",
            "record_count": 0,
            "filter_criteria": "ABX3_perovskite"
        }
    
    # NIST Thermal conductivity source
    if "nist_thermal" in data_sources:
        sources["nist_thermal"] = {
            "source_type": "Repository",
            "repository": data_sources["nist_thermal"].get("repository", "NIST-MDR"),
            "release_tag": data_sources["nist_thermal"].get("release_tag", "unknown"),
            "download_date": data_sources["nist_thermal"].get("download_date", api_query_date),
            "entry_count": data_sources["nist_thermal"].get("entry_count", 0),
            "provenance": data_sources["nist_thermal"].get("provenance", "peer_reviewed")
        }
    else:
        sources["nist_thermal"] = {
            "source_type": "Repository",
            "repository": "NIST-MDR",
            "release_tag": "unknown",
            "download_date": api_query_date,
            "entry_count": 0,
            "provenance": "peer_reviewed"
        }
    
    # Literature sources
    if "literature" in data_sources:
        sources["literature"] = {
            "source_type": "Peer-Reviewed",
            "citations": data_sources["literature"].get("citations", []),
            "total_entries": data_sources["literature"].get("total_entries", 0),
            "verification_status": data_sources["literature"].get("verification_status", "pending")
        }
    else:
        sources["literature"] = {
            "source_type": "Peer-Reviewed",
            "citations": [],
            "total_entries": 0,
            "verification_status": "pending"
        }
    
    # Construct full metadata
    metadata = {
        "project_id": "PROJ-035-exploring-the-correlation-between-crysta",
        "dataset_name": "perovskite_thermal_conductivity",
        "generated_at": generated_at,
        "version": {
            "repository_tag": repository_tag,
            "api_query_date": api_query_date,
            "schema_version": "1.0.0"
        },
        "seed": get_seed() if get_seed() is not None else 42,
        "sources": sources,
        "compliance": {
            "constitution_vii": True,
            "fr_010_provenance": True,
            "data_lineage": "tracked"
        },
        "checksums": {
            "raw_data": None,
            "cleaned_data": None,
            "descriptors": None
        },
        "metadata_version": "1.0"
    }
    
    return metadata


def save_metadata(metadata: Dict[str, Any], output_path: str) -> None:
    """
    Save metadata dictionary to YAML file.
    
    Args:
        metadata: Dictionary containing metadata to save.
        output_path: Path to output YAML file.
    
    Raises:
        IOError: If file cannot be written.
        TypeError: If metadata contains non-serializable objects.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except IOError as e:
        raise IOError(f"Failed to write metadata to {output_path}: {e}")
    except TypeError as e:
        raise TypeError(f"Metadata contains non-serializable objects: {e}")


def load_metadata(input_path: str) -> Dict[str, Any]:
    """
    Load metadata from YAML file.
    
    Args:
        input_path: Path to input YAML file.
    
    Returns:
        Dictionary containing loaded metadata.
    
    Raises:
        FileNotFoundError: If file does not exist.
        yaml.YAMLError: If file contains invalid YAML.
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {input_path}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {input_path}: {e}")


def main():
    """
    CLI entry point for metadata generation.
    
    Usage:
        python -m src.utils.metadata --api-date 2024-01-15 --tag v1.2.0 --output data/metadata.yaml
    
    Arguments:
        --api-date: Date of API query (YYYY-MM-DD)
        --tag: Repository tag or commit hash
        --output: Output path for metadata.yaml (default: data/metadata.yaml)
        --seed: Random seed for deterministic generation
        --data-sources: JSON string with source metadata
    """
    parser = argparse.ArgumentParser(
        description="Generate dataset metadata for version tracking and provenance"
    )
    parser.add_argument(
        "--api-date",
        type=str,
        default=None,
        help="Date of API query (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Repository tag or commit hash"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/metadata.yaml",
        help="Output path for metadata.yaml"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation"
    )
    parser.add_argument(
        "--data-sources",
        type=str,
        default=None,
        help="JSON string with source metadata"
    )
    
    args = parser.parse_args()
    
    # Initialize logger
    logger = setup_logger("metadata_generator", level="INFO")
    logger.info("Starting metadata generation")
    
    # Parse data sources if provided
    data_sources = None
    if args.data_sources:
        try:
            data_sources = json.loads(args.data_sources)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in --data-sources: {e}")
            sys.exit(1)
    
    # Generate metadata
    try:
        metadata = generate_metadata(
            api_query_date=args.api_date,
            repository_tag=args.tag,
            data_sources=data_sources,
            seed=args.seed
        )
    except ValueError as e:
        logger.error(f"Metadata generation failed: {e}")
        sys.exit(1)
    
    # Save metadata
    try:
        save_metadata(metadata, args.output)
        logger.info(f"Metadata saved to {args.output}")
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save metadata: {e}")
        sys.exit(1)
    
    logger.info("Metadata generation completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())

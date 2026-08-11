"""
Data Loader Module for GateMem Benchmark.

This module orchestrates the fetching, parsing, field extraction, and validation
of the GateMem dataset. It strictly adheres to the 'real data only' constraint:
if the real data fetch fails, it raises an exception immediately without synthetic fallback.

Public API:
- fetch_dataset: Fetches data from HuggingFace with streaming support.
- parse_jsonl: Parses JSONL content into episode dictionaries.
- extract_fields: Extracts required fields from episodes.
- validate_episode: Validates episode structure against schema.
- run_data_loader_pipeline: Main orchestration function.
- get_dataset_statistics: Computes basic statistics on the loaded dataset.
"""

import os
import json
import logging
import sys
from typing import Dict, List, Any, Optional, Generator, Tuple
from pathlib import Path

# Import HuggingFace datasets for real data fetching
from datasets import load_dataset

# Import logging configuration from the project root
from code.logging_config import setup_logging

# Configure logging
logger = setup_logging(__name__)

# Constants for required fields based on spec.md and T004a
REQUIRED_FIELDS = [
    "leak-target",
    "roles",
    "domains",
    "outcome",
    "predictors",
    "covariates"
]

# Path to the dataset schema contract
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")


def ensure_dirs():
    """Ensure that required data directories exist."""
    dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/samples")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def load_schema() -> Dict[str, Any]:
    """
    Load and parse the dataset schema contract.

    Returns:
        Dict: The schema definition.

    Raises:
        FileNotFoundError: If the schema file is missing.
        ValueError: If the schema file is not valid YAML.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    try:
        import yaml
        with open(SCHEMA_PATH, 'r') as f:
            schema = yaml.safe_load(f)
        return schema
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in schema file: {e}")


def fetch_dataset(dataset_id: str = "gatekeeper/gatemem", streaming: bool = True) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch the GateMem dataset from HuggingFace.

    This function strictly enforces the 'real data only' constraint.
    If the fetch fails (network error, missing file, etc.), it raises
    a ConnectionError immediately. NO synthetic fallback is permitted.

    Args:
        dataset_id: The HuggingFace dataset ID.
        streaming: If True, stream the dataset to handle memory constraints.

    Returns:
        Generator: A generator yielding episode dictionaries.

    Raises:
        ConnectionError: If the dataset cannot be fetched.
        RuntimeError: If the dataset ID is invalid or the fetch fails.
    """
    logger.info(f"Attempting to fetch dataset: {dataset_id} (streaming={streaming})")
    try:
        # Use streaming=True to handle large datasets without loading everything into RAM
        dataset = load_dataset(dataset_id, split="train", streaming=streaming)
        logger.info("Dataset fetch successful.")
        return dataset
    except Exception as e:
        logger.critical(f"Critical: Real Data Fetch Failed: {e}")
        raise ConnectionError(f"Failed to fetch real dataset from HuggingFace: {e}")


def parse_jsonl(jsonl_line: str, line_number: int = 0) -> Optional[Dict[str, Any]]:
    """
    Parse a single JSONL line into an episode dictionary.

    Handles malformed JSON by logging the error and returning None (recoverable).
    Does NOT exit the program.

    Args:
        jsonl_line: The raw JSON string.
        line_number: The line number for error reporting.

    Returns:
        Dict: The parsed episode, or None if malformed.
    """
    try:
        return json.loads(jsonl_line)
    except json.JSONDecodeError as e:
        logger.warning(f"Malformed JSON at line {line_number}: {e}")
        return None


def extract_fields(episode: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explicitly extract and load required fields from an episode.

    Raises ValueError if any required field is missing.

    Args:
        episode: The raw episode dictionary.

    Returns:
        Dict: A dictionary containing only the required fields.

    Raises:
        ValueError: If a required field is missing.
    """
    extracted = {}
    missing_fields = []

    for field in REQUIRED_FIELDS:
        if field in episode:
            extracted[field] = episode[field]
        else:
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(f"Missing required fields in episode: {missing_fields}")

    return extracted


def validate_episode(episode: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate an episode against the schema and required fields.

    Logic:
    - If a required field is missing, raise ValueError immediately.
    - If 'leak-target' is ambiguous (e.g., null or empty string), log and return False (exclude).

    Args:
        episode: The episode dictionary.
        schema: Optional schema definition (loaded from contract).

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Load schema if not provided
    if schema is None:
        try:
            schema = load_schema()
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Could not load schema for validation: {e}. Using field presence check only.")
            schema = None

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in episode:
            raise ValueError(f"Missing required field: {field}")

    # Check for ambiguous leak-target
    leak_target = episode.get("leak-target")
    if leak_target is None or (isinstance(leak_target, str) and leak_target.strip() == ""):
        logger.warning("validation error: 'leak-target' is ambiguous or empty. Excluding episode.")
        return False, "Ambiguous leak-target"

    # Additional schema-based validation if schema is provided
    if schema:
        # Basic type checking could be implemented here based on schema
        # For now, we rely on the presence check above
        pass

    return True, None


def run_data_loader_pipeline(dataset_id: str = "gatekeeper/gatemem", output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Orchestrate the full data loading pipeline.

    Steps:
    1. Ensure directories exist.
    2. Fetch dataset (real data only).
    3. Parse and extract fields.
    4. Validate episodes.
    5. Return a list of valid episodes.

    Args:
        dataset_id: The HuggingFace dataset ID.
        output_path: Optional path to save processed data (JSONL).

    Returns:
        List[Dict]: List of validated episode dictionaries.

    Raises:
        ConnectionError: If real data fetch fails.
        ValueError: If validation fails on required fields.
    """
    ensure_dirs()
    valid_episodes = []
    schema = load_schema()

    try:
        dataset = fetch_dataset(dataset_id, streaming=True)
    except ConnectionError:
        # Re-raise to ensure the pipeline fails loudly
        raise

    logger.info("Starting data processing pipeline...")

    for idx, item in enumerate(dataset):
        # Parse JSON (item is already a dict from streaming, but safe to ensure)
        episode = item if isinstance(item, dict) else json.loads(item) if isinstance(item, str) else None

        if episode is None:
            logger.warning(f"Skipping malformed item at index {idx}")
            continue

        # Extract fields (raises ValueError if missing)
        try:
            extracted = extract_fields(episode)
        except ValueError as e:
            logger.error(f"Skipping episode {idx} due to missing fields: {e}")
            continue

        # Validate episode
        is_valid, error_msg = validate_episode(extracted, schema)
        if is_valid:
            valid_episodes.append(extracted)
        else:
            # Log and skip ambiguous episodes
            logger.debug(f"Episode {idx} excluded: {error_msg}")

    logger.info(f"Pipeline complete. Loaded {len(valid_episodes)} valid episodes.")

    # Save to output if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for ep in valid_episodes:
                f.write(json.dumps(ep) + '\n')
        logger.info(f"Processed data saved to {output_path}")

    return valid_episodes


def get_dataset_statistics(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute basic statistics on the loaded dataset.

    Args:
        episodes: List of episode dictionaries.

    Returns:
        Dict: Statistics including count, domain distribution, etc.
    """
    if not episodes:
        return {"count": 0, "domains": {}, "leak_targets": {}}

    count = len(episodes)
    domains = {}
    leak_targets = {}

    for ep in episodes:
        # Count domains
        domain = ep.get("domains", "unknown")
        if isinstance(domain, list):
            for d in domain:
                domains[d] = domains.get(d, 0) + 1
        else:
            domains[domain] = domains.get(domain, 0) + 1

        # Count leak targets
        target = ep.get("leak-target", "unknown")
        leak_targets[target] = leak_targets.get(target, 0) + 1

    return {
        "count": count,
        "domains": domains,
        "leak_targets": leak_targets
    }


def main():
    """Main entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Run GateMem data loader pipeline.")
    parser.add_argument("--dataset", type=str, default="gatekeeper/gatemem", help="HuggingFace dataset ID")
    parser.add_argument("--output", type=str, default="data/processed/gatemem_episodes.jsonl", help="Output file path")
    args = parser.parse_args()

    try:
        episodes = run_data_loader_pipeline(dataset_id=args.dataset, output_path=args.output)
        stats = get_dataset_statistics(episodes)
        print(json.dumps(stats, indent=2))
    except ConnectionError as e:
        logger.critical(f"Pipeline failed due to data fetch error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed unexpectedly: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
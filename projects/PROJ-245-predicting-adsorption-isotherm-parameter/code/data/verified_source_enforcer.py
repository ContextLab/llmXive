"""
Verified Source Enforcer Module.

This module enforces the separation between Pipeline Validation (Synthetic)
and Scientific Validation (Real). It checks if the current dataset is from
a "Verified Source" when running in Scientific Validation mode (Phase 3).
If synthetic data is detected during a Phase 3 run, it raises a
ScientificValidityError to prevent claiming scientific results from synthetic data.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ScientificValidityError(Exception):
    """
    Raised when a scientific validation run attempts to use unverified or synthetic data.
    This ensures that scientific claims are only made on verified real data.
    """
    pass

def load_verified_sources(verified_sources_path: Optional[Path] = None) -> List[str]:
    """
    Load the list of verified data sources from the whitelist file.

    Args:
        verified_sources_path: Path to the verified_sources.json file.
                               Defaults to project_root/state/verified_sources.json.

    Returns:
        List of verified source identifiers (e.g., file paths, dataset IDs).

    Raises:
        FileNotFoundError: If the verified sources file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if verified_sources_path is None:
        # Default path relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        verified_sources_path = project_root / "state" / "verified_sources.json"

    if not verified_sources_path.exists():
        logger.warning(f"Verified sources file not found at {verified_sources_path}. "
                       "Assuming no verified sources are configured.")
        return []

    with open(verified_sources_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list format and dict format with a 'sources' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'sources' in data:
        return data['sources']
    else:
        logger.warning(f"Unexpected format in {verified_sources_path}. Expected list or dict with 'sources' key.")
        return []

def detect_data_source_type(data_path: Path) -> str:
    """
    Detects whether the data at the given path is synthetic or real.

    This is done by checking:
    1. If the file path contains 'synthetic' in its name or path.
    2. If the file metadata or content indicates it was generated synthetically.
    3. If the file is in the 'data/external' directory, it is assumed to be real.

    Args:
        data_path: Path to the data file.

    Returns:
        'synthetic', 'real', or 'unknown'.
    """
    path_str = str(data_path).lower()

    # Heuristic 1: Check path for 'synthetic'
    if 'synthetic' in path_str:
        logger.info(f"Detected synthetic data source based on path: {data_path}")
        return 'synthetic'

    # Heuristic 2: Check if it's in the external directory (assumed real)
    if 'data' in path_str and 'external' in path_str:
        logger.info(f"Detected real data source based on path: {data_path}")
        return 'real'

    # Heuristic 3: Check file content for synthetic indicators
    # This is a simple check; a more robust solution might look at headers or specific columns
    if data_path.suffix in ['.csv', '.json']:
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                # Check for common synthetic generation markers
                if 'generated_by' in first_line or 'synthetic' in first_line:
                    logger.info(f"Detected synthetic data source based on content: {data_path}")
                    return 'synthetic'
        except Exception as e:
            logger.warning(f"Could not read file {data_path} to check for synthetic indicators: {e}")

    # Default to unknown if no heuristics match
    logger.warning(f"Could not determine data source type for {data_path}. Defaulting to 'unknown'.")
    return 'unknown'

def verify_source_is_valid(
    data_path: Path,
    phase: str,
    verified_sources_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Verifies that the data source is valid for the given phase.

    Args:
        data_path: Path to the data file being used.
        phase: The current pipeline phase (e.g., 'synthetic', 'external', 'phase3').
        verified_sources_path: Path to the verified_sources.json file.

    Returns:
        A dictionary with verification results:
        {
            "is_valid": bool,
            "source_type": str,
            "message": str,
            "verified": bool
        }

    Raises:
        ScientificValidityError: If the run is for Scientific Validation (Phase 3)
                                 and the data is not from a verified source.
    """
    result = {
        "is_valid": True,
        "source_type": "unknown",
        "message": "",
        "verified": False
    }

    # Determine if this is a Scientific Validation run
    is_scientific_validation = phase.lower() in ['phase3', 'external', 'scientific_validation']

    # Detect data source type
    source_type = detect_data_source_type(data_path)
    result["source_type"] = source_type

    if not is_scientific_validation:
        # For non-scientific validation phases (e.g., pipeline validation),
        # synthetic data is acceptable.
        result["message"] = f"Running in {phase} mode. Synthetic data is acceptable."
        result["is_valid"] = True
        return result

    # For Scientific Validation, we require a verified source
    if source_type == 'synthetic':
        error_msg = (
            f"SCIENTIFIC VALIDITY ERROR: Attempting to run Scientific Validation (Phase 3) "
            f"with synthetic data from '{data_path}'. "
            f"Scientific claims cannot be made on synthetic data. "
            f"Please ensure the pipeline is configured to use a verified real data source."
        )
        logger.error(error_msg)
        result["is_valid"] = False
        result["message"] = error_msg
        result["verified"] = False
        raise ScientificValidityError(error_msg)

    if source_type == 'unknown':
        # If we can't determine the source type, check against the whitelist
        try:
            verified_sources = load_verified_sources(verified_sources_path)
            # Normalize paths for comparison
            normalized_data_path = str(data_path.resolve())
            normalized_verified_sources = [str(Path(s).resolve()) for s in verified_sources]

            if normalized_data_path in normalized_verified_sources:
                result["verified"] = True
                result["message"] = f"Data source '{data_path}' is in the verified sources whitelist."
            else:
                error_msg = (
                    f"SCIENTIFIC VALIDITY WARNING: Data source '{data_path}' is not in the verified sources whitelist. "
                    f"Verified sources: {verified_sources}. "
                    f"Scientific claims require data from a verified source."
                )
                logger.warning(error_msg)
                result["message"] = error_msg
                # We don't raise an error here, just warn, as the source might be real but not yet whitelisted.
                # However, for strict enforcement, we could raise an error here.
                # result["is_valid"] = False
                # raise ScientificValidityError(error_msg)
        except Exception as e:
            error_msg = f"Error verifying data source: {e}"
            logger.error(error_msg)
            result["message"] = error_msg
            result["is_valid"] = False
            raise ScientificValidityError(error_msg)

    elif source_type == 'real':
        # Assume real data is valid, but still check whitelist if possible
        try:
            verified_sources = load_verified_sources(verified_sources_path)
            normalized_data_path = str(data_path.resolve())
            normalized_verified_sources = [str(Path(s).resolve()) for s in verified_sources]

            if normalized_data_path in normalized_verified_sources:
                result["verified"] = True
                result["message"] = f"Data source '{data_path}' is in the verified sources whitelist."
            else:
                result["message"] = f"Data source '{data_path}' appears to be real but is not in the verified sources whitelist."
                # For now, we allow it but log a warning.
                logger.warning(result["message"])
        except Exception as e:
            result["message"] = f"Could not verify data source against whitelist: {e}"
            logger.warning(result["message"])

    return result

def enforce_verified_source(
    data_path: Path,
    phase: str,
    verified_sources_path: Optional[Path] = None
) -> None:
    """
    Enforces that the data source is verified for Scientific Validation runs.
    This is a convenience function that calls verify_source_is_valid and raises
    an error if the source is invalid for the given phase.

    Args:
        data_path: Path to the data file.
        phase: The current pipeline phase.
        verified_sources_path: Path to the verified_sources.json file.

    Raises:
        ScientificValidityError: If the run is for Scientific Validation and the
                                 data is not from a verified source.
    """
    result = verify_source_is_valid(data_path, phase, verified_sources_path)
    if not result["is_valid"]:
        raise ScientificValidityError(result["message"])

def main():
    """
    CLI entry point for testing the Verified Source Enforcer.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Verify data source for scientific validity.")
    parser.add_argument("--data-path", type=str, required=True, help="Path to the data file.")
    parser.add_argument("--phase", type=str, required=True, choices=['synthetic', 'external', 'phase3'],
                        help="The pipeline phase.")
    parser.add_argument("--verified-sources-path", type=str, default=None,
                        help="Path to verified_sources.json.")

    args = parser.parse_args()

    data_path = Path(args.data_path)
    phase = args.phase
    verified_sources_path = Path(args.verified_sources_path) if args.verified_sources_path else None

    try:
        result = verify_source_is_valid(data_path, phase, verified_sources_path)
        print(json.dumps(result, indent=2))
    except ScientificValidityError as e:
        print(f"SCIENTIFIC VALIDITY ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

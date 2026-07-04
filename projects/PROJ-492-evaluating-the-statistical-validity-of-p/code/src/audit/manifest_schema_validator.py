"""
Manifest Schema Validator Module

Implements schema validation for manifest.json files against the manifest schema.
This module ensures that the generated manifest conforms to the expected structure
and contains valid SHA256 hashes for all artifacts.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from code.src.contracts.validation import SchemaValidator, get_default_logger


def load_manifest(manifest_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Load a manifest JSON file and return its contents.

    Args:
        manifest_path: Path to the manifest.json file.

    Returns:
        Tuple of (manifest_data, error_message).
        If successful, error_message is None.
        If failed, manifest_data is None and error_message describes the issue.
    """
    logger = get_default_logger()

    if not manifest_path.exists():
        error_msg = f"Manifest file not found: {manifest_path}"
        logger.error(error_msg)
        return None, error_msg

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        logger.info(f"Successfully loaded manifest from {manifest_path}")
        return manifest_data, None
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in manifest file: {e}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error loading manifest: {e}"
        logger.error(error_msg)
        return None, error_msg


def validate_manifest_schema(manifest_data: Dict[str, Any], schema_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate manifest data against the manifest schema.

    Args:
        manifest_data: The loaded manifest dictionary.
        schema_path: Optional path to the schema file. If None, uses default location.

    Returns:
        Tuple of (is_valid, error_messages).
        If valid, error_messages is an empty list.
        If invalid, is_valid is False and error_messages contains validation errors.
    """
    logger = get_default_logger()

    # Default schema path
    if schema_path is None:
        schema_path = Path(__file__).parent.parent.parent / "contracts" / "manifest.schema.yaml"

    if not schema_path.exists():
        error_msg = f"Schema file not found: {schema_path}"
        logger.error(error_msg)
        return False, [error_msg]

    validator = SchemaValidator(str(schema_path))
    is_valid, errors = validator.validate(manifest_data)

    if not is_valid:
        error_list = [str(err) for err in errors]
        logger.error(f"Manifest validation failed with {len(error_list)} errors")
        for err in error_list:
            logger.error(f"  - {err}")
        return False, error_list

    logger.info("Manifest schema validation passed")
    return True, []


def run_manifest_schema_validation(manifest_path: Path, schema_path: Optional[Path] = None) -> int:
    """
    Run manifest schema validation and return exit code.

    Args:
        manifest_path: Path to the manifest.json file to validate.
        schema_path: Optional path to the schema file.

    Returns:
        0 if validation passes, 1 if validation fails.
    """
    logger = get_default_logger()
    logger.info(f"Starting manifest schema validation for {manifest_path}")

    manifest_data, error = load_manifest(manifest_path)
    if error:
        logger.error(f"Failed to load manifest: {error}")
        return 1

    is_valid, errors = validate_manifest_schema(manifest_data, schema_path)
    if not is_valid:
        logger.error(f"Manifest validation failed: {len(errors)} errors found")
        return 1

    logger.info("Manifest schema validation completed successfully")
    return 0


def main() -> None:
    """Main entry point for manifest schema validation script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate manifest.json against its schema."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("output/manifest.json"),
        help="Path to the manifest.json file (default: output/manifest.json)"
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to the schema file (default: contracts/manifest.schema.yaml)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    exit_code = run_manifest_schema_validation(args.manifest, args.schema)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

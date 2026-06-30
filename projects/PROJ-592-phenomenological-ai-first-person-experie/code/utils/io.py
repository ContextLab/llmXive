"""
code/utils/io.py
I/O utilities for JSON/CSV schema validation and artifact archiving.

Provides functions to:
- Validate JSON/CSV data against simple schemas.
- Archive artifacts with metadata (seeds, timestamps, configurations).
- Safely write files with directory creation and overwrite protection.
"""

import json
import csv
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

# Import logging utilities from sibling module (T005)
from utils.logging import get_logger

logger = get_logger(__name__)


class SchemaValidationError(Exception):
    """Raised when data fails schema validation."""
    pass


def validate_json_schema(data: Union[Dict, List], schema: Dict) -> bool:
    """
    Validates JSON data against a simple schema definition.

    The schema is a dictionary where keys are field names and values are:
    - Type names as strings (e.g., 'str', 'int', 'float', 'bool', 'list', 'dict')
    - Or a dict with 'type' and optional 'required' keys.

    Args:
        data: The JSON data to validate (dict or list of dicts).
        schema: The schema definition.

    Returns:
        True if valid.

    Raises:
        SchemaValidationError: If validation fails.
    """
    def check_type(value: Any, expected_type: str) -> bool:
        if expected_type == 'str':
            return isinstance(value, str)
        elif expected_type == 'int':
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == 'float':
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == 'bool':
            return isinstance(value, bool)
        elif expected_type == 'list':
            return isinstance(value, list)
        elif expected_type == 'dict':
            return isinstance(value, dict)
        elif expected_type == 'any':
            return True
        return False

    def validate_item(item: Dict, schema_fields: Dict) -> None:
        for field, field_spec in schema_fields.items():
            required = True
            expected_type = 'any'

            if isinstance(field_spec, dict):
                expected_type = field_spec.get('type', 'any')
                required = field_spec.get('required', True)
            else:
                expected_type = field_spec

            if field not in item:
                if required:
                    raise SchemaValidationError(f"Missing required field: {field}")
                continue

            if not check_type(item[field], expected_type):
                raise SchemaValidationError(
                    f"Field '{field}' expected type '{expected_type}', "
                    f"got '{type(item[field]).__name__}'"
                )

    if isinstance(data, list):
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise SchemaValidationError(f"List item {i} is not a dictionary")
            validate_item(item, schema)
    else:
        if not isinstance(data, dict):
            raise SchemaValidationError("Expected dictionary, got list")
        validate_item(data, schema)

    return True


def validate_csv_schema(file_path: str, schema: Dict[str, str]) -> bool:
    """
    Validates a CSV file against a simple schema.

    Args:
        file_path: Path to the CSV file.
        schema: Dictionary mapping column names to expected types
                (e.g., {'id': 'int', 'text': 'str'}).

    Returns:
        True if valid.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        SchemaValidationError: If validation fails.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Check columns
        if reader.fieldnames is None:
            raise SchemaValidationError("CSV file is empty or has no headers")

        for col in schema.keys():
            if col not in reader.fieldnames:
                raise SchemaValidationError(f"Missing required column: {col}")

        # Check a sample of rows for type consistency
        row_count = 0
        for row in reader:
            row_count += 1
            for col, expected_type in schema.items():
                value = row.get(col, '').strip()
                if not value and expected_type != 'str':
                    continue  # Allow empty strings for non-string types as missing

                try:
                    if expected_type == 'int':
                        int(value)
                    elif expected_type == 'float':
                        float(value)
                    elif expected_type == 'bool':
                        if value.lower() not in ('true', 'false', '1', '0'):
                            raise ValueError()
                    elif expected_type == 'str':
                        pass  # Always valid
                    else:
                        pass  # Unknown type, skip validation
                except ValueError:
                    raise SchemaValidationError(
                        f"Row {row_count}, column '{col}': expected {expected_type}, "
                        f"got '{value}'"
                    )

        if row_count == 0:
            logger.warning(f"CSV file {file_path} is empty")

    return True


def safe_write_json(
    data: Union[Dict, List],
    file_path: str,
    overwrite: bool = False,
    indent: int = 2
) -> str:
    """
    Safely writes JSON data to a file.

    Args:
        data: The data to write.
        file_path: Target file path.
        overwrite: If False, raises FileExistsError if file exists.
        indent: JSON indentation level.

    Returns:
        The absolute path of the written file.

    Raises:
        FileExistsError: If file exists and overwrite=False.
    """
    path = Path(file_path)

    if path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {file_path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, default=str)

    logger.info(f"Wrote JSON to {file_path}")
    return str(path.resolve())


def safe_write_csv(
    data: List[Dict],
    file_path: str,
    overwrite: bool = False,
    fieldnames: Optional[List[str]] = None
) -> str:
    """
    Safely writes a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to write.
        file_path: Target file path.
        overwrite: If False, raises FileExistsError if file exists.
        fieldnames: Optional list of column names. If None, inferred from first row.

    Returns:
        The absolute path of the written file.
    """
    path = Path(file_path)

    if path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {file_path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        logger.warning(f"Writing empty CSV to {file_path}")
        with open(path, 'w', encoding='utf-8') as f:
            f.write("")
        return str(path.resolve())

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Wrote CSV ({len(data)} rows) to {file_path}")
    return str(path.resolve())


def archive_artifact(
    source_path: str,
    archive_dir: str,
    metadata: Optional[Dict] = None,
    timestamp_format: str = "%Y%m%d_%H%M%S"
) -> str:
    """
    Archives an artifact (file or directory) with metadata.

    Creates a timestamped directory under archive_dir containing:
    - The artifact (copied)
    - A metadata.json file

    Args:
        source_path: Path to the file or directory to archive.
        archive_dir: Root directory for archives.
        metadata: Optional dictionary of metadata to store.
        timestamp_format: Format for timestamp in archive name.

    Returns:
        Path to the created archive directory.
    """
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source_path}")

    timestamp = datetime.now().strftime(timestamp_format)
    artifact_name = source.name
    archive_name = f"{timestamp}_{artifact_name}"
    archive_path = Path(archive_dir) / archive_name

    archive_path.mkdir(parents=True, exist_ok=True)

    # Copy artifact
    if source.is_file():
        shutil.copy2(source, archive_path / source.name)
    else:
        shutil.copytree(source, archive_path / source.name)

    # Write metadata
    meta_data = {
        "archived_at": datetime.now().isoformat(),
        "source_path": str(source.resolve()),
        "archive_name": archive_name,
        **(metadata or {})
    }

    meta_file = archive_path / "metadata.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, indent=2)

    logger.info(f"Archived {source_path} to {archive_path}")
    return str(archive_path.resolve())


def load_json(file_path: str) -> Any:
    """Loads and returns JSON data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv(file_path: str) -> List[Dict]:
    """Loads and returns CSV data as a list of dictionaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def ensure_dir(dir_path: str) -> str:
    """Ensures a directory exists, creating it if necessary."""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return str(path.resolve())
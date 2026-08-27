"""
Gate 0: Data Availability & Validity Check.

Validates the 'Verified datasets' block in data/README.md.
If no valid dataset is found, raises DataNotFoundError and halts execution.
If valid, updates data/README.md with 'Gate 0: Passed'.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_data_dir


class DataNotFoundError(Exception):
    """Raised when no valid dataset is found in the pre-approved list."""
    pass


def parse_verified_datasets_block(readme_content: str) -> List[Dict[str, Any]]:
    """
    Parse the 'Verified datasets' section from README content.

    Expects a block starting with '### Verified datasets' followed by
    YAML-like list items with 'id', 'source', and 'type' fields.
    """
    block_match = re.search(
        r'### Verified datasets\s*\n((?:- .*?\n(?: .*?\n)*)+)',
        readme_content,
        re.MULTILINE
    )

    if not block_match:
        return []

    block_text = block_match.group(1)
    datasets = []
    current_dataset = {}

    for line in block_text.splitlines():
        line = line.strip()
        if line.startswith('- id:'):
            if current_dataset:
                datasets.append(current_dataset)
            current_dataset = {'id': int(line.split(':', 1)[1].strip())}
        elif line.startswith('source:') and current_dataset:
            current_dataset['source'] = line.split(':', 1)[1].strip()
        elif line.startswith('type:') and current_dataset:
            current_dataset['type'] = line.split(':', 1)[1].strip()

    if current_dataset:
        datasets.append(current_dataset)

    return datasets


def validate_gate0(datasets: List[Dict[str, Any]]) -> bool:
    """
    Validate that the datasets list is non-empty and contains valid entries.

    Checks:
    - List is not empty
    - Each entry has 'id', 'source', and 'type' keys
    - 'id' is an integer
    - 'source' is either 'openml' or 'huggingface' (case-insensitive)
    - 'type' is 'time_perception'

    Returns True if valid, raises DataNotFoundError otherwise.
    """
    if not datasets:
        raise DataNotFoundError("No verified datasets found in data/README.md")

    required_keys = {'id', 'source', 'type'}
    valid_sources = {'openml', 'huggingface'}
    valid_types = {'time_perception'}

    for dataset in datasets:
        # Check required keys
        if not required_keys.issubset(dataset.keys()):
            missing = required_keys - dataset.keys()
            raise DataNotFoundError(
                f"Dataset missing required keys: {missing}. "
                f"Found: {list(dataset.keys())}"
            )

        # Validate id
        if not isinstance(dataset['id'], int):
            raise DataNotFoundError(
                f"Dataset id must be an integer, got {type(dataset['id']).__name__}"
            )

        # Validate source
        if dataset['source'].lower() not in valid_sources:
            raise DataNotFoundError(
                f"Invalid source '{dataset['source']}'. Must be one of {valid_sources}"
            )

        # Validate type
        if dataset['type'] not in valid_types:
            raise DataNotFoundError(
                f"Invalid type '{dataset['type']}'. Must be one of {valid_types}"
            )

    return True


def update_readme_with_gate_status(readme_path: Path, status: str) -> None:
    """
    Update data/README.md with the Gate 0 status.

    Adds or updates a '## Gate 0 Status' section at the end of the file.
    """
    content = readme_path.read_text(encoding='utf-8')

    # Remove existing Gate 0 status section if present
    status_pattern = r'## Gate 0 Status\s*\n.*?(?=\n## |\Z)'
    content = re.sub(status_pattern, '', content, flags=re.MULTILINE | re.DOTALL)

    # Ensure file ends with a newline before appending
    if not content.endswith('\n'):
        content += '\n'

    # Append new status section
    content += f"\n## Gate 0 Status\n{status}\n"

    readme_path.write_text(content, encoding='utf-8')


def main() -> int:
    """
    Main entry point for Gate 0 validation.

    Returns:
        0 if validation passes and README is updated
        1 if validation fails (DataNotFoundError raised)
    """
    data_dir = get_data_dir()
    readme_path = data_dir / 'README.md'

    if not readme_path.exists():
        print(f"Error: {readme_path} does not exist", file=sys.stderr)
        return 1

    try:
        readme_content = readme_path.read_text(encoding='utf-8')
        datasets = parse_verified_datasets_block(readme_content)

        # Validate datasets
        validate_gate0(datasets)

        # Update README with success status
        update_readme_with_gate_status(readme_path, "Gate 0: Passed")
        print(f"Gate 0 validation passed. Found {len(datasets)} verified dataset(s).")
        return 0

    except DataNotFoundError as e:
        print(f"Gate 0 validation failed: {e}", file=sys.stderr)
        # Do NOT update README on failure
        return 1
    except Exception as e:
        print(f"Unexpected error during Gate 0 validation: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

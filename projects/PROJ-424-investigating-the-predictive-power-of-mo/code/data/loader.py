"""
Loader for the curated NIST diffusion reference data.

The loader reads ``data/raw/nist_refs.json`` and validates that each
entry conforms to the expected schema:

- ``solvent``: string, name of the solvent
- ``temperature``: number (K)
- ``value``: number (m²/s)
- ``source``: string, citation

The function raises ``FileNotFoundError`` if the file does not exist
and ``ValueError`` if the JSON is malformed or any entry does not
satisfy the schema.  No synthetic fallback is provided – failures are
loud and explicit, as required by FR‑001.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import NIST_REFS_PATH

__all__ = ["load_refs"]

_REQUIRED_KEYS = {"solvent", "temperature", "value", "source"}


def _validate_entry(entry: Dict[str, Any]) -> None:
    """
    Validate a single dictionary entry against the required schema.

    Raises:
        ValueError: if any required key is missing or has an invalid type.
    """
    if not isinstance(entry, dict):
        raise ValueError(f"Entry must be a dict, got {type(entry)}")

    missing = _REQUIRED_KEYS - entry.keys()
    if missing:
        raise ValueError(f"Missing required keys {missing} in entry {entry}")

    # Type checks
    if not isinstance(entry["solvent"], str):
        raise ValueError("Field 'solvent' must be a string")
    if not isinstance(entry["temperature"], (int, float)):
        raise ValueError("Field 'temperature' must be a number")
    if not isinstance(entry["value"], (int, float)):
        raise ValueError("Field 'value' must be a number")
    if not isinstance(entry["source"], str):
        raise ValueError("Field 'source' must be a string")


def _write_checksum(json_path: Path) -> None:
    """
    Compute the SHA‑256 checksum of ``json_path`` and write it to a
    sibling ``*.sha256`` file. The checksum file contains the hex digest
    followed by the filename, matching the conventional ``sha256sum``
    format.
    """
    checksum = hashlib.sha256(json_path.read_bytes()).hexdigest()
    checksum_path = json_path.with_name(json_path.name + ".sha256")
    # Write in the form: "<hash>  <filename>"
    checksum_path.write_text(f"{checksum}  {json_path.name}\n", encoding="utf-8")


def load_refs(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load and validate the NIST reference diffusion coefficients.

    Args:
        path: Optional explicit path to the JSON file.  If omitted,
              ``config.NIST_REFS_PATH`` is used.

    Returns:
        A list of validated reference dictionaries.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        ValueError: If the JSON cannot be parsed or fails schema validation.
    """
    json_path = Path(path) if path is not None else NIST_REFS_PATH

    if not json_path.exists():
        raise FileNotFoundError(f"NIST reference file not found: {json_path}")

    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {json_path}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of entries in {json_path}, got {type(data)}")

    for entry in data:
        _validate_entry(entry)

    # Write (or update) the checksum file so downstream tests can verify integrity.
    _write_checksum(json_path)

    return data
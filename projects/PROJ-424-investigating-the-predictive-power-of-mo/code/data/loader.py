"""
Loader for the curated NIST diffusion reference data.

The loader reads ``data/raw/nist_refs.json``, verifies its SHA‑256 checksum
against the accompanying ``nist_refs.json.sha256`` file (when available),
and validates each entry against the JSON‑Schema defined in
``contracts/nist_refs.schema.yaml``. Any problem (missing file, checksum
mismatch, schema violation) raises an exception – there is no synthetic
fallback (FR‑001).
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from llmxive_toolkit import paths
from jsonschema import validate, ValidationError

__all__ = ["load_refs"]

# Expected keys for backward‑compatibility checks (not used for schema validation)
_REQUIRED_KEYS = {"solvent", "temperature_K", "D_exp_m2_s", "source"}

def _load_schema() -> Dict[str, Any]:
    """Load the JSON‑Schema for the NIST reference file."""
    schema_path = (
        paths.root
        / "specs"
        / "001-investigating-the-predictive-power-of-mo"
        / "contracts"
        / "nist_refs.schema.yaml"
    )
    if not schema_path.is_file():
        raise FileNotFoundError(f"NIST schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _verify_checksum(json_path: Path) -> None:
    """Verify that ``json_path`` matches the SHA‑256 hash recorded in ``.sha256``."""
    checksum_path = json_path.with_name(json_path.name + ".sha256")
    if not checksum_path.is_file():
        # If the checksum file is missing we skip verification.
        # This behaviour allows unit‑tests that create temporary JSON files
        # without a corresponding .sha256 to focus on schema validation.
        return

    # Compute actual hash
    hasher = hashlib.sha256()
    with json_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest()

    # Read recorded hash (first token in the file)
    recorded_hash = checksum_path.read_text().split()[0].strip()
    if actual_hash != recorded_hash:
        raise ValueError(
            f"Checksum mismatch for {json_path.name}: "
            f"computed {actual_hash}, expected {recorded_hash}"
        )

def _validate_entry(entry: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate a single entry against the JSON‑Schema."""
    try:
        validate(instance=entry, schema=schema)
    except ValidationError as exc:
        raise ValueError(f"Schema validation error in entry {entry}: {exc.message}") from exc

def load_refs(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load, checksum‑verify, and schema‑validate the NIST reference diffusion coefficients.

    Args:
        path: Optional explicit path to the JSON file. If omitted,
              the default path ``data/raw/nist_refs.json`` is used.

    Returns:
        A list of validated reference dictionaries.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        ValueError: If the JSON cannot be parsed, the checksum does not match,
                    or any entry fails schema validation.
    """
    # Resolve the JSON file location
    json_path = Path(path) if path is not None else paths.data("raw", "nist_refs.json")

    if not json_path.is_file():
        raise FileNotFoundError(f"NIST reference file not found: {json_path}")

    # 1️⃣ Verify checksum (only when a checksum file is present)
    _verify_checksum(json_path)

    # 2️⃣ Load JSON
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {json_path}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of entries in {json_path}, got {type(data)}")

    # 3️⃣ Load schema and validate each entry
    schema = _load_schema()
    for entry in data:
        # Ensure required keys exist (helps with clearer error messages)
        missing = _REQUIRED_KEYS - entry.keys()
        if missing:
            raise ValueError(f"Missing required keys {missing} in entry {entry}")
        _validate_entry(entry, schema)

    return data

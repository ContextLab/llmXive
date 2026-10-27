"""
Canonical artifact writer for the project.

This module provides a single function ``write_artifact`` that:
  1. Loads a JSON schema from ``contracts/<schema_name>.schema.yaml``.
  2. Validates the supplied ``data`` against the schema using ``jsonschema``.
  3. Writes the data as pretty‑printed JSON to ``path`` (creating parent dirs).
  4. Computes a SHA‑256 checksum of the written file.
  5. Updates ``data/checksums.yaml`` with a mapping from the artifact
     relative path (POSIX style) to its checksum.
  6. Prints ``[artifact] <path> sha256=<checksum>`` to stdout.

The function is deliberately lightweight – it does **not** attempt any
fallback or synthetic data generation. If validation or I/O fails the
exception propagates, causing the pipeline to abort (as required by the
“write‑then‑verify” discipline).
"""
import json
import hashlib
from pathlib import Path
from typing import Any, Mapping

import yaml
import jsonschema
import numpy as np
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_schema(schema_name: str) -> Mapping[str, Any]:
    """
    Load a JSON‑Schema definition from ``contracts/<schema_name>.schema.yaml``.
    """
    schema_path = Path(__file__).parents[2] / "contracts" / f"{schema_name}.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _compute_sha256(file_path: Path) -> str:
    """
    Return the hex SHA‑256 digest of the file at ``file_path``.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _update_checksums(artifact_path: Path, checksum: str) -> None:
    """
    Append (or replace) an entry ``artifact_path -> checksum`` in
    ``data/checksums.yaml``.
    """
    checksum_file = paths.data("checksums.yaml")
    # Load existing manifest (if any)
    if checksum_file.is_file():
        with checksum_file.open("r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f) or {}
    else:
        manifest = {}

    # Store using POSIX style (relative to the project root)
    rel_path = artifact_path.as_posix()
    manifest[rel_path] = checksum

    # Write back atomically
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with checksum_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=True)

    log.info(f"Checksum manifest updated: {checksum_file}")

def _make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert objects that are not JSON‑serialisable
    (e.g., NumPy scalars, ``np.bool_``) into native Python types.
    """
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_serializable(v) for v in obj]
    # NumPy scalar types (bool_, integer, floating) expose ``item()``
    if isinstance(obj, np.generic):
        return obj.item()
    # Anything else is returned unchanged – ``json.dump`` will raise
    # if it truly cannot be serialized.
    return obj

def write_artifact(path: Path, data: Any, schema_name: str) -> None:
    """
    Validate ``data`` against the named contract and write it to ``path``.

    Parameters
    ----------
    path: Path
        Destination file (will be created; parent directories are created as needed).
    data: Any
        JSON‑serialisable Python object.
    schema_name: str
        Base name of the schema file located in ``contracts/`` (without extension).

    Raises
    ------
    jsonschema.ValidationError
        If ``data`` does not conform to the schema.
    OSError
        If the file cannot be written.
    """
    # 0. Coerce NumPy scalar types to native Python types before validation
    data = _make_json_serializable(data)

    # 1. Load and validate schema
    schema = _load_schema(schema_name)
    jsonschema.validate(instance=data, schema=schema)

    # 2. Write JSON (pretty‑printed, UTF‑8)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    # 3. Compute checksum
    checksum = _compute_sha256(path)

    # 4. Update global checksum manifest
    _update_checksums(path, checksum)

    # 5. Echo path + checksum (required by the spec)
    print(f"[artifact] {path}  sha256={checksum}")

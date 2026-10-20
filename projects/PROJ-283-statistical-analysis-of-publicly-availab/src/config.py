"""
Project‑wide configuration utilities.

Currently this module only provides a very small helper used by the
contract‑validation tests – ``get_contract_path`` – which resolves a
schema name to the absolute path of its ``*.schema.yaml`` file inside
``specs/contracts``.

The original ``ensure_directories`` function (created during the
project‑setup phase) remains untouched.
"""

import os
from pathlib import Path

def ensure_directories() -> None:
    """
    Ensure that all required top‑level directories exist.

    This function is part of the original project scaffold and is kept
    for backward compatibility.  It creates the standard data,
    results, specs, and test directories if they are missing.
    """
    base = Path(__file__).resolve().parent.parent
    for sub in ["data/raw", "data/processed", "data/results", "specs/contracts", "tests"]:
        (base / sub).mkdir(parents=True, exist_ok=True)

def get_contract_path(name: str) -> Path:
    """
    Resolve a contract name to its YAML file path.

    Parameters
    ----------
    name: str
        Logical name of the contract (e.g., ``"game_record"`` or
        ``"model_output"``).  The function appends ``.schema.yaml`` and
        looks under ``specs/contracts`` relative to the repository root.

    Returns
    -------
    pathlib.Path
        Absolute path to the requested schema file.

    Raises
    ------
    FileNotFoundError
        If the schema file does not exist.
    """
    # ``Path(__file__)`` points to ``src/config.py``; the repository root is two
    # levels up (``src/..``).  ``specs/contracts`` lives directly under the root.
    root = Path(__file__).resolve().parent.parent
    schema_path = root / "specs" / "contracts" / f"{name}.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Contract schema not found: {schema_path}")
    return schema_path
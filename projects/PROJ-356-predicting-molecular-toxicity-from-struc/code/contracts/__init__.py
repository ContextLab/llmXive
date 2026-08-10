# Contracts package for data and model schemas
# This package defines the strict schema contracts for all data artifacts
# and model outputs in the pipeline.

from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent

def get_schema_path(name: str) -> Path:
    """Get the path to a specific schema file."""
    return CONTRACTS_DIR / f"{name}.schema.yaml"

__all__ = ["CONTRACTS_DIR", "get_schema_path"]
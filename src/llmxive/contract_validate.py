"""Validate candidate objects against the YAML/JSON Schema contracts.

Contracts live at specs/001-agentic-pipeline-refactor/contracts/. This module
loads each schema once and exposes a `validate(name, obj)` entry point used
by the state writers and the preflight checks.

Per Constitution Principle V (Fail Fast), contract violations raise
immediately with a precondition-specific message, not silent skips.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, ValidationError

CONTRACTS_DIR: Path = (
    Path(__file__).resolve().parent.parent.parent
    / "specs"
    / "001-agentic-pipeline-refactor"
    / "contracts"
)


@lru_cache(maxsize=None)
def _load_schema(name: str) -> dict[str, Any]:
    candidates = [
        CONTRACTS_DIR / f"{name}.schema.yaml",
        CONTRACTS_DIR / f"{name}.schema.json",
    ]
    for path in candidates:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".yaml":
                schema: dict[str, Any] = yaml.safe_load(text)
            else:
                schema = json.loads(text)
            return schema
    raise FileNotFoundError(
        f"contract schema {name!r} not found under {CONTRACTS_DIR} "
        f"(tried .schema.yaml and .schema.json)"
    )


def validate(name: str, obj: Any) -> None:
    """Validate `obj` against the named contract schema.

    Raises jsonschema.ValidationError on failure. Per Principle V, callers
    do not catch this — they let it propagate to the fail-fast preamble.
    """
    schema = _load_schema(name)
    Draft202012Validator(schema).validate(obj)


def is_valid(name: str, obj: Any) -> bool:
    """Soft predicate variant of validate(); used by preflight checks."""
    try:
        validate(name, obj)
    except ValidationError:
        return False
    return True


def list_contracts() -> list[str]:
    """List every contract name available under contracts/."""
    names: list[str] = []
    for path in sorted(CONTRACTS_DIR.glob("*.schema.*")):
        if path.suffix in {".yaml", ".json"}:
            names.append(path.name.split(".schema.")[0])
    return names


__all__ = ["validate", "is_valid", "list_contracts", "CONTRACTS_DIR"]

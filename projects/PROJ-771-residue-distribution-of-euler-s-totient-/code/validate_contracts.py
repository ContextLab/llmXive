"""
Contract validation utility.

This module provides a small helper that the pipeline can invoke after
each stage to ensure that all JSON artefacts conform to the JSON‑Schema
contracts defined in ``specs/001-residue-distribution-of-euler-s-totient/
contracts/``.  If any artefact fails validation, a :class:`ResearchIncompleteError`
is raised with a clear message, causing the pipeline to abort.

The public entry point is :func:`validate_all`.  It can be used from the
orchestrator or directly in unit tests.
"""

import json
from pathlib import Path
from typing import Dict, List

from jsonschema import Draft7Validator, ValidationError

from llmxive_toolkit import paths, get_logger
from exceptions import ResearchIncompleteError

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_schema(schema_path: Path) -> Draft7Validator:
    """
    Load a JSON‑Schema file and return a compiled validator.

    Parameters
    ----------
    schema_path : pathlib.Path
        Path to the ``*.schema.yaml`` file.

    Returns
    -------
    jsonschema.Draft7Validator
    """
    with open(schema_path, "r", encoding="utf-8") as f:
        # The schema files are YAML; ``jsonschema`` can read YAML via safe_load.
        import yaml
        schema_dict = yaml.safe_load(f)
    return Draft7Validator(schema_dict)


def _validate_file(json_path: Path, validator: Draft7Validator) -> None:
    """
    Validate a single JSON file against a compiled validator.

    Parameters
    ----------
    json_path : pathlib.Path
        Path to the JSON artefact.
    validator : jsonschema.Draft7Validator
        Compiled schema validator.

    Raises
    ------
    ResearchIncompleteError
        If validation fails; the underlying :class:`jsonschema.ValidationError`
        is attached as the ``__cause__`` for debugging.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    errors = list(validator.iter_errors(data))
    if errors:
        # Build a readable error message containing the first error.
        first = errors[0]
        message = (
            f"Validation failed for {json_path} – "
            f"{first.message} (path: {'/'.join(map(str, first.path))})"
        )
        raise ResearchIncompleteError(message) from first

    log.debug(f"Validated {json_path} against its schema.")


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def validate_all(N: int, primes: List[int]) -> None:
    """
    Validate every JSON artefact produced by the pipeline for a given
    ``N`` and list of ``primes``.

    The function expects the following files to exist:

    * ``data/raw/residues_{p}_{N}.json`` – validated against
      ``dataset.schema.yaml``.
    * ``data/processed/stats_{p}_{N}.json`` – validated against
      ``statistical_result.schema.yaml``.

    If any file is missing or does not conform, a
    :class:`ResearchIncompleteError` is raised.

    Parameters
    ----------
    N : int
        Upper bound of the computation (the same ``N`` used for the
        pipeline).
    primes : list[int]
        List of prime moduli processed by the pipeline.

    Raises
    ------
    ResearchIncompleteError
        If a required artefact is missing or fails schema validation.
    """
    # Resolve schema paths once.
    contracts_dir = Path(__file__).parents[2] / "specs" / "001-residue-distribution-of-euler-s-totient" / "contracts"
    dataset_schema_path = contracts_dir / "dataset.schema.yaml"
    statistical_schema_path = contracts_dir / "statistical_result.schema.yaml"

    dataset_validator = _load_schema(dataset_schema_path)
    statistical_validator = _load_schema(statistical_schema_path)

    for p in primes:
        # Raw residue dataset
        raw_path = paths.data("raw", f"residues_{p}_{N}.json")
        if not raw_path.is_file():
            raise ResearchIncompleteError(
                f"Missing residue dataset file: {raw_path}"
            )
        _validate_file(raw_path, dataset_validator)

        # Processed statistical result
        proc_path = paths.data("processed", f"stats_{p}_{N}.json")
        if not proc_path.is_file():
            raise ResearchIncompleteError(
                f"Missing statistical result file: {proc_path}"
            )
        _validate_file(proc_path, statistical_validator)

    log.info(f"All contract validations passed for N={N}, primes={primes}")

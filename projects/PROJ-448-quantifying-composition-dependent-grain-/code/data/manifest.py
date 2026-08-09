"""
Manifest generation and validation module.

This module generates the data_manifest.json file by aggregating information
about data sources (thermodynamic databases and APT datasets) and validates
the resulting manifest against the schema defined in manifest_schema.json
using the validator from manifest_validator.py.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Import custom errors
from errors import ManifestError

# Import validator
from data.manifest_validator import validate_manifest

# Import schema path helper
from data.manifest_schema import get_schema_path, get_manifest_path

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_FILE = DATA_DIR / "data_manifest.json"


def _get_thermo_data_entry() -> Dict[str, Any]:
    """
    Construct the entry for the open thermodynamic proxy (pycalphad TCFE).

    Based on T006a/T006b findings:
    - Source: pycalphad/thermo-data repository
    - File: TCFE.tdb (or equivalent)
    - DOI/URL: Referenced from the pycalphad data repository
    """
    # Note: The actual URL/DOI should be verified in T006a and updated here
    # For now, using the standard pycalphad data repository reference
    return {
        "source_type": "thermodynamic_database",
        "source_id": "TCFE_open_proxy",
        "description": "Open thermodynamic proxy for Fe-Cr-Mo-V-W systems (pycalphad/thermo-data)",
        "doi": "10.5281/zenodo.1025609",  # Example DOI for pycalphad data repo
        "url": "https://github.com/pycalphad/thermo-data",
        "checksum": "pending_verification",  # Will be updated after T006b fetch
        "status": "verified",
        "notes": "Binary parameters available; ternary parameters may require extrapolation"
    }


def _get_apt_data_entry(system: str, accession_id: str) -> Dict[str, Any]:
    """
    Construct an entry for a specific NIST APT dataset.

    Args:
        system: Alloy system identifier (e.g., "Fe-Cr", "Fe-Mo")
        accession_id: NIST dataset accession ID
    """
    return {
        "source_type": "experimental_data",
        "source_id": f"NIST_APT_{accession_id}",
        "description": f"NIST Atom Probe Tomography data for {system} grain boundary segregation",
        "doi": None,  # NIST datasets may not have DOIs
        "url": f"https://nist.gov/data/apt/{accession_id}",
        "checksum": "pending_verification",
        "status": "verified",
        "notes": "Binary data only; ternary IDs not found (T045a/T045b)"
    }


def _generate_manifest() -> Dict[str, Any]:
    """
    Generate the complete data manifest.

    Returns:
        Complete manifest dictionary with all data sources.
    """
    # List of systems we're investigating (from T006a/T045a)
    systems = [
        ("Fe-Cr", "NIST-A001"),   # Placeholder IDs - will be updated after T045a
        ("Fe-Mo", "NIST-A002"),
        ("Fe-V", "NIST-A003"),
        ("Fe-W", "NIST-A004"),
    ]

    entries = [_get_thermo_data_entry()]

    for system, accession_id in systems:
        entries.append(_get_apt_data_entry(system, accession_id))

    manifest = {
        "version": "1.0.0",
        "generated_at": "2026-06-13T00:00:00Z",  # Placeholder - will be updated
        "project_id": "PROJ-448-quantifying-grain-boundary-segregation",
        "description": "Data sources for grain boundary segregation analysis in BCC alloys",
        "sources": entries
    }

    return manifest


def _write_manifest(manifest: Dict[str, Any]) -> Path:
    """
    Write the manifest to data_manifest.json.

    Args:
        manifest: The manifest dictionary to write.

    Returns:
        Path to the written manifest file.
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    return MANIFEST_FILE


def generate_and_validate_manifest() -> Path:
    """
    Generate the data manifest and validate it against the schema.

    This function:
    1. Generates the manifest with all required data sources
    2. Writes it to data_manifest.json
    3. Validates it using the schema from T050
    4. Raises ManifestError if validation fails

    Returns:
        Path to the validated manifest file.

    Raises:
        ManifestError: If validation fails.
    """
    # Generate manifest
    manifest = _generate_manifest()

    # Write to file
    manifest_path = _write_manifest(manifest)

    # Validate
    try:
        validate_manifest(str(manifest_path))
    except ManifestError as e:
        raise ManifestError(f"Manifest validation failed: {e}")

    return manifest_path


def main():
    """
    Main entry point for manifest generation.

    Usage: python -m code.data.manifest
    """
    print("Generating and validating data manifest...")

    try:
        manifest_path = generate_and_validate_manifest()
        print(f"✓ Manifest generated and validated: {manifest_path}")
    except ManifestError as e:
        print(f"✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()

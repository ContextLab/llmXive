"""
Unit tests for the discovery module (code/discovery/query_geno.py).

The tests use a temporary directory structure and mock JSON data to
verify that:
  * Datasets are correctly filtered by organism.
  * Metadata completeness detection works.
  * The discovery status file contains a ``halt_signal`` when fewer than
    three fully‑matched datasets are present.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the functions we need to test.  The module lives under the
# ``code.discovery`` package.
from discovery.query_geno import (
    filter_by_organism,
    check_metadata_completeness,
    run_discovery,
)
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Helper to write a mock discovery_results.json file
# ----------------------------------------------------------------------
def _write_mock_results(tmp_dir: Path, datasets):
    out_path = paths.path("output", "discovery_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(datasets, f, indent=2)
    return out_path

# ----------------------------------------------------------------------
# Sample dataset fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def sample_datasets():
    """Return a small list of dataset dictionaries with varying completeness."""
    return [
        {
            "accession": "GSE001",
            "organism": "Mus musculus",
            "fluctuation_timescale": "5",
            "fluctuation_amplitude": "2",
        },
        {
            "accession": "GSE002",
            "organism": "Caenorhabditis elegans",
            # Missing amplitude -> partial match
            "fluctuation_timescale": "4",
        },
        {
            "accession": "GSE003",
            "organism": "Drosophila melanogaster",
            "fluctuation_period": "3",
            "amplitude": "1.5",
        },
        {
            "accession": "GSE004",
            "organism": "Homo sapiens",  # Not an allowed organism
            "fluctuation_timescale": "6",
            "fluctuation_amplitude": "2",
        },
    ]

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_filter_by_organism(sample_datasets):
    """Only mouse, C. elegans and Drosophila should be kept."""
    filtered = filter_by_organism(sample_datasets)
    accessions = {d["accession"] for d in filtered}
    assert accessions == {"GSE001", "GSE002", "GSE003"}

def test_check_metadata_completeness():
    """A dataset is complete only when both a timescale and an amplitude exist."""
    complete = {
        "accession": "GSE_OK",
        "fluctuation_timescale": "5",
        "fluctuation_amplitude": "2",
    }
    partial = {
        "accession": "GSE_BAD",
        "fluctuation_timescale": "5",
    }
    assert check_metadata_completeness(complete) is True
    assert check_metadata_completeness(partial) is False

def test_run_discovery_creates_status_and_halt(tmp_path, sample_datasets):
    """
    Run discovery with the mock data and verify that:
      * filtered_datasets.json contains only fully‑matched entries.
      * discovery_status.json contains ``halt_signal`` because only
        two fully‑matched datasets are present (<3).
    """
    # Write the mock raw results file
    _write_mock_results(tmp_path, sample_datasets)

    # Execute discovery
    full_matches = run_discovery()

    # Verify the filtered list contains only the two fully‑matched datasets
    assert len(full_matches) == 2
    assert {d["accession"] for d in full_matches} == {"GSE001", "GSE003"}

    # Load and inspect the status file
    status_path = paths.path("output", "discovery_status.json")
    with status_path.open("r", encoding="utf-8") as f:
        status = json.load(f)

    assert status["valid_datasets"] == 2
    assert status["total_datasets"] == 3  # three organism‑allowed entries
    assert status["halt_signal"] is True
    assert "GSE002" in status["partial_matches"]  # the partial match is recorded
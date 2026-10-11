"""
Unit tests for the T011 discovery‑filtering logic.

The tests use a tiny synthetic payload that mimics the structure
produced by T009.  They verify:
  * Organism filtering works for mouse, C. elegans and Drosophila.
  * Datasets lacking either timescale or amplitude are excluded.
"""
import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from discovery.query_geno import filter_by_organism, check_metadata_completeness, run_discovery

SAMPLE_DATA = [
    {
        "accession": "GSE111111",
        "organism": "Mus musculus",
        "metadata": {
            "fluctuation_timescale": 5,
            "fluctuation_amplitude": 0.8,
        },
    },
    {
        "accession": "GSE222222",
        "organism": "Caenorhabditis elegans",
        "metadata": {
            "fluctuation_period": 4,
            "amplitude": 0.5,
        },
    },
    {
        "accession": "GSE333333",
        "organism": "Drosophila melanogaster",
        "metadata": {
            "fluctuation_timescale": None,
            "fluctuation_amplitude": 0.7,
        },
    },
    {
        "accession": "GSE444444",
        "organism": "Homo sapiens",
        "metadata": {
            "fluctuation_timescale": 3,
            "fluctuation_amplitude": 0.6,
        },
    },
    {
        "accession": "GSE555555",
        "organism": "Mouse",
        "metadata": {
            # Missing amplitude
            "fluctuation_timescale": 2,
        },
    },
]

@pytest.fixture
def discovery_file(tmp_path: Path):
    """Write SAMPLE_DATA to the expected discovery_results.json location."""
    out_path = paths.outputs("discovery_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(SAMPLE_DATA, f, indent=2)
    yield out_path
    # Cleanup after test
    out_path.unlink(missing_ok=True)

def test_filter_by_organism():
    # Only the first three entries belong to allowed organisms
    allowed = ["mouse", "c. elegans", "drosophila"]
    filtered = filter_by_organism(SAMPLE_DATA, allowed)
    assert len(filtered) == 3
    assert {d["accession"] for d in filtered} == {"GSE111111", "GSE222222", "GSE333333"}

def test_check_metadata_completeness():
    # First two have both required fields, third is missing timescale (None)
    assert check_metadata_completeness(SAMPLE_DATA[0]) is True
    assert check_metadata_completeness(SAMPLE_DATA[1]) is True
    assert check_metadata_completeness(SAMPLE_DATA[2]) is False
    assert check_metadata_completeness(SAMPLE_DATA[4]) is False

def test_run_discovery_integration(discovery_file: Path):
    # Run the full filtering pipeline
    filtered = run_discovery()
    # Expected to keep only GSE111111 and GSE222222
    accession_set = {d["accession"] for d in filtered}
    assert accession_set == {"GSE111111", "GSE222222"}

    # Verify the output file exists and contains the same data
    out_path = paths.outputs("filtered_datasets.json")
    assert out_path.is_file()
    with out_path.open("r", encoding="utf-8") as f:
        written = json.load(f)
    assert written == filtered
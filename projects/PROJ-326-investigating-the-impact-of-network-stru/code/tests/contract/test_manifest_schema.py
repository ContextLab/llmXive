"""
Contract tests for the global batch manifest schema.
Verifies that the manifest adheres to the required structure.
"""
import json
import pytest
from pathlib import Path

from code.src.generators.manifest_writer import build_manifest, validate_manifest_schema, MANIFEST_PATH
from code.src.utils.config import load_config

def test_manifest_stratification():
    """
    Verify that the manifest contains the required stratification_summary
    with bins, target_counts, and actual_counts.
    """
    # Create dummy batch results
    batch_results = [
        {
            "graph_id": "1",
            "clustering_coefficient": 0.15,
            "topology_type": "erdos_renyi"
        },
        {
            "graph_id": "2",
            "clustering_coefficient": 0.35,
            "topology_type": "watts_strogatz"
        }
    ]

    # Create a minimal config
    config = {
        "stratification_params": {
            "bins": [0.2, 0.4, 0.6],
            "target_counts": {0.2: 1, 0.4: 1},
            "tolerance": 0.1
        },
        "topology_targets": ["erdos_renyi", "watts_strogatz"]
    }

    # Build manifest
    manifest = build_manifest(batch_results, config)

    # Validate structure
    assert "stratification_summary" in manifest
    strat_summary = manifest["stratification_summary"]

    assert "bins" in strat_summary
    assert "target_counts" in strat_summary
    assert "actual_counts" in strat_summary
    assert "quota_fulfilled" in strat_summary

    # Verify bins match config
    assert strat_summary["bins"] == [0.2, 0.4, 0.6]

    # Verify actual counts are populated
    assert len(strat_summary["actual_counts"]) > 0

def test_manifest_schema_validation():
    """
    Verify that the schema validation function rejects invalid manifests.
    """
    # Valid manifest
    valid_manifest = {
        "global_batch_id": "test",
        "generation_algorithm": ["erdos_renyi"],
        "stratification_summary": {"bins": [], "target_counts": {}, "actual_counts": {}, "quota_fulfilled": True},
        "graphs": []
    }

    assert validate_manifest_schema(valid_manifest) is True

    # Invalid manifest (missing required key)
    invalid_manifest = {
        "global_batch_id": "test",
        # Missing: generation_algorithm, stratification_summary, graphs
    }

    assert validate_manifest_schema(invalid_manifest) is False

def test_manifest_writes_to_disk():
    """
    Verify that the manifest is written to the correct path.
    """
    # Create dummy batch results
    batch_results = [
        {"graph_id": "1", "clustering_coefficient": 0.1, "topology_type": "erdos_renyi"}
    ]
    config = {
        "stratification_params": {"bins": [0.2], "target_counts": {0.2: 1}, "tolerance": 0.0},
        "topology_targets": ["erdos_renyi"]
    }

    manifest = build_manifest(batch_results, config)

    # Write to temp path
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "test_manifest.json"
        from code.src.generators.manifest_writer import save_manifest
        save_manifest(manifest, tmp_path)

        # Verify file exists
        assert tmp_path.exists()

        # Verify content
        with open(tmp_path, "r") as f:
            loaded = json.load(f)

        assert loaded["global_batch_id"] == manifest["global_batch_id"]
        assert len(loaded["graphs"]) == 1

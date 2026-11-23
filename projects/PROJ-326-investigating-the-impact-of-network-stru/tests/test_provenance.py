"""
Tests for the provenance aggregation module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.src.analysis.provenance import (
    load_json_file,
    extract_seeds_from_run_log,
    extract_parameters_from_manifest,
    aggregate_provenance,
    save_provenance
)


class TestProvenanceModule:
    """Test cases for provenance aggregation functions."""

    def test_load_json_file_success(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        test_file = tmp_path / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        result = load_json_file(test_file)
        assert result == test_data

    def test_load_json_file_not_found(self):
        """Test loading a non-existent file."""
        result = load_json_file(Path("/nonexistent/file.json"))
        assert result is None

    def test_load_json_file_invalid(self, tmp_path):
        """Test loading an invalid JSON file."""
        test_file = tmp_path / "invalid.json"
        with open(test_file, 'w') as f:
            f.write("not valid json {{{")

        result = load_json_file(test_file)
        assert result is None

    def test_extract_seeds_from_run_log(self):
        """Test extracting seeds from a run log."""
        run_log = {
            "run_id": "test-run-123",
            "seeds": {
                "global": 42,
                "generator": 123,
                "simulation": 456
            },
            "verification_status": "PASS"
        }

        seeds = extract_seeds_from_run_log(run_log)

        assert len(seeds) == 1
        assert seeds[0]['run_id'] == "test-run-123"
        assert seeds[0]['seeds']['global'] == 42
        assert seeds[0]['verification_status'] == "PASS"

    def test_extract_seeds_empty(self):
        """Test extracting seeds from an empty run log."""
        run_log = {}
        seeds = extract_seeds_from_run_log(run_log)
        assert len(seeds) == 0

    def test_extract_parameters_from_manifest(self):
        """Test extracting parameters from a manifest."""
        manifest = {
            "total_generated": 10,
            "graph_details": [
                {
                    "graph_id": "graph_001",
                    "topology_class": "erdos_renyi",
                    "generation_algorithm": "ErdosRenyiGenerator",
                    "parameter_values": {"n": 100, "p": 0.05},
                    "seed": 42,
                    "status": "success"
                },
                {
                    "graph_id": "graph_002",
                    "topology_class": "watts_strogatz",
                    "generation_algorithm": "WattsStrogatzGenerator",
                    "parameter_values": {"n": 100, "k": 4, "p": 0.1},
                    "seed": 43,
                    "status": "success"
                }
            ]
        }

        params = extract_parameters_from_manifest(manifest)

        assert len(params) == 2
        assert params[0]['graph_id'] == "graph_001"
        assert params[0]['topology_class'] == "erdos_renyi"
        assert params[1]['graph_id'] == "graph_002"
        assert params[1]['parameter_values']['p'] == 0.1

    def test_extract_parameters_empty(self):
        """Test extracting parameters from an empty manifest."""
        manifest = {}
        params = extract_parameters_from_manifest(manifest)
        assert len(params) == 0

    def test_aggregate_provenance(self, tmp_path):
        """Test full provenance aggregation."""
        # Create test run log
        run_log = {
            "run_id": "test-run-001",
            "seeds": {"global": 100, "generator": 200, "simulation": 300},
            "verification_status": "PASS"
        }
        run_log_path = tmp_path / "run_log.json"
        with open(run_log_path, 'w') as f:
            json.dump(run_log, f)

        # Create test manifest
        manifest = {
            "total_generated": 5,
            "valid_count": 5,
            "success_rate": 1.0,
            "total_attempts": 5,
            "failed_graphs": [],
            "graph_details": [
                {
                    "graph_id": "g1",
                    "topology_class": "erdos_renyi",
                    "generation_algorithm": "ER",
                    "parameter_values": {"n": 50, "p": 0.1},
                    "seed": 100,
                    "status": "success"
                }
            ]
        }
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)

        # Aggregate
        provenance = aggregate_provenance(run_log_path, manifest_path)

        # Verify structure
        assert 'batch_summary' in provenance
        assert 'seed_history' in provenance
        assert 'parameter_history' in provenance
        assert 'fr_007_compliance' in provenance

        assert provenance['batch_summary']['total_generated'] == 5
        assert len(provenance['seed_history']) == 1
        assert len(provenance['parameter_history']) == 1
        assert provenance['fr_007_compliance']['status'] == 'PASS'

    def test_aggregate_provenance_missing_files(self, tmp_path):
        """Test aggregation with missing input files."""
        run_log_path = tmp_path / "missing_log.json"
        manifest_path = tmp_path / "missing_manifest.json"

        with pytest.raises(FileNotFoundError):
            aggregate_provenance(run_log_path, manifest_path)

    def test_save_provenance(self, tmp_path):
        """Test saving provenance to a file."""
        provenance = {
            "batch_summary": {"total_generated": 10},
            "seed_history": [{"run_id": "test"}],
            "parameter_history": [{"graph_id": "g1"}],
            "fr_007_compliance": {"status": "PASS"}
        }

        output_path = tmp_path / "provenance.json"
        save_provenance(provenance, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            saved = json.load(f)

        assert saved == provenance
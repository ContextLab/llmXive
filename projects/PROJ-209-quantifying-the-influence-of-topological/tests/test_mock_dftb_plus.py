"""
Tests for mock_dftb_plus module.
"""

import os
import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path for imports
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.generators.mock_dftb_plus import (
    compute_physical_value,
    simulate_dftb_computation,
    run_mock_dftb_analysis,
    save_results_to_csv,
    save_exclusions_to_json,
    load_defect_data_from_csv,
    ensure_output_directories,
    get_project_root
)


class TestComputePhysicalValue:
    """Tests for compute_physical_value function."""

    def test_graphene_defect(self):
        """Test computation for graphene defect."""
        value = compute_physical_value(0.1, "graphene_vacancy", 42)
        assert value > 0.1
        assert value < 10.0

    def test_mos2_defect(self):
        """Test computation for MoS2 defect."""
        value = compute_physical_value(0.1, "mos2_substitution", 42)
        assert value > 0.1
        assert value < 10.0

    def test_unknown_defect_type(self):
        """Test computation for unknown defect type."""
        value = compute_physical_value(0.1, "unknown_type", 42)
        assert value > 0.1
        assert value < 10.0

    def test_very_low_density(self):
        """Test computation with very low defect density."""
        value = compute_physical_value(1e-6, "graphene_vacancy", 42)
        assert value > 0.1
        assert value < 10.0

    def test_high_density(self):
        """Test computation with high defect density."""
        value = compute_physical_value(0.5, "graphene_vacancy", 42)
        assert value > 0.1
        assert value < 10.0

    def test_deterministic_output(self):
        """Test that output is deterministic with same seed."""
        value1 = compute_physical_value(0.1, "graphene_vacancy", 42)
        value2 = compute_physical_value(0.1, "graphene_vacancy", 42)
        assert value1 == value2


class TestSimulateDftbComputation:
    """Tests for simulate_dftb_computation function."""

    def test_successful_computation(self):
        """Test successful computation."""
        value, status = simulate_dftb_computation("test_id", 0.1, "graphene_vacancy", 300)
        assert status == "SUCCESS"
        assert value is not None
        assert value > 0.1

    def test_timeout_handling(self):
        """Test timeout handling (mocked)."""
        with patch('src.generators.mock_dftb_plus.time.sleep') as mock_sleep:
            mock_sleep.side_effect = Exception("Timeout simulation")
            value, status = simulate_dftb_computation("test_id", 0.1, "graphene_vacancy", 0.001)
            assert status == "TIMEOUT"
            assert value is None


class TestRunMockDftbAnalysis:
    """Tests for run_mock_dftb_analysis function."""

    def test_basic_analysis(self):
        """Test basic analysis with valid defect data."""
        defect_ids = ["defect_1", "defect_2"]
        defect_data = {
            "defect_1": {"defect_density": 0.1, "defect_type": "graphene_vacancy", "fracture_energy": None},
            "defect_2": {"defect_density": 0.2, "defect_type": "mos2_substitution", "fracture_energy": None}
        }
        
        results, exclusions = run_mock_dftb_analysis(defect_ids, defect_data)
        
        assert len(results) == 2
        assert all(r['status'] in ['SUCCESS', 'TIMEOUT'] for r in results)
        assert 'excluded_ids' in exclusions
        assert 'count' in exclusions

    def test_empty_defect_ids(self):
        """Test analysis with empty defect IDs list."""
        results, exclusions = run_mock_dftb_analysis([], {})
        assert len(results) == 0
        assert exclusions['count'] == 0

    def test_missing_defect_in_data(self):
        """Test analysis with defect ID not in defect data."""
        defect_ids = ["defect_1", "defect_2"]
        defect_data = {
            "defect_1": {"defect_density": 0.1, "defect_type": "graphene_vacancy", "fracture_energy": None}
        }
        
        results, exclusions = run_mock_dftb_analysis(defect_ids, defect_data)
        
        assert len(results) == 1  # Only defect_1 should be processed
        assert results[0]['defect_id'] == "defect_1"


class TestSaveResultsToCsv:
    """Tests for save_results_to_csv function."""

    def test_save_results(self):
        """Test saving results to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "results.csv")
            results = [
                {"defect_id": "defect_1", "computed_value": 5.5, "status": "SUCCESS"},
                {"defect_id": "defect_2", "computed_value": None, "status": "TIMEOUT"}
            ]
            
            save_results_to_csv(results, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2
            assert rows[0]['defect_id'] == "defect_1"
            assert rows[0]['status'] == "SUCCESS"
            assert rows[1]['defect_id'] == "defect_2"
            assert rows[1]['status'] == "TIMEOUT"


class TestSaveExclusionsToJson:
    """Tests for save_exclusions_to_json function."""

    def test_save_exclusions(self):
        """Test saving exclusions to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "exclusions.json")
            exclusions = {
                "excluded_ids": ["defect_2", "defect_3"],
                "count": 2
            }
            
            save_exclusions_to_json(exclusions, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
                
            assert data['count'] == 2
            assert len(data['excluded_ids']) == 2


class TestLoadDefectDataFromCsv:
    """Tests for load_defect_data_from_csv function."""

    def test_load_valid_csv(self):
        """Test loading valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "defects.csv")
            
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['defect_id', 'defect_density', 'defect_type', 'fracture_energy'])
                writer.writeheader()
                writer.writerow({
                    'defect_id': 'defect_1',
                    'defect_density': '0.1',
                    'defect_type': 'graphene_vacancy',
                    'fracture_energy': ''
                })
                writer.writerow({
                    'defect_id': 'defect_2',
                    'defect_density': '0.2',
                    'defect_type': 'mos2_substitution',
                    'fracture_energy': '5.5'
                })
            
            defect_data = load_defect_data_from_csv(csv_path)
            
            assert 'defect_1' in defect_data
            assert defect_data['defect_1']['defect_density'] == 0.1
            assert defect_data['defect_1']['fracture_energy'] is None
            
            assert 'defect_2' in defect_data
            assert defect_data['defect_2']['defect_density'] == 0.2
            assert defect_data['defect_2']['fracture_energy'] == '5.5'

    def test_missing_file(self):
        """Test loading non-existent CSV file."""
        defect_data = load_defect_data_from_csv("non_existent_file.csv")
        assert defect_data == {}


class TestEnsureOutputDirectories:
    """Tests for ensure_output_directories function."""

    def test_create_directories(self):
        """Test that output directories are created."""
        with patch('src.generators.mock_dftb_plus.get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)
                ensure_output_directories()
                
                assert os.path.exists(os.path.join(tmpdir, "data", "processed"))
                assert os.path.exists(os.path.join(tmpdir, "data", "state"))
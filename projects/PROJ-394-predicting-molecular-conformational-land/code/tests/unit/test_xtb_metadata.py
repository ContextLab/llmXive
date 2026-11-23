"""
Unit tests for xtb metadata capture module.

Tests Constitution Principle VI implementation:
- Metadata capture and versioning
- JSON serialization
- File archiving
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from data.xtb_metadata import XtbMetadata, get_xtb_version, archive_calculation


class TestXtbMetadata:
    """Tests for XtbMetadata class."""

    def test_init_with_defaults(self):
        """Test initialization with minimal parameters."""
        meta = XtbMetadata(smiles="CCO")
        assert meta.smiles == "CCO"
        assert meta.calculation_id is not None
        assert meta.command_args == []
        assert meta.convergence_criteria == {}
        assert meta.timestamp is not None

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        meta = XtbMetadata(
            smiles="c1ccccc1",
            calculation_id="test-123",
            command_args=["--gfn", "2", "--acc", "1e-6"],
            convergence_criteria={"max_iter": 200, "energy_threshold": 1e-6},
            input_file="input.xyz",
            output_file="output.txt",
            energy=-100.5,
            gradient_norm=1e-5,
            converged=True,
            iterations=45,
            wall_time=12.3,
        )
        assert meta.smiles == "c1ccccc1"
        assert meta.calculation_id == "test-123"
        assert meta.command_args == ["--gfn", "2", "--acc", "1e-6"]
        assert meta.convergence_criteria["max_iter"] == 200
        assert meta.energy == -100.5
        assert meta.converged is True

    def test_to_dict_structure(self):
        """Test that to_dict produces expected structure."""
        meta = XtbMetadata(
            smiles="CCO",
            command_args=["--gfn", "2"],
            convergence_criteria={"energy_threshold": 1e-6},
        )
        d = meta.to_dict()

        assert "calculation_id" in d
        assert "smiles" in d
        assert "timestamp" in d
        assert "xtb_version" in d
        assert "command_line" in d
        assert "command_args" in d
        assert "convergence_criteria" in d
        assert "input_file" in d
        assert "output_file" in d
        assert "results" in d
        assert "config_snapshot" in d

        assert d["smiles"] == "CCO"
        assert d["command_line"][0] == "xtb"
        assert d["command_line"][1:] == ["--gfn", "2"]

    def test_save_creates_json(self):
        """Test that save() creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = XtbMetadata(
                smiles="CCO",
                calculation_id="save-test",
            )
            filepath = meta.save(output_dir=Path(tmpdir))

            assert filepath.exists()
            assert filepath.suffix == ".json"

            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["smiles"] == "CCO"
            assert data["calculation_id"] == "save-test"

    def test_save_creates_directory(self):
        """Test that save() creates the output directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "metadata"
            meta = XtbMetadata(smiles="CCO")
            filepath = meta.save(output_dir=output_dir)

            assert output_dir.exists()
            assert filepath.exists()

    def test_capture_xtb_version_mocks(self):
        """Test version capture with mocked subprocess."""
        with patch("data.xtb_metadata.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="xtb version 2.7.1\n", stderr="")
            meta = XtbMetadata(smiles="CCO")
            version = meta.capture_xtb_version()
            assert version == "xtb version 2.7.1"

    def test_capture_xtb_version_not_found(self):
        """Test version capture when xtb is not found."""
        with patch("data.xtb_metadata.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("xtb not found")
            meta = XtbMetadata(smiles="CCO")
            with pytest.raises(RuntimeError, match="xtb executable not found"):
                meta.capture_xtb_version()


class TestGetXtbVersion:
    """Tests for get_xtb_version utility function."""

    def test_get_version_mocked(self):
        """Test get_xtb_version with mocked subprocess."""
        with patch("data.xtb_metadata.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="xtb version 2.7.1\n", stderr="")
            version = get_xtb_version()
            assert version == "xtb version 2.7.1"

    def test_get_version_not_found(self):
        """Test get_xtb_version when xtb is not found."""
        with patch("data.xtb_metadata.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("xtb not found")
            with pytest.raises(RuntimeError, match="xtb executable not found"):
                get_xtb_version()


class TestArchiveCalculation:
    """Tests for archive_calculation convenience function."""

    def test_archive_full_calculation(self):
        """Test archiving a complete calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = archive_calculation(
                smiles="c1ccccc1",
                command_args=["--gfn", "2", "--acc", "1e-6"],
                convergence_criteria={"max_iter": 200},
                input_file="benzene.xyz",
                output_file="benzene.out",
                energy=-234.56,
                gradient_norm=1e-6,
                converged=True,
                iterations=32,
                wall_time=5.5,
                calculation_id="benzene-001",
            )

            assert filepath.exists()
            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["smiles"] == "c1ccccc1"
            assert data["results"]["energy"] == -234.56
            assert data["results"]["converged"] is True
            assert data["calculation_id"] == "benzene-001"

    def test_archive_minimal_calculation(self):
        """Test archiving with minimal required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = archive_calculation(
                smiles="CCO",
                command_args=[],
                convergence_criteria={},
                input_file="ethanol.xyz",
                output_file="ethanol.out",
            )

            assert filepath.exists()
            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["smiles"] == "CCO"
            assert data["results"]["energy"] is None
            assert data["results"]["converged"] is None
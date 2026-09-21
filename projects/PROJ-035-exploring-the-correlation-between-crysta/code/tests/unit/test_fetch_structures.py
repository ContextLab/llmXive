"""
Unit tests for fetch_structures module (T013).

Tests cover:
- API key loading
- Backoff logic
- Perovskite stoichiometry filtering
- Structure fetching and CSV output
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingest.fetch_structures import (
    load_api_key,
    fetch_with_backoff,
    is_perovskite,
    fetch_perovskite_structures,
    main
)
from pymatgen.core import Structure, Lattice


class TestLoadApiKey:
    """Tests for load_api_key function."""

    def test_load_api_key_success(self, monkeypatch):
        """Test successful API key loading."""
        monkeypatch.setenv("MP_API_KEY", "test_key_123")
        api_key = load_api_key()
        assert api_key == "test_key_123"

    def test_load_api_key_missing(self, monkeypatch, caplog):
        """Test API key loading when not set."""
        monkeypatch.delenv("MP_API_KEY", raising=False)
        with pytest.raises(SystemExit):
            load_api_key()


class TestFetchWithBackoff:
    """Tests for fetch_with_backoff function."""

    @patch('src.ingest.fetch_structures.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful fetch on first attempt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": 1}]}
        mock_get.return_value = mock_response

        result = fetch_with_backoff(
            "http://test.com",
            {},
            {"X-API-Key": "test"}
        )
        assert result == {"data": [{"id": 1}]}
        mock_get.assert_called_once()

    @patch('src.ingest.fetch_structures.requests.get')
    def test_rate_limit_retry(self, mock_get, monkeypatch):
        """Test retry behavior on rate limit (429)."""
        monkeypatch.setattr(np.random, 'uniform', lambda a, b: 1.0)  # Deterministic jitter

        # First call: 429, second call: 200
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": [{"id": 2}]}

        mock_get.side_effect = [mock_response_429, mock_response_200]

        result = fetch_with_backoff(
            "http://test.com",
            {},
            {"X-API-Key": "test"},
            max_retries=3,
            seed=42
        )

        assert result == {"data": [{"id": 2}]}
        assert mock_get.call_count == 2

    @patch('src.ingest.fetch_structures.requests.get')
    def test_auth_failure(self, mock_get):
        """Test immediate failure on 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with pytest.raises(SystemExit):
            fetch_with_backoff(
                "http://test.com",
                {},
                {"X-API-Key": "invalid"}
            )


class TestIsPerovskite:
    """Tests for is_perovskite stoichiometry check."""

    def test_valid_perovskite_abo3(self):
        """Test detection of valid ABO3 perovskite."""
        # Create a simple cubic perovskite: CaTiO3
        # A=Ca (1), B=Ti (1), X=O (3) -> fractions: 0.2, 0.2, 0.6
        lattice = Lattice.cubic(3.8)
        coords = [
            [0, 0, 0],      # Ca (A)
            [0.5, 0.5, 0.5], # Ti (B)
            [0.5, 0.5, 0],   # O (X)
            [0.5, 0, 0.5],   # O (X)
            [0, 0.5, 0.5],   # O (X)
        ]
        species = ["Ca", "Ti", "O", "O", "O"]
        structure = Structure(lattice, species, coords)

        assert is_perovskite(structure) is True

    def test_invalid_stoichiometry(self):
        """Test rejection of non-ABX3 stoichiometry."""
        # SiO2 - not perovskite
        lattice = Lattice.cubic(5.0)
        coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
        species = ["Si", "O"]
        structure = Structure(lattice, species, coords)

        assert is_perovskite(structure) is False

    def test_two_element_structure(self):
        """Test rejection of two-element structure."""
        # NaCl
        lattice = Lattice.cubic(5.6)
        coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
        species = ["Na", "Cl"]
        structure = Structure(lattice, species, coords)

        assert is_perovskite(structure) is False

    def test_four_element_structure(self):
        """Test rejection of four-element structure."""
        # Complex oxide with 4 elements
        lattice = Lattice.cubic(4.0)
        coords = [[0, 0, 0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25], [0.75, 0.75, 0.75]]
        species = ["La", "Ba", "Mn", "O"]
        structure = Structure(lattice, species, coords)

        assert is_perovskite(structure) is False


class TestFetchPerovskiteStructures:
    """Tests for fetch_perovskite_structures function."""

    @patch('src.ingest.fetch_structures.fetch_with_backoff')
    @patch('src.ingest.fetch_structures.Structure.from_dict')
    def test_fetch_creates_csv(self, mock_structure_from_dict, mock_fetch, tmp_path):
        """Test that fetching creates CSV with correct structure."""
        output_path = tmp_path / "test_structures.csv"

        # Mock API response
        mock_fetch.return_value = {
            "data": [
                {
                    "material_id": "mp-123",
                    "formula_pretty": "CaTiO3",
                    "nsites": 5,
                    "nelements": 3,
                    "structure": {
                        "lattice": {
                            "a": 3.8, "b": 3.8, "c": 3.8,
                            "alpha": 90, "beta": 90, "gamma": 90
                        },
                        "species": [{"element": "Ca"}, {"element": "Ti"}, {"element": "O"}, {"element": "O"}, {"element": "O"}],
                        "coords": [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]]
                    }
                }
            ],
            "next_cursor": None
        }

        # Mock Structure parsing
        mock_structure = MagicMock()
        mock_structure.computation.elements = [MagicMock(symbol="Ca"), MagicMock(symbol="Ti"), MagicMock(symbol="O")]
        mock_structure.composition = MagicMock()
        mock_structure.composition.elements = [MagicMock(symbol="Ca"), MagicMock(symbol="Ti"), MagicMock(symbol="O")]
        mock_structure.composition.items.return_value = [(MagicMock(symbol="Ca"), 0.2), (MagicMock(symbol="Ti"), 0.2), (MagicMock(symbol="O"), 0.6)]
        mock_structure.lattice.a = 3.8
        mock_structure.lattice.b = 3.8
        mock_structure.lattice.c = 3.8
        mock_structure.lattice.alpha = 90
        mock_structure.lattice.beta = 90
        mock_structure.lattice.gamma = 90
        mock_structure.volume = 54.872
        mock_structure.density = 4.0
        mock_structure_from_dict.return_value = mock_structure

        # Mock is_perovskite to return True
        with patch('src.ingest.fetch_structures.is_perovskite', return_value=True):
            total, perovskite_count = fetch_perovskite_structures(
                api_key="test_key",
                output_path=output_path,
                seed=42
            )

        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert "structure_id" in df.columns
        assert "formula_pretty" in df.columns
        assert "is_perovskite" in df.columns


class TestMain:
    """Tests for main function."""

    @patch('src.ingest.fetch_structures.fetch_perovskite_structures')
    @patch('src.ingest.fetch_structures.load_api_key')
    @patch('src.ingest.fetch_structures.init_seed')
    def test_main_execution(self, mock_init_seed, mock_load_key, mock_fetch, tmp_path, monkeypatch):
        """Test main function execution."""
        monkeypatch.setenv("MP_API_KEY", "test_key")
        mock_load_key.return_value = "test_key"
        mock_fetch.return_value = (100, 50)

        # Create output path
        output_path = tmp_path / "structures.csv"

        # Mock sys.argv
        test_args = ['fetch_structures.py', '--output', str(output_path), '--seed', '42']
        monkeypatch.setattr(sys, 'argv', test_args)

        # Mock Path to use tmp_path
        with patch('src.ingest.fetch_structures.OUTPUT_PATH', output_path):
            main()

        assert output_path.exists()
        mock_fetch.assert_called_once()
        mock_init_seed.assert_called_once_with(42)
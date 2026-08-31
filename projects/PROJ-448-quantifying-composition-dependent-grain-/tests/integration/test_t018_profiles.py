"""
Integration test for T018: Segregation Profile Generation.

Verifies that:
1. The script runs without errors
2. Output file is created and valid JSON
3. Profiles contain expected fields
4. Metadata is present and accurate
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import DATA_PROCESSED_PATH, DATA_RAW_PATH
from code.models.mclean import McLeanResult

class TestT018Integration:
    """Integration tests for segregation profile generation."""

    @pytest.fixture
    def mock_equilibrium_data(self, tmp_path):
        """Create mock equilibrium composition data."""
        csv_path = tmp_path / "equilibrium_compositions.csv"
        data = {
            "system": ["Fe-Cr-Mo", "Fe-Cr-Mo", "Fe-Cr-V", "Fe-Mo-W"],
            "temperature": [600, 700, 600, 650],
            "Cr": [0.1, 0.15, 0.2, 0.0],
            "Mo": [0.05, 0.05, 0.0, 0.1],
            "V": [0.0, 0.0, 0.1, 0.0],
            "W": [0.0, 0.0, 0.0, 0.05]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def mock_dft_data(self, tmp_path):
        """Create mock DFT energy data."""
        json_path = tmp_path / "dft_energies.json"
        data = {
            "Fe-Cr": [
                {"temperature": 600, "energy_eV": 0.15},
                {"temperature": 700, "energy_eV": 0.12}
            ],
            "Fe-Mo": [
                {"temperature": 600, "energy_eV": 0.25},
                {"temperature": 650, "energy_eV": 0.22},
                {"temperature": 700, "energy_eV": 0.20}
            ],
            "Fe-V": [
                {"temperature": 600, "energy_eV": 0.18}
            ],
            "Fe-W": [
                {"temperature": 650, "energy_eV": 0.30}
            ],
            "Cr-Mo": [
                {"temperature": 600, "energy_eV": 0.05}
            ]
        }
        with open(json_path, "w") as f:
            json.dump(data, f)
        return json_path

    @patch("code.config.DATA_PROCESSED_PATH")
    @patch("code.config.DATA_RAW_PATH")
    def test_profile_generation(
        self, 
        mock_raw_path, 
        mock_processed_path, 
        mock_equilibrium_data,
        mock_dft_data,
        tmp_path
    ):
        """Test that T018 generates valid segregation profiles."""
        # Setup mock paths
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        mock_processed_path.__truediv__ = lambda self, x: processed_dir / x
        mock_raw_path.__truediv__ = lambda self, x: raw_dir / x
        mock_processed_path.__fspath__ = lambda self: str(processed_dir)
        mock_raw_path.__fspath__ = lambda self: str(raw_dir)

        # Copy mock data to expected locations
        import shutil
        shutil.copy(mock_equilibrium_data, processed_dir / "equilibrium_compositions.csv")
        shutil.copy(mock_dft_data, raw_dir / "dft_energies.json")

        # Import and run the script
        from code.scripts.generate_segregation_profiles import main

        # Run the script
        main()

        # Verify output file exists
        output_path = processed_dir / "segregation_profiles.json"
        assert output_path.exists(), "Output file not created"

        # Verify JSON structure
        with open(output_path) as f:
            result = json.load(f)

        assert "metadata" in result
        assert "profiles" in result
        assert len(result["profiles"]) > 0

        # Verify profile structure
        for profile in result["profiles"]:
            assert "system" in profile
            assert "temperature_K" in profile
            assert "bulk_composition" in profile
            assert "segregation_profiles" in profile
            
            for seg in profile["segregation_profiles"]:
                assert "element" in seg
                assert "bulk_concentration" in seg
                assert "segregation_energy_eV" in seg
                assert "equilibrium_concentration" in seg
                assert "saturation_flag" in seg

    def test_empty_ternary_data(self, tmp_path, caplog):
        """Test handling of missing ternary data."""
        # Create empty equilibrium file
        csv_path = tmp_path / "equilibrium_compositions.csv"
        pd.DataFrame(columns=["system", "temperature", "Cr", "Mo", "V", "W"]).to_csv(csv_path, index=False)

        # Create empty DFT file
        json_path = tmp_path / "dft_energies.json"
        with open(json_path, "w") as f:
            json.dump({}, f)

        # Setup paths
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        shutil = __import__("shutil")
        shutil.copy(csv_path, processed_dir / "equilibrium_compositions.csv")
        shutil.copy(json_path, raw_dir / "dft_energies.json")

        # Mock paths
        with patch("code.config.DATA_PROCESSED_PATH") as mock_processed, \
             patch("code.config.DATA_RAW_PATH") as mock_raw:
            
            mock_processed.__truediv__ = lambda self, x: processed_dir / x
            mock_raw.__truediv__ = lambda self, x: raw_dir / x
            mock_processed.__fspath__ = lambda self: str(processed_dir)
            mock_raw.__fspath__ = lambda self: str(raw_dir)

            from code.scripts.generate_segregation_profiles import main
            main()

            # Verify empty result with metadata
            output_path = processed_dir / "segregation_profiles.json"
            with open(output_path) as f:
                result = json.load(f)
            
            assert result["metadata"]["total_records"] == 0
            assert "No ternary equilibrium data available" in result["metadata"]["note"]

    def test_missing_input_files(self, tmp_path, caplog):
        """Test error handling for missing input files."""
        # Setup empty paths
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        
        with patch("code.config.DATA_PROCESSED_PATH") as mock_processed:
            mock_processed.__truediv__ = lambda self, x: processed_dir / x
            mock_processed.__fspath__ = lambda self: str(processed_dir)

            from code.scripts.generate_segregation_profiles import main
            
            # Should raise FileNotFoundError
            with pytest.raises(SystemExit):
                main()
            
            assert "Missing required input file" in caplog.text
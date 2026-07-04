"""
Integration test for T020: Retrieval Output Generation.
Verifies that retrieval results are correctly saved to CSV.
"""
import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from retrieval_output import process_retrieval_results, main
from data_models import RetrievalResult, CensorshipStatus, PlanetCategory
from config import get_config

class TestRetrievalOutput:
    """Tests for T020 output generation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup temporary directories and teardown after tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock config
        self.original_config = None
        try:
            import config
            self.original_config = config.get_config()
            config.get_config = lambda: {
                'data_dir': str(self.data_dir),
                'cpu_threads': 1,
                'random_seed': 42
            }
        except Exception:
            pass

        yield

        # Cleanup
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Restore config
        if self.original_config:
            import config
            config.get_config = lambda: self.original_config

    def test_process_retrieval_results_writes_csv(self):
        """Test that process_retrieval_results writes a valid CSV file."""
        results = [
            RetrievalResult(
                planet_name="WASP-12b",
                equilibrium_temperature=2500.0,
                metallicity=0.5,
                spectral_resolution=1000,
                snr=50.0,
                category=PlanetCategory.HOT_JUPITER,
                log10_water_mixing_ratio=-4.5,
                uncertainty_1sigma=0.2,
                is_censored=False,
                censorship_status=CensorshipStatus.UNDETERMINED,
                convergence_status="SUCCESS",
                retrieval_error=""
            ),
            RetrievalResult(
                planet_name="K2-18b",
                equilibrium_temperature=300.0,
                metallicity=0.0,
                spectral_resolution=500,
                snr=10.0,
                category=PlanetCategory.SUPER_EARTH,
                log10_water_mixing_ratio=None,
                uncertainty_1sigma=0.5,
                is_censored=True,
                censorship_status=CensorshipStatus.UPPER_LIMIT,
                convergence_status="CENSORED",
                retrieval_error=""
            )
        ]

        output_path = self.processed_dir / "retrieval_results.csv"
        process_retrieval_results(results, output_path)

        assert output_path.exists(), "Output CSV file was not created."

        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 2, "Expected 2 rows in CSV."
        assert "planet_name" in df.columns, "Missing 'planet_name' column."
        assert "log10_water_mixing_ratio" in df.columns, "Missing 'log10_water_mixing_ratio' column."
        assert "is_censored" in df.columns, "Missing 'is_censored' column."

        # Check specific values
        assert df.iloc[0]['planet_name'] == "WASP-12b"
        assert df.iloc[0]['log10_water_mixing_ratio'] == -4.5
        assert df.iloc[0]['is_censored'] == False
        
        assert df.iloc[1]['planet_name'] == "K2-18b"
        # NaN handling in CSV usually results in empty string or NaN, check logic
        assert df.iloc[1]['is_censored'] == True
        assert df.iloc[1]['censorship_status'] == "UPPER_LIMIT"

    def test_csv_schema_matches_requirements(self):
        """Test that the CSV schema includes all required fields for downstream analysis."""
        results = [
            RetrievalResult(
                planet_name="TestPlanet",
                equilibrium_temperature=1000.0,
                metallicity=0.1,
                spectral_resolution=100,
                snr=20.0,
                category=PlanetCategory.HOT_JUPITER,
                log10_water_mixing_ratio=-5.0,
                uncertainty_1sigma=0.1,
                is_censored=False,
                censorship_status=CensorshipStatus.UNDETERMINED,
                convergence_status="SUCCESS",
                retrieval_error=""
            )
        ]
        output_path = self.processed_dir / "schema_test.csv"
        process_retrieval_results(results, output_path)

        required_columns = [
            'planet_name', 'equilibrium_temperature', 'metallicity', 
            'spectral_resolution', 'snr', 'category',
            'log10_water_mixing_ratio', 'uncertainty_1sigma', 
            'is_censored', 'censorship_status', 'convergence_status'
        ]

        df = pd.read_csv(output_path)
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
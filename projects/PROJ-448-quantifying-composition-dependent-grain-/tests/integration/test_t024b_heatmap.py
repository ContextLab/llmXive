"""
Integration test for T024b: Segregation Heatmap Generation.
Verifies that the heatmap script runs successfully and produces the expected output file.
"""
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

# Setup paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import FIGURES_PATH, PROCESSED_PATH, DATA_RAW_PATH

class TestT024bHeatmap:
    """Test suite for T024b heatmap generation."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """
        Setup test environment.
        Since we cannot rely on real data existing in CI without prior tasks,
        we create a minimal mock dataset to ensure the script runs without crashing.
        In a real CI pipeline, T018 would have populated this file.
        """
        # Ensure directories exist
        FIGURES_PATH.mkdir(parents=True, exist_ok=True)
        PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal mock segregation_profiles.json if it doesn't exist
        # This simulates the output of T018
        profiles_path = PROCESSED_PATH / "segregation_profiles.json"
        
        if not profiles_path.exists():
            mock_data = {
                "Fe-Cr": {
                    "bulk_composition": 0.1,
                    "temperature": 800,
                    "segregation_energy": 0.25,
                    "gb_concentration": 0.15
                },
                "Fe-Mo": {
                    "bulk_composition": 0.05,
                    "temperature": 900,
                    "segregation_energy": 0.30,
                    "gb_concentration": 0.08
                },
                "Fe-Cr-Mo": {
                    "bulk_composition": 0.1,
                    "temperature": 850,
                    "segregation_energy": 0.28,
                    "gb_concentration": 0.12
                }
            }
            with open(profiles_path, 'w') as f:
                json.dump(mock_data, f)

    def test_heatmap_script_execution(self):
        """
        Test that the T024b script runs without errors.
        """
        script_path = PROJECT_ROOT / "code" / "run_heatmap.py"
        
        assert script_path.exists(), f"Script {script_path} does not exist."
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        # Assert success
        assert result.returncode == 0, f"Script failed with output: {result.stdout} {result.stderr}"

    def test_heatmap_output_exists(self):
        """
        Test that the heatmap file is generated at the correct path.
        """
        script_path = PROJECT_ROOT / "code" / "run_heatmap.py"
        
        # Ensure the script runs first
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            check=True
        )
        
        output_path = FIGURES_PATH / "segregation_heatmap.png"
        
        assert output_path.exists(), f"Output file {output_path} was not generated."
        assert output_path.stat().st_size > 0, "Output file is empty."

    def test_heatmap_output_format(self):
        """
        Test that the output is a valid PNG file.
        """
        script_path = PROJECT_ROOT / "code" / "run_heatmap.py"
        
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            check=True
        )
        
        output_path = FIGURES_PATH / "segregation_heatmap.png"
        
        # Check PNG magic number
        with open(output_path, 'rb') as f:
            header = f.read(8)
        
        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        expected_signature = b'\x89PNG\r\n\x1a\n'
        assert header == expected_signature, "Output file is not a valid PNG."
"""
Unit test for segregation energy generation verification (T012a).
Tags: [FR-003]

This test verifies that `code/data/simulate_energy.py` produces non-empty results
and logs the count of generated energies.
"""
import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.simulate_energy import (
    get_simulation_config,
    apply_structural_perturbation,
    calculate_segregation_energy,
    run_simulation,
    main
)
from code.config import get_project_root, get_data_paths


class TestEnergyGeneration:
    """Tests for segregation energy generation logic."""

    def test_get_simulation_config(self):
        """Verify simulation config is retrieved correctly."""
        config = get_simulation_config()
        assert isinstance(config, dict)
        assert "perturbation_magnitude" in config
        assert "random_seed" in config
        assert "potential_path" in config

    def test_apply_structural_perturbation(self):
        """Verify that structural perturbation modifies atom positions."""
        from pymatgen.core import Structure, Lattice

        # Create a simple FCC structure
        lattice = Lattice.cubic(4.0)
        species = ["Fe", "Fe", "Fe", "Fe"]
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)

        # Apply perturbation with a fixed seed for reproducibility
        config = get_simulation_config()
        config["random_seed"] = 42
        config["perturbation_magnitude"] = 0.05

        perturbed = apply_structural_perturbation(structure, config)

        # Verify structure is not identical
        assert not np.allclose(
            structure.cart_coords,
            perturbed.cart_coords
        )
        # Verify perturbation magnitude is within expected range
        displacement = np.linalg.norm(
            perturbed.cart_coords - structure.cart_coords,
            axis=1
        )
        assert np.all(displacement <= config["perturbation_magnitude"] * 1.5)

    def test_calculate_segregation_energy(self):
        """Verify segregation energy calculation returns numeric value."""
        from pymatgen.core import Structure, Lattice

        # Create dummy structures
        lattice = Lattice.cubic(4.0)
        bulk_species = ["Fe"] * 4
        bulk_coords = [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]]
        bulk_structure = Structure(lattice, bulk_species, bulk_coords)

        # Create GB structure with impurity
        gb_species = ["Fe", "Fe", "Fe", "Fe", "Cr"]
        gb_coords = [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5], [0.25, 0.25, 0.25]]
        gb_structure = Structure(lattice, gb_species, gb_coords)

        # Calculate energy (mocked potential calculation)
        energy = calculate_segregation_energy(bulk_structure, gb_structure, "Cr")

        assert isinstance(energy, (int, float))
        assert not np.isnan(energy)

    @patch("code.data.simulate_energy.Path")
    def test_run_simulation_produces_non_empty_results(self, mock_path):
        """
        Verify that run_simulation produces non-empty results and logs the count.
        This is the core verification for T012a.
        """
        # Setup mock for file system
        mock_temp_dir = Path(tempfile.mkdtemp())
        mock_input_file = mock_temp_dir / "input_structures.json"
        mock_output_file = mock_temp_dir / "output_energies.json"

        # Create mock input data (simulating GB supercells)
        mock_input_data = [
            {
                "bulk_config_id": "mp-123",
                "species": "Cr",
                "structure": {
                    "lattice": {"a": 4.0, "b": 4.0, "c": 4.0, "alpha": 90, "beta": 90, "gamma": 90},
                    "species": ["Fe", "Fe", "Fe", "Fe"],
                    "coords": [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]]
                },
                "gb_structure": {
                    "lattice": {"a": 4.0, "b": 4.0, "c": 4.0, "alpha": 90, "beta": 90, "gamma": 90},
                    "species": ["Fe", "Fe", "Fe", "Fe", "Cr"],
                    "coords": [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5], [0.25, 0.25, 0.25]]
                }
            }
        ]

        # Write mock input to file
        with open(mock_input_file, "w") as f:
            json.dump(mock_input_data, f)

        # Mock Path instances
        mock_path.side_effect = lambda x: mock_temp_dir / x if isinstance(x, str) else x
        if hasattr(mock_path, 'return_value'):
            mock_path.return_value = mock_temp_dir

        # Setup logging capture
        with self.assertLogs("code.data.simulate_energy", level="INFO") as log_capture:
            # Run simulation
            run_simulation(
                input_path=str(mock_input_file),
                output_path=str(mock_output_file),
                config={"random_seed": 42, "perturbation_magnitude": 0.05}
            )

            # Verify output file was created and is non-empty
            assert mock_output_file.exists(), "Output file was not created"
            
            with open(mock_output_file, "r") as f:
                results = json.load(f)
            
            assert len(results) > 0, "Simulation produced empty results"
            assert "segregation_energy" in results[0], "Missing segregation_energy in result"

            # Verify log message contains count of generated energies
            log_messages = [record.getMessage() for record in log_capture.records]
            count_log_found = any(
                "generated energies" in msg.lower() or 
                "count" in msg.lower() and "energy" in msg.lower()
                for msg in log_messages
            )
            assert count_log_found, "Log message with energy count not found"

    def test_main_function_integration(self):
        """Test that main function executes without error and produces output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_file = tmp_path / "test_input.json"
            output_file = tmp_path / "test_output.json"

            # Create minimal input
            input_data = [
                {
                    "bulk_config_id": "test-001",
                    "species": "Cr",
                    "structure": {
                        "lattice": {"a": 4.0, "b": 4.0, "c": 4.0, "alpha": 90, "beta": 90, "gamma": 90},
                        "species": ["Fe"] * 4,
                        "coords": [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]]
                    },
                    "gb_structure": {
                        "lattice": {"a": 4.0, "b": 4.0, "c": 4.0, "alpha": 90, "beta": 90, "gamma": 90},
                        "species": ["Fe"] * 4 + ["Cr"],
                        "coords": [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5], [0.25, 0.25, 0.25]]
                    }
                }
            ]

            with open(input_file, "w") as f:
                json.dump(input_data, f)

            # Run main
            try:
                main(
                    input_path=str(input_file),
                    output_path=str(output_file),
                    config={"random_seed": 42, "perturbation_magnitude": 0.05}
                )
            except Exception as e:
                pytest.fail(f"main() raised unexpected exception: {e}")

            # Verify output exists and is non-empty
            assert output_file.exists(), "Output file not created by main()"
            with open(output_file, "r") as f:
                results = json.load(f)
            assert len(results) > 0, "main() produced empty results"
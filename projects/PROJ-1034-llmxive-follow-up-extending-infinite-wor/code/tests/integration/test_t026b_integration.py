import pytest
import os
import tempfile
import json
import yaml
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.cli.run_simulation import run_simulation_with_fallback, load_target_steps_from_config

class TestT026bIntegration:
    """
    Integration tests for T026b: Full pipeline with config loading and metric recording.
    """

    def test_run_simulation_reads_config_and_records_metrics(self):
        """
        Test that the simulation reads target_steps from config and records metrics to data/processed/.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file
            config_path = os.path.join(tmpdir, "config.yaml")
            with open(config_path, 'w') as f:
                yaml.dump({"target_steps": 100}, f)

            # Create output directory
            output_base = os.path.join(tmpdir, "data")
            os.makedirs(os.path.join(output_base, "raw"))
            os.makedirs(os.path.join(output_base, "processed"))

            # Mock the simulation to avoid actual heavy computation
            with patch('src.cli.run_simulation.run_eco_simulation') as mock_sim:
                mock_sim.return_value = {
                    'steps_completed': 100,
                    'metrics': [{'step': 1, 'coherence': 0.9, 'diversity': 0.8}]
                }

                result = run_simulation_with_fallback(
                    agent_type="ca_eco_director",
                    target_steps=100,
                    seed=42,
                    config_path=config_path,
                    output_base=output_base
                )

                # Verify result
                assert result["status"] == "completed"
                assert result["actual_steps"] == 100
                assert result["reached_target"] is True

                # Verify metrics file was written to data/processed/
                expected_processed_path = os.path.join(output_base, "processed", "metrics_ca_eco_director_42.json")
                assert os.path.exists(expected_processed_path), f"Metrics file not found at {expected_processed_path}"

                with open(expected_processed_path, 'r') as f:
                    metrics_data = json.load(f)

                assert metrics_data["steps"] == 100
                assert metrics_data["reached_target"] is True
                assert "metrics" in metrics_data

    def test_fallback_dataset_generation(self):
        """
        Test that fallback dataset is generated when real data is unavailable.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            with open(config_path, 'w') as f:
                yaml.dump({"target_steps": 50}, f)

            output_base = os.path.join(tmpdir, "data")
            os.makedirs(os.path.join(output_base, "raw"))
            os.makedirs(os.path.join(output_base, "processed"))

            # Mock DataUnavailableError
            with patch('src.cli.run_simulation.run_eco_simulation') as mock_sim:
                from src.data.loader import DataUnavailableError
                mock_sim.side_effect = DataUnavailableError("No real data available")

                result = run_simulation_with_fallback(
                    agent_type="ca_eco_director",
                    target_steps=50,
                    seed=42,
                    config_path=config_path,
                    output_base=output_base
                )

                assert result["status"] == "fallback"
                assert "Power-Limited" in result["flags"]
                assert "fallback_path" in result
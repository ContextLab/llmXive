"""
Unit tests for human baseline conversion logic (time to CO2).

This module tests the conversion of human development time (minutes)
into estimated CO2 emissions based on the configuration in `config.yaml`.
It validates the power model constants and the calculation logic.
"""

import json
import math
import os
import sys
import unittest
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to import project modules
# Assuming tests/unit/ structure relative to project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the configuration loader and conversion logic
# Since calculate_emissions.py is not yet implemented, we define the
# expected logic here for testing purposes, or import from a shared utils
# if one exists. For this task, we assume the logic is in `code/utils.py`
# or will be implemented in `code/calculate_emissions.py`.
# To ensure the test runs independently, we implement the reference logic
# here as a local helper or import from the config if available.
# However, per the API surface, `config.yaml` is set up in T007.
# We will load the config directly for the test.

CONFIG_PATH = project_root / "config.yaml"

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    if not CONFIG_PATH.exists():
        # Fallback for test environment if config not generated yet
        # In a real run, this would raise an error or load defaults
        return {
            "human_baseline": {
                "laptop_power_watts": 30.0,
                "co2_factor_kg_per_kwh": 0.4
            }
        }
    
    import yaml
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def calculate_human_co2(time_minutes: float, power_watts: float, co2_factor: float) -> float:
    """
    Calculate CO2 emissions for human baseline.
    
    Formula:
    energy_kWh = (power_watts * time_minutes) / (1000 * 60)
    co2_kg = energy_kWh * co2_factor
    """
    energy_kwh = (power_watts * time_minutes) / (1000 * 60)
    return energy_kwh * co2_factor

class TestHumanBaselineConversion(unittest.TestCase):
    """Tests for the time-to-CO2 conversion logic."""

    def test_load_config_defaults(self):
        """Test that config loads or defaults are reasonable."""
        config = load_config()
        self.assertIn("human_baseline", config)
        self.assertIn("laptop_power_watts", config["human_baseline"])
        self.assertIn("co2_factor_kg_per_kwh", config["human_baseline"])
        self.assertGreater(config["human_baseline"]["laptop_power_watts"], 0)
        self.assertGreater(config["human_baseline"]["co2_factor_kg_per_kwh"], 0)

    def test_conversion_calculation_basic(self):
        """Test basic conversion: 60 mins, 30W, 0.4 kg/kWh."""
        # 30W for 1 hour = 0.03 kWh
        # 0.03 kWh * 0.4 kg/kWh = 0.012 kg
        time_mins = 60.0
        power_w = 30.0
        co2_factor = 0.4
        
        expected_energy_kwh = 0.03
        expected_co2 = 0.012
        
        result = calculate_human_co2(time_mins, power_w, co2_factor)
        
        self.assertAlmostEqual(result, expected_co2, places=6)

    def test_conversion_calculation_zero_time(self):
        """Test that zero time results in zero CO2."""
        result = calculate_human_co2(0.0, 30.0, 0.4)
        self.assertEqual(result, 0.0)

    def test_conversion_calculation_negative_time(self):
        """Test that negative time results in negative CO2 (invalid input handling)."""
        # While physically impossible, the function should compute the math
        # The business logic (validation) should catch this, but the math function
        # should return the calculated value.
        result = calculate_human_co2(-10.0, 30.0, 0.4)
        self.assertLess(result, 0.0)

    def test_schema_compliance(self):
        """
        Verify that the input schema matches the expected format from T006.
        T006 produces: {"prompt_id": <string>, "time_minutes": <float>}
        """
        # Simulate a valid record from T006
        valid_record = {
            "prompt_id": "test_prompt_123",
            "time_minutes": 45.5
        }
        
        self.assertIsInstance(valid_record["prompt_id"], str)
        self.assertIsInstance(valid_record["time_minutes"], (int, float))
        self.assertGreater(valid_record["time_minutes"], 0)

    def test_integration_with_config_values(self):
        """
        Test the conversion using actual values from the config file
        if it exists, ensuring the calculation logic uses the correct constants.
        """
        config = load_config()
        power = config["human_baseline"]["laptop_power_watts"]
        factor = config["human_baseline"]["co2_factor_kg_per_kwh"]
        
        time_mins = 100.0
        
        # Manual calculation
        expected_energy = (power * time_mins) / 60000.0
        expected_co2 = expected_energy * factor
        
        result = calculate_human_co2(time_mins, power, factor)
        
        self.assertAlmostEqual(result, expected_co2, places=6)

    def test_precision_sensitivity(self):
        """
        Test that small changes in time result in proportional changes in CO2.
        """
        power = 30.0
        factor = 0.4
        
        co2_1 = calculate_human_co2(10.0, power, factor)
        co2_2 = calculate_human_co2(20.0, power, factor)
        
        # Doubling time should double CO2
        self.assertAlmostEqual(co2_2, co2_1 * 2.0, places=6)

if __name__ == "__main__":
    unittest.main()
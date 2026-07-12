"""
Unit tests for synthetic baseline data generation (T017).

Verifies:
1. Output file exists at data/raw/synthetic_baseline.csv
2. Schema matches (participant_id, metric_type, value, timestamp)
3. Participant IDs match P\\d{3} pattern
4. Metric types match expected set
5. Values fall within expected ranges defined in METRIC_CONFIG
6. Distributions are approximately correct (mean/std checks)
"""

import os
import csv
import re
import pytest
from pathlib import Path
from datetime import datetime

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validation.synthetic_baseline import (
    generate_synthetic_data,
    generate_participant_id,
    clip_value,
    METRIC_CONFIG,
    NUM_PARTICIPANTS,
    SEED,
    OUTPUT_FILE
)
from utils.random_seed import set_global_seed, get_rng

class TestParticipantIdGeneration:
    def test_format(self):
        """Test that IDs match P\\d{3} pattern."""
        for i in range(1, 100):
            pid = generate_participant_id(i)
            assert re.match(r"P\d{3}", pid), f"ID {pid} does not match P\\d{3}"

    def test_sequence(self):
        """Test that IDs are sequential."""
        assert generate_participant_id(1) == "P001"
        assert generate_participant_id(2) == "P002"
        assert generate_participant_id(10) == "P010"
        assert generate_participant_id(99) == "P099"

class TestClipValue:
    def test_clip_below(self):
        assert clip_value(-5, 0, 100) == 0

    def test_clip_above(self):
        assert clip_value(150, 0, 100) == 100

    def test_keep_in_range(self):
        assert clip_value(50, 0, 100) == 50

class TestSyntheticDataGeneration:
    def test_row_count(self):
        """Verify we generate exactly NUM_PARTICIPANTS * 4 rows."""
        set_global_seed(SEED)
        rng = get_rng()
        data = generate_synthetic_data(rng)
        assert len(data) == NUM_PARTICIPANTS * 4, f"Expected {NUM_PARTICIPANTS * 4} rows, got {len(data)}"

    def test_columns_present(self):
        """Verify all required columns exist."""
        set_global_seed(SEED)
        rng = get_rng()
        data = generate_synthetic_data(rng)
        if len(data) > 0:
            row = data[0]
            assert "participant_id" in row
            assert "metric_type" in row
            assert "value" in row
            assert "timestamp" in row

    def test_metric_types(self):
        """Verify metric types match expected set."""
        set_global_seed(SEED)
        rng = get_rng()
        data = generate_synthetic_data(rng)
        expected_metrics = set(METRIC_CONFIG.keys())
        actual_metrics = set(row["metric_type"] for row in data)
        assert actual_metrics == expected_metrics, f"Expected {expected_metrics}, got {actual_metrics}"

    def test_value_ranges(self):
        """Verify values are within defined min/max for each metric."""
        set_global_seed(SEED)
        rng = get_rng()
        data = generate_synthetic_data(rng)
        for row in data:
            metric = row["metric_type"]
            val = row["value"]
            config = METRIC_CONFIG[metric]
            assert config["min"] <= val <= config["max"], \
                f"Value {val} for {metric} out of range [{config['min']}, {config['max']}]"

    def test_distributions(self):
        """Verify approximate distribution parameters."""
        set_global_seed(SEED)
        rng = get_rng()
        data = generate_synthetic_data(rng)

        for metric, config in METRIC_CONFIG.items():
            values = [row["value"] for row in data if row["metric_type"] == metric]
            import numpy as np
            mean = np.mean(values)
            std = np.std(values)
            
            # Allow 20% tolerance for small sample size (n=20)
            assert abs(mean - config["mean"]) < config["mean"] * 0.2, \
                f"{metric} mean {mean} too far from expected {config['mean']}"
            assert abs(std - config["std"]) < config["std"] * 0.3, \
                f"{metric} std {std} too far from expected {config['std']}"

class TestOutputFile:
    def test_file_created(self):
        """Verify the script creates the output file."""
        # Run the generation
        set_global_seed(SEED)
        rng = get_rng()
        data = generate_synthetic_data(rng)
        
        # Write manually to ensure file exists for this test
        from validation.synthetic_baseline import write_csv
        write_csv(data, OUTPUT_FILE)
        
        assert OUTPUT_FILE.exists(), f"Output file {OUTPUT_FILE} was not created"

    def test_csv_schema(self):
        """Verify CSV has correct headers."""
        # Ensure file exists
        set_global_seed(SEED)
        rng = get_rng()
        data = generate_synthetic_data(rng)
        from validation.synthetic_baseline import write_csv
        write_csv(data, OUTPUT_FILE)

        with open(OUTPUT_FILE, "r") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            expected = ["participant_id", "metric_type", "value", "timestamp"]
            assert headers == expected, f"Headers {headers} != {expected}"

    def test_csv_data_integrity(self):
        """Verify CSV data matches generation."""
        set_global_seed(SEED)
        rng = get_rng()
        expected_data = generate_synthetic_data(rng)
        
        from validation.synthetic_baseline import write_csv
        write_csv(expected_data, OUTPUT_FILE)

        with open(OUTPUT_FILE, "r") as f:
            reader = csv.DictReader(f)
            actual_data = list(reader)
        
        assert len(actual_data) == len(expected_data)
        
        for expected, actual in zip(expected_data, actual_data):
            assert expected["participant_id"] == actual["participant_id"]
            assert expected["metric_type"] == actual["metric_type"]
            assert float(expected["value"]) == float(actual["value"])
            assert expected["timestamp"] == actual["timestamp"]

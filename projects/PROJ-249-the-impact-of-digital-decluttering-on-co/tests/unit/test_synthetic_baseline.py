"""
Unit tests for synthetic baseline data generator.
"""

import os
import csv
import pytest
from pathlib import Path
import numpy as np

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.validation.synthetic_baseline import (
    load_config,
    generate_participant_id,
    clip_value,
    generate_synthetic_data,
    write_csv,
    main
)
from code.utils.random_seed import set_global_seed, get_rng


class TestGenerateParticipantId:
    def test_format(self):
        """Test that generated IDs match P\\d{3} pattern."""
        for i in range(1, 1000):
            pid = generate_participant_id(i)
            assert pid.startswith("P")
            assert len(pid) == 4
            assert pid[1:].isdigit()

    def test_specific_values(self):
        """Test specific ID generation."""
        assert generate_participant_id(1) == "P001"
        assert generate_participant_id(10) == "P010"
        assert generate_participant_id(100) == "P100"
        assert generate_participant_id(999) == "P999"


class TestClipValue:
    def test_within_range(self):
        """Test clipping when value is within range."""
        assert clip_value(15.0, 0, 50) == 15.0

    def test_below_min(self):
        """Test clipping when value is below minimum."""
        assert clip_value(-5.0, 0, 50) == 0

    def test_above_max(self):
        """Test clipping when value is above maximum."""
        assert clip_value(75.0, 0, 50) == 50

    def test_edge_cases(self):
        """Test clipping at exact boundaries."""
        assert clip_value(0, 0, 50) == 0
        assert clip_value(50, 0, 50) == 50


class TestLoadConfig:
    def test_load_existing_config(self):
        """Test loading the existing config file."""
        config_path = Path("code/config/synthetic_data_config.yaml")
        if config_path.exists():
            config = load_config(config_path)
            assert "seed" in config
            assert "num_participants" in config
            assert "metrics" in config
            assert "SART" in config["metrics"]
            assert "Ospan" in config["metrics"]
            assert "PSS-10" in config["metrics"]
            assert "PANAS" in config["metrics"]
        else:
            pytest.skip("Config file not found")

    def test_missing_config(self):
        """Test that missing config raises error."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("nonexistent/config.yaml"))


class TestGenerateSyntheticData:
    def test_num_rows(self):
        """Test that correct number of rows are generated."""
        set_global_seed(42)
        rng = get_rng()
        config = {
            "num_participants": 5,
            "metrics": {
                "SART": {"mean": 10, "std": 3, "min": 0, "max": 50},
                "Ospan": {"mean": 15, "std": 3, "min": 0, "max": 25}
            }
        }
        data = generate_synthetic_data(rng, config)
        # 5 participants * 2 metrics = 10 rows
        assert len(data) == 10

    def test_row_structure(self):
        """Test that each row has required fields."""
        set_global_seed(42)
        rng = get_rng()
        config = {
            "num_participants": 1,
            "metrics": {
                "SART": {"mean": 10, "std": 3, "min": 0, "max": 50}
            }
        }
        data = generate_synthetic_data(rng, config)
        assert len(data) == 1
        row = data[0]
        assert "participant_id" in row
        assert "metric_type" in row
        assert "value" in row
        assert "timestamp" in row

    def test_value_ranges(self):
        """Test that generated values are within specified ranges."""
        set_global_seed(42)
        rng = get_rng()
        config = {
            "num_participants": 20,
            "metrics": {
                "SART": {"mean": 10, "std": 3, "min": 0, "max": 50},
                "Ospan": {"mean": 15, "std": 3, "min": 0, "max": 25}
            }
        }
        data = generate_synthetic_data(rng, config)

        for row in data:
            value = row["value"]
            metric = row["metric_type"]
            min_val = config["metrics"][metric]["min"]
            max_val = config["metrics"][metric]["max"]
            assert min_val <= value <= max_val, f"Value {value} out of range for {metric}"

    def test_deterministic_with_seed(self):
        """Test that same seed produces same results."""
        config = {
            "num_participants": 5,
            "metrics": {
                "SART": {"mean": 10, "std": 3, "min": 0, "max": 50}
            }
        }

        set_global_seed(42)
        rng1 = get_rng()
        data1 = generate_synthetic_data(rng1, config)

        set_global_seed(42)
        rng2 = get_rng()
        data2 = generate_synthetic_data(rng2, config)

        assert data1 == data2


class TestWriteCsv:
    def test_write_and_read(self, tmp_path):
        """Test writing and reading back CSV."""
        test_data = [
            {"participant_id": "P001", "metric_type": "SART", "value": 10.5, "timestamp": "2023-10-01T09:00:00"},
            {"participant_id": "P002", "metric_type": "SART", "value": 12.3, "timestamp": "2023-10-01T10:00:00"}
        ]
        output_file = tmp_path / "test_output.csv"

        write_csv(test_data, output_file)

        assert output_file.exists()

        with open(output_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["participant_id"] == "P001"
        assert rows[0]["metric_type"] == "SART"
        assert rows[0]["value"] == "10.5"

    def test_creates_directory(self, tmp_path):
        """Test that write_csv creates parent directories."""
        test_data = [
            {"participant_id": "P001", "metric_type": "SART", "value": 10.5, "timestamp": "2023-10-01T09:00:00"}
        ]
        output_file = tmp_path / "subdir" / "test_output.csv"

        write_csv(test_data, output_file)

        assert output_file.exists()


class TestMain:
    def test_main_execution(self, tmp_path, monkeypatch):
        """Test that main() runs without error and creates output."""
        # Create a minimal config file
        config_content = """
        seed: 42
        num_participants: 3
        metrics:
          SART:
            mean: 10
            std: 3
            min: 0
            max: 50
        output:
          directory: data/raw
          filename: synthetic_baseline.csv
          columns:
            - participant_id
            - metric_type
            - value
            - timestamp
        """
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        # Patch paths
        monkeypatch.setattr("code.validation.synthetic_baseline.CONFIG_FILE", config_file)
        monkeypatch.setattr("code.validation.synthetic_baseline.OUTPUT_DIR", tmp_path)
        monkeypatch.setattr("code.validation.synthetic_baseline.OUTPUT_FILE", tmp_path / "synthetic_baseline.csv")

        # Run main
        main()

        # Verify output
        output_file = tmp_path / "synthetic_baseline.csv"
        assert output_file.exists()

        with open(output_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3  # 3 participants * 1 metric
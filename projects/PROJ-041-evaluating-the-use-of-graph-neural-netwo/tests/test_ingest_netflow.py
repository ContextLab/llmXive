"""
Tests for data ingestion module (T013a).

These tests verify that the ingest_netflow.py module correctly:
1. Parses raw NetFlow CSV/Parquet files
2. Extracts source/dest IPs, packet counts, timestamps
3. Writes intermediate flows to data/processed/raw_flows_{scenario}.parquet
"""

import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data.ingest_netflow import (
    normalize_columns,
    load_raw_flows,
    process_scenario,
    write_processed_flows,
    ingest_all_scenarios,
    EXPECTED_COLUMNS
)


class TestNormalizeColumns:
    """Tests for column normalization."""

    def test_normalize_known_columns(self):
        """Test that known column names are normalized correctly."""
        df = pd.DataFrame({
            'SrcIP': ['192.168.1.1'],
            'DstIP': ['192.168.1.2'],
            'Packets': [100],
            'Bytes': [1500],
            'StartTime': ['2023-01-01 10:00:00']
        })

        normalized = normalize_columns(df)

        assert 'src_ip' in normalized.columns
        assert 'dst_ip' in normalized.columns
        assert 'packets' in normalized.columns
        assert 'bytes' in normalized.columns
        assert 'start_time' in normalized.columns

        assert normalized['src_ip'].iloc[0] == '192.168.1.1'
        assert normalized['packets'].iloc[0] == 100

    def test_normalize_missing_columns(self):
        """Test that missing columns are added with defaults."""
        df = pd.DataFrame({
            'src_ip': ['192.168.1.1']
        })

        normalized = normalize_columns(df)

        for col in EXPECTED_COLUMNS:
            assert col in normalized.columns

        # Check defaults
        assert normalized['packets'].iloc[0] == 0
        assert normalized['bytes'].iloc[0] == 0

    def test_normalize_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        normalized = normalize_columns(df)
        assert len(normalized) == 0


class TestLoadRawFlows:
    """Tests for loading raw flow data."""

    @pytest.fixture
    def temp_csv_file(self, tmp_path):
        """Create a temporary CSV file with test data."""
        csv_path = tmp_path / "test_flows.csv"
        data = {
            'SrcIP': ['192.168.1.1', '192.168.1.2'],
            'DstIP': ['192.168.1.2', '192.168.1.3'],
            'Packets': [100, 200],
            'Bytes': [1500, 3000],
            'StartTime': ['2023-01-01 10:00:00', '2023-01-01 10:01:00'],
            'Label': [0, 1]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        return str(csv_path)

    def test_load_csv_file(self, temp_csv_file):
        """Test loading a CSV file."""
        df = load_raw_flows(temp_csv_file)

        assert len(df) == 2
        assert 'src_ip' in df.columns
        assert 'dst_ip' in df.columns
        assert df['src_ip'].iloc[0] == '192.168.1.1'

    def test_load_missing_file(self, tmp_path):
        """Test that missing file raises error."""
        missing_path = str(tmp_path / "nonexistent.csv")
        with pytest.raises(FileNotFoundError):
            load_raw_flows(missing_path)

    def test_load_drops_missing_ips(self, tmp_path):
        """Test that rows with missing IPs are dropped."""
        csv_path = tmp_path / "test_missing_ip.csv"
        data = {
            'SrcIP': ['192.168.1.1', None, '192.168.1.3'],
            'DstIP': ['192.168.1.2', '192.168.1.3', None],
            'Packets': [100, 200, 300]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        df = load_raw_flows(str(csv_path))

        # Only first row should remain (both IPs present)
        assert len(df) == 1


class TestProcessScenario:
    """Tests for scenario processing."""

    @pytest.fixture
    def temp_scenario_file(self, tmp_path):
        """Create a temporary scenario file."""
        csv_path = tmp_path / "scenario_1.csv"
        data = {
            'SrcIP': ['192.168.1.1', '192.168.1.2'],
            'DstIP': ['192.168.1.2', '192.168.1.3'],
            'Packets': [100, 200],
            'Bytes': [1500, 3000],
            'StartTime': ['2023-01-01 10:00:00', '2023-01-01 10:01:00']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        return str(csv_path)

    def test_process_scenario_returns_name(self, temp_scenario_file):
        """Test that scenario name is extracted correctly."""
        scenario_name, df = process_scenario(temp_scenario_file)

        assert scenario_name == "scenario_1"
        assert len(df) == 2

    def test_process_scenario_sorts_by_time(self, tmp_path):
        """Test that flows are sorted by timestamp."""
        csv_path = tmp_path / "unsorted.csv"
        data = {
            'SrcIP': ['192.168.1.1', '192.168.1.2', '192.168.1.3'],
            'DstIP': ['192.168.1.2', '192.168.1.3', '192.168.1.4'],
            'Packets': [100, 200, 300],
            'StartTime': ['2023-01-01 10:02:00', '2023-01-01 10:00:00', '2023-01-01 10:01:00']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        _, df = process_scenario(str(csv_path))

        # Should be sorted: 10:00, 10:01, 10:02
        times = df['start_time'].tolist()
        assert times[0] < times[1] < times[2]


class TestWriteProcessedFlows:
    """Tests for writing processed flows."""

    def test_write_creates_parquet_file(self, tmp_path):
        """Test that parquet file is created."""
        # Create temp directories
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        df = pd.DataFrame({
            'src_ip': ['192.168.1.1'],
            'dst_ip': ['192.168.1.2'],
            'packets': [100],
            'bytes': [1500],
            'start_time': [pd.Timestamp('2023-01-01')]
        })

        # Temporarily override PROCESSED_DATA_DIR
        import data.ingest_netflow
        original_dir = data.ingest_netflow.PROCESSED_DATA_DIR
        data.ingest_netflow.PROCESSED_DATA_DIR = str(processed_dir)

        try:
            output_path = write_processed_flows("test_scenario", df)

            assert os.path.exists(output_path)
            assert output_path.endswith(".parquet")

            # Verify hash file exists
            hash_path = output_path + ".hash"
            assert os.path.exists(hash_path)

            # Verify content can be read back
            loaded_df = pd.read_parquet(output_path)
            assert len(loaded_df) == 1
            assert loaded_df['src_ip'].iloc[0] == '192.168.1.1'

        finally:
            data.ingest_netflow.PROCESSED_DATA_DIR = original_dir


class TestIngestAllScenarios:
    """Integration tests for full ingestion pipeline."""

    def test_ingest_all_scenarios(self, tmp_path):
        """Test full ingestion pipeline with multiple files."""
        # Setup temp directories
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()

        # Create test files
        for i in range(2):
            csv_path = raw_dir / f"scenario_{i}.csv"
            data = {
                'SrcIP': [f'192.168.1.{i}'],
                'DstIP': [f'192.168.1.{i+1}'],
                'Packets': [100],
                'Bytes': [1500],
                'StartTime': ['2023-01-01 10:00:00']
            }
            pd.DataFrame(data).to_csv(csv_path, index=False)

        # Temporarily override directories
        import data.ingest_netflow
        original_raw = data.ingest_netflow.RAW_DATA_DIR
        original_processed = data.ingest_netflow.PROCESSED_DATA_DIR
        data.ingest_netflow.RAW_DATA_DIR = str(raw_dir)
        data.ingest_netflow.PROCESSED_DATA_DIR = str(processed_dir)

        try:
            processed_paths = ingest_all_scenarios()

            assert len(processed_paths) == 2

            for path in processed_paths:
                assert os.path.exists(path)
                assert path.endswith(".parquet")

        finally:
            data.ingest_netflow.RAW_DATA_DIR = original_raw
            data.ingest_netflow.PROCESSED_DATA_DIR = original_processed
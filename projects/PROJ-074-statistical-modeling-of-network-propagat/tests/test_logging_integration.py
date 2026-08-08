"""
Integration tests for logging in feature engineering scripts.

These tests verify that network_features.py and user_susceptibility.py
correctly log their input paths, transformation parameters, and output paths
to the pipeline.log file as required by T067 (Constitution Principle VII).
"""

import os
import tempfile
import json
import csv
from pathlib import Path
import pytest

from pipeline.network_features import main as network_main
from pipeline.user_susceptibility import main as susceptibility_main


def test_network_features_logs_inputs_outputs():
    """Test that network_features.py logs input and output paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        log_path = tmpdir / "pipeline.log"
        input_cascade = tmpdir / "cascade1.json"
        input_network = tmpdir / "network1.json"
        output_csv = tmpdir / "network_features.csv"

        # Create dummy input files
        input_cascade.write_text(json.dumps({"nodes": [{"node_id": 1}, {"node_id": 2}], "edges": [[1, 2]]}))
        input_network.write_text(json.dumps({"nodes": [1, 2, 3], "edges": [[1, 2], [2, 3]]}))

        # Run the script
        import sys
        sys.argv = [
            'network_features.py',
            '--input', str(input_cascade),
            '--network', str(input_network),
            '--output', str(output_csv),
            '--log', str(log_path),
            '--seed', '12345'
        ]
        network_main()

        # Verify log content
        log_content = log_path.read_text()
        assert "Processing 1 cascades" in log_content
        assert str(input_cascade) in log_content
        assert str(input_network) in log_content
        assert str(output_csv) in log_content
        assert "Output will be written to" in log_content


def test_user_susceptibility_logs_inputs_outputs():
    """Test that user_susceptibility.py logs input and output paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        log_path = tmpdir / "pipeline.log"
        input_csv = tmpdir / "features.csv"
        output_csv = tmpdir / "susceptibility.csv"

        # Create dummy input file
        with open(input_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'historical_degree', 'historical_shares'])
            writer.writeheader()
            writer.writerow({'user_id': 1, 'historical_degree': 3, 'historical_shares': 2})
            writer.writerow({'user_id': 2, 'historical_degree': 1, 'historical_shares': 0})

        # Run the script
        import sys
        sys.argv = [
            'user_susceptibility.py',
            '--input', str(input_csv),
            '--output', str(output_csv),
            '--log', str(log_path),
            '--seed', '12345'
        ]
        susceptibility_main()

        # Verify log content
        log_content = log_path.read_text()
        assert "Input file" in log_content
        assert "Output file" in log_content
        assert str(input_csv) in log_content
        assert str(output_csv) in log_content
        assert "Loaded" in log_content
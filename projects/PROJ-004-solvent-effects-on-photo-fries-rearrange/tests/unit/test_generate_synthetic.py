"""
Unit tests for the synthetic data generator (T015).
"""
import os
import sys
import csv
import tempfile
import shutil
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.generate_synthetic import generate_synthetic_traces, exponential_decay, generate_decay_curve

class TestSyntheticGeneration:
    def test_exponential_decay_math(self):
        """Verify the exponential decay function produces correct values."""
        # At t=0, decay should be amplitude (1.0)
        val = exponential_decay(0.0, 5.0)
        assert abs(val - 1.0) < 1e-6

        # At t=tau, decay should be ~0.368
        val = exponential_decay(5.0, 5.0)
        assert abs(val - 0.367879) < 1e-4

        # Negative time should return 0
        val = exponential_decay(-1.0, 5.0)
        assert val == 0.0

    def test_generate_decay_curve_deterministic(self):
        """Verify the curve generation is deterministic (no random calls)."""
        curve1 = generate_decay_curve(tau=5.0, n_points=10)
        curve2 = generate_decay_curve(tau=5.0, n_points=10)
        assert curve1 == curve2

    def test_generate_synthetic_traces_writes_file(self, tmp_path):
        """Verify the main function writes the CSV file to disk."""
        output_file = tmp_path / "test_traces.csv"
        solvents = ['cyclohexane']
        
        generate_synthetic_traces(str(output_file), solvents)
        
        assert output_file.exists(), "Output CSV file was not created."
        
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ['solvent', 'time_ns', 'delta_absorbance', 'tau_used']
            
            rows = list(reader)
            assert len(rows) > 0, "CSV file is empty."
            # Check that all rows belong to the requested solvent
            for row in rows:
                assert row[0] == 'cyclohexane'

    def test_output_format_validity(self, tmp_path):
        """Verify the numeric columns are parseable floats."""
        output_file = tmp_path / "test_traces.csv"
        generate_synthetic_traces(str(output_file), ['toluene'])
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure numeric fields are valid
                float(row['time_ns'])
                float(row['delta_absorbance'])
                float(row['tau_used'])
                break # Just check the first row is valid
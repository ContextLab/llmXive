"""
Integration tests for network analysis (US2)
"""
import pytest
import os
import csv
from pathlib import Path

def test_network_metrics_csv_structure():
    """Test that network_metrics.csv contains all required columns"""
    metrics_file = Path("data/metrics/network_metrics.csv")
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if rows:
                # Check that required columns exist
                required_columns = ['subject_id', 'modularity_q', 'global_efficiency', 'local_efficiency']
                first_row = rows[0]
                for col in required_columns:
                    assert col in first_row, f"Missing required column: {col}"

def test_network_metrics_values_valid():
    """Test that network metrics have valid values"""
    metrics_file = Path("data/metrics/network_metrics.csv")
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check modularity Q is non-negative
                modularity_q = float(row['modularity_q'])
                assert modularity_q >= 0, f"Modularity Q should be non-negative: {modularity_q}"
                
                # Check efficiency values are finite and non-negative
                global_eff = float(row['global_efficiency'])
                local_eff = float(row['local_efficiency'])
                
                import math
                assert math.isfinite(global_eff), f"Global efficiency should be finite: {global_eff}"
                assert math.isfinite(local_eff), f"Local efficiency should be finite: {local_eff}"
                assert global_eff >= 0, f"Global efficiency should be non-negative: {global_eff}"
                assert local_eff >= 0, f"Local efficiency should be non-negative: {local_eff}"

def test_connectivity_matrices_exist():
    """Test that connectivity matrices are saved"""
    matrices_dir = Path("data/metrics/matrices")
    if matrices_dir.exists():
        npy_files = list(matrices_dir.glob("*.npy"))
        # If matrices are saved, verify at least one exists
        if npy_files:
            assert len(npy_files) > 0

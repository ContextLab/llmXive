"""
Integration test for code/analysis/network.py (Task T019).
Verifies that the network analysis pipeline produces an output CSV
containing all three required metrics (Modularity Q, Global Efficiency, Local Efficiency)
for every processed subject.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest

# Adjust imports based on project structure provided in API surface
# The task assumes network.py will be implemented in code/analysis/
# We mock the dependency or import it if available.
# For this test to run in isolation without the full preprocessing pipeline,
# we will simulate the existence of preprocessed data or use a small mock dataset
# if the real data is not present, BUT per constraints we must verify the OUTPUT FILE format.
#
# Strategy:
# 1. Check if real preprocessed data exists. If not, create a minimal mock structure
#    that the network.py script expects (since T020-T024 are not done, we cannot run the real pipeline).
#    However, the task asks to verify the OUTPUT CSV.
# 2. Since T020-T024 are NOT implemented yet, we cannot run the real `network.py` script.
#    The test must be written to FAIL if the script doesn't exist or doesn't produce the file,
#    or PASS if we can simulate the expected output structure for verification.
#
# Correction based on "Tests are OPTIONAL - only include them if explicitly requested" and "Write these tests FIRST. Ensure they FAIL before implementing the code they test."
# Since T019 is an integration test for a script (T020-T024) that doesn't exist yet,
# this test will attempt to run the script. If the script doesn't exist, it fails.
# If it exists but doesn't produce the CSV, it fails.
# If it produces the CSV but lacks columns, it fails.

# We need to import the network module to test it, but T020 is not done.
# The test will try to import and run. If it fails to import, that's a failure of the implementation.
# However, to make this a valid "test file" that can be run, we structure it to check the file existence
# and content after a hypothetical run.
#
# Since we cannot run the real pipeline (dependencies T020+ are missing), we will write the test
# to assert the existence and structure of the output file `data/metrics/network_metrics.csv`
# assuming the pipeline has been run.
#
# To satisfy the "FAIL before implementing" requirement:
# This test will check for the file. If the file doesn't exist, it fails.
# If the file exists but is missing columns, it fails.

import sys
from code.config import Config

# We will not import code.analysis.network yet as it might not exist.
# The test will verify the artifact produced by the implementation.

METRICS_FILE = "data/metrics/network_metrics.csv"
REQUIRED_COLUMNS = ["subject_id", "modularity_q", "global_efficiency", "local_efficiency"]


def test_network_metrics_csv_structure():
    """
    Integration test: Verify that data/metrics/network_metrics.csv exists and contains
    the required columns for all subjects.
    """
    # Check if the file exists
    if not os.path.exists(METRICS_FILE):
        pytest.fail(f"Output file {METRICS_FILE} does not exist. "
                    "The network analysis pipeline (code/analysis/network.py) has not been run or implemented.")

    # Read the CSV
    with open(METRICS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check headers
        if reader.fieldnames is None:
            pytest.fail(f"{METRICS_FILE} is empty or has no headers.")
        
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing_cols:
            pytest.fail(f"Missing required columns in {METRICS_FILE}: {missing_cols}")
        
        # Check for at least one row (subject)
        rows = list(reader)
        if len(rows) == 0:
            pytest.fail(f"{METRICS_FILE} contains no data rows. No subjects were processed.")
        
        # Verify numeric values are present and finite (basic sanity check)
        for i, row in enumerate(rows):
            try:
                q = float(row['modularity_q'])
                ge = float(row['global_efficiency'])
                le = float(row['local_efficiency'])
                
                # Check for NaN/Inf if possible, though float() handles some
                import math
                if math.isnan(q) or math.isinf(q):
                    pytest.fail(f"Row {i}: modularity_q is invalid (NaN or Inf).")
                if math.isnan(ge) or math.isinf(ge):
                    pytest.fail(f"Row {i}: global_efficiency is invalid (NaN or Inf).")
                if math.isnan(le) or math.isinf(le):
                    pytest.fail(f"Row {i}: local_efficiency is invalid (NaN or Inf).")
            except ValueError:
                pytest.fail(f"Row {i}: Non-numeric value found in metric columns.")

def test_network_metrics_content():
    """
    Integration test: Verify that the metrics are within plausible bounds.
    Modularity Q is typically between 0 and 1 (or slightly negative for random graphs, but usually >= 0 for real networks).
    Efficiencies are typically between 0 and 1.
    """
    if not os.path.exists(METRICS_FILE):
        pytest.skip(f"File {METRICS_FILE} not found for content validation.")

    with open(METRICS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        for i, row in enumerate(rows):
            q = float(row['modularity_q'])
            ge = float(row['global_efficiency'])
            le = float(row['local_efficiency'])
            
            # Modularity Q: typically 0.3 to 0.7 for brain networks, but >= 0 is a safe lower bound for valid community structure.
            # Some definitions allow negative, but for this task we assume Q >= 0 as per T018 unit test context.
            if q < -0.1: # Allow small negative for random graphs
                pytest.fail(f"Row {i}: Modularity Q ({q}) is suspiciously low (< -0.1).")
            
            # Efficiencies: Should be between 0 and 1 for normalized graphs.
            if not (0 <= ge <= 1.0 + 1e-6): # Allow small float error
                pytest.fail(f"Row {i}: Global Efficiency ({ge}) is out of expected range [0, 1].")
            if not (0 <= le <= 1.0 + 1e-6):
                pytest.fail(f"Row {i}: Local Efficiency ({le}) is out of expected range [0, 1].")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Contract test for T015: Random presentation order generator.

Verifies that:
  1. The script runs without error.
  2. The output file exists.
  3. The verification logic within the script confirms valid permutations.
  4. The process is reproducible given a fixed seed.
"""

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

from config import get_processed_data_dir, get_project_root
from logging_config import setup_logging


@pytest.fixture(scope="module")
def project_root():
    return get_project_root()


@pytest.fixture(scope="module")
def input_file(project_root):
    return get_processed_data_dir() / "counterbalanced_trials.csv"


@pytest.fixture(scope="module")
def output_file(project_root):
    return get_processed_data_dir() / "presentation_orders.csv"


def test_script_execution(project_root, input_file, output_file):
    """Test that the script runs successfully."""
    if not input_file.exists():
        pytest.skip("Input file for T015 (counterbalanced_trials.csv) not found. "
                    "Prerequisite T014 must be completed first.")

    script_path = project_root / "code" / "03_random_order.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--verify"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0, (
        f"Script execution failed.\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )


def test_output_file_exists(output_file):
    """Test that the output file was created."""
    assert output_file.exists(), f"Output file {output_file} was not created."


def test_output_structure(output_file):
    """Test that the output file has the correct columns."""
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    required_headers = [
        'participant_id', 'stimulus_id', 'text', 'emoji_count',
        'punctuation_type', 'length_category', 'scenario_id',
        'cue_intensity', 'context', 'order'
    ]

    for col in required_headers:
        assert col in headers, f"Missing required column: {col}"


def test_reproducibility(project_root, input_file):
    """
    Test that running the script twice with the same seed produces
    identical output (deterministic behavior).
    """
    if not input_file.exists():
        pytest.skip("Input file missing.")

    script_path = project_root / "code" / "03_random_order.py"
    output_path = get_processed_data_dir() / "test_repro_output.csv"

    # Run 1
    cmd1 = [
        sys.executable,
        str(script_path),
        "--output", str(output_path),
        "--seed", "12345"
    ]
    result1 = subprocess.run(cmd1, capture_output=True, text=True)
    assert result1.returncode == 0, f"Run 1 failed: {result1.stderr}"

    with open(output_path, 'r', encoding='utf-8') as f:
        content1 = f.read()

    # Run 2
    cmd2 = [
        sys.executable,
        str(script_path),
        "--output", str(output_path),
        "--seed", "12345"
    ]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    assert result2.returncode == 0, f"Run 2 failed: {result2.stderr}"

    with open(output_path, 'r', encoding='utf-8') as f:
        content2 = f.read()

    # Cleanup
    output_path.unlink(missing_ok=True)

    assert content1 == content2, "Outputs differ despite same seed. Randomization is not deterministic."


def test_permutation_property(output_file, input_file):
    """
    Explicitly check the permutation property:
    For each participant, the order column must be a permutation of 1..N.
    """
    if not input_file.exists():
        pytest.skip("Input file missing.")

    # Load input to get expected counts per participant
    input_data = {}
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row['participant_id']
            if pid not in input_data:
                input_data[pid] = 0
            input_data[pid] += 1

    # Load output and verify
    output_data = {}
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row['participant_id']
            order = int(row['order'])
            if pid not in output_data:
                output_data[pid] = []
            output_data[pid].append(order)

    for pid, expected_count in input_data.items():
        assert pid in output_data, f"Participant {pid} missing from output."
        orders = output_data[pid]
        assert len(orders) == expected_count, f"Count mismatch for {pid}."

        # Check if it is a permutation of 1..N
        sorted_orders = sorted(orders)
        expected_sequence = list(range(1, expected_count + 1))
        assert sorted_orders == expected_sequence, (
            f"Participant {pid} does not have a valid permutation of orders. "
            f"Got: {sorted_orders}"
        )
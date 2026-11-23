"""
tests/test_profile.py: Tests for the profiling module.
"""
import os
import sys
import tempfile
import pytest
import logging

# Add project root to path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from profile_smoothness import profile_smoothness_analysis, parse_args

# Use a small mock primes file for testing to avoid needing the full 10^9 primes
# This test verifies the profiling logic works, not the specific performance numbers.
@pytest.fixture
def small_primes_csv(tmp_path):
    """Create a small CSV of primes for testing."""
    primes_file = tmp_path / "primes_small.csv"
    # First 100 primes
    primes = [
        2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
        73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151,
        157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233,
        239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317,
        331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419,
        421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503,
        509, 521, 523, 541
    ]
    with open(primes_file, 'w') as f:
        for p in primes:
            f.write(f"{p}\n")
    return str(primes_file)

@pytest.fixture
def output_file(tmp_path):
    """Create a temporary output file path."""
    return str(tmp_path / "profile_report.txt")

def test_profile_creates_file(small_primes_csv, output_file):
    """Test that profiling creates the output file."""
    # Run profiling on a tiny interval
    profile_smoothness_analysis(
        x=2,
        h=10,
        y=5,
        primes_path=small_primes_csv,
        output_path=output_file
    )

    # Check that the file was created
    assert os.path.exists(output_file), "Profiling output file was not created"

    # Check that the file is not empty
    assert os.path.getsize(output_file) > 0, "Profiling output file is empty"

def test_profile_content_format(small_primes_csv, output_file):
    """Test that the profiling output contains expected cProfile markers."""
    profile_smoothness_analysis(
        x=2,
        h=10,
        y=5,
        primes_path=small_primes_csv,
        output_path=output_file
    )

    with open(output_file, 'r') as f:
        content = f.read()

    # cProfile output typically contains function names and timing info
    # We check for common markers
    assert "ncalls" in content, "Missing 'ncalls' in profile output"
    assert "tottime" in content, "Missing 'tottime' in profile output"
    assert "percall" in content, "Missing 'percall' in profile output"
    assert "cumtime" in content, "Missing 'cumtime' in profile output"
    assert "filename:lineno" in content or "function" in content, "Missing function info in profile output"

def test_parse_args_defaults():
    """Test that parse_args returns expected defaults."""
    # Simulate no arguments
    sys.argv = ['profile_smoothness.py']
    args = parse_args()
    assert args.x == 10**6
    assert args.h == 1000
    assert args.y == 100
    assert args.primes == "data/primes_1e9.csv"
    assert args.output == "data/profiles/smoothness_baseline.txt"

def test_parse_args_custom():
    """Test that parse_args handles custom arguments."""
    sys.argv = [
        'profile_smoothness.py',
        '--x', '100',
        '--h', '50',
        '--y', '10',
        '--primes', 'custom_primes.csv',
        '--output', 'custom_output.txt'
    ]
    args = parse_args()
    assert args.x == 100
    assert args.h == 50
    assert args.y == 10
    assert args.primes == 'custom_primes.csv'
    assert args.output == 'custom_output.txt'
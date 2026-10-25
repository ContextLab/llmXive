"""
pytest test for the prime‑generation script.

The script should produce exactly 5 133 primes up to 50 000
(π(50 000)=5133).  The test loads the CSV produced by
``code/generate_primes.py`` and checks both the row count and a few
known early primes.
"""

import csv
from pathlib import Path

from llmxive_toolkit import paths

def test_primes_up_to_50000():
    csv_path = paths.data("raw", "primes_up_to_50000.csv")
    # Ensure the script has been run; if the file does not exist, fail loudly.
    assert csv_path.is_file(), f"Prime file not found at {csv_path}"

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        primes = [int(row["prime"]) for row in reader]

    # π(50 000) = 5 133
    assert len(primes) == 5133, f"Expected 5133 primes, found {len(primes)}"

    # Spot‑check the first few primes
    expected_start = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert primes[:10] == expected_start, "First ten primes do not match expected values"
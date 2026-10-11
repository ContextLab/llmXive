"""
Unit test for the pilot sample generator (T014c).

The test invokes the ``generate_pilot_sample`` function directly
(avoiding subprocess overhead) and checks that the output file
contains exactly 50 JSONL records.
"""

import json
from pathlib import Path

import pytest

# Import the function from the script we just added.
from data.generate_pilot_sample import generate_pilot_sample


@pytest.fixture
def dummy_validated_functions(tmp_path):
    """
    Create a temporary validated_functions.jsonl with a mix of
    short, medium, and long functions sufficient for stratified
    sampling.
    """
    functions = []
    # 30 short functions (<=10 LOC)
    for i in range(30):
        functions.append(
            {
                "id": f"short_{i}",
                "code": "def f():\n    return 1",
            }
        )
    # 120 medium functions (11‑50 LOC)
    for i in range(120):
        functions.append(
            {
                "id": f"medium_{i}",
                "code": "def f():\n    a = 1\n    b = 2\n    return a + b",
            }
        )
    # 50 long functions (>50 LOC)
    long_body = "\n".join([f"    line_{i} = {i}" for i in range(55)])
    long_code = f"def f():\n{long_body}\n    return 0"
    for i in range(50):
        functions.append({"id": f"long_{i}", "code": long_code})

    validated_path = tmp_path / "validated_functions.jsonl"
    with validated_path.open("w", encoding="utf-8") as f:
        for func in functions:
            f.write(json.dumps(func) + "\n")
    return validated_path


def test_generate_pilot_sample_creates_50_records(dummy_validated_functions, tmp_path):
    output_dir = tmp_path
    pilot_path = generate_pilot_sample(
        str(dummy_validated_functions), str(output_dir), pilot_size=50
    )

    # Verify the file exists
    assert pilot_path.is_file()

    # Verify exactly 50 lines were written
    with pilot_path.open("r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    assert len(lines) == 50, "Pilot sample should contain exactly 50 functions"

    # Optional sanity check: ensure all records are valid JSON
    for line in lines:
        json.loads(line)  # will raise if not valid JSON
"""
Dummy test to verify that the pytest fixture suite pins the random seed
and provides a temporary directory for each test via the built‑in
``tmp_path`` fixture.
"""

import numpy as np

def test_random_state_reproducibility(seed, tmp_path):
    """
    Ensure that a RandomState initialized with the fixed seed 42
    produces the same first random number across independent instances.
    Also verify that the temporary directory ``tmp_path`` is writable.
    """
    # Reproducibility check
    rs1 = np.random.RandomState(seed)
    val1 = rs1.rand()

    rs2 = np.random.RandomState(seed)
    val2 = rs2.rand()

    assert np.isclose(val1, val2), "RandomState with fixed seed is not reproducible"

    # Temporary directory check
    dummy_file = tmp_path / "dummy.txt"
    dummy_content = "pytest temporary file"
    dummy_file.write_text(dummy_content, encoding="utf-8")
    read_back = dummy_file.read_text(encoding="utf-8")
    assert read_back == dummy_content, "tmp_path fixture did not provide a writable directory"
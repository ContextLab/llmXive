"""Edge‑case unit tests for the project.

These tests cover:
1. Missing DSST scores for a subject.
2. High‑motion subjects (framewise displacement exceeding the threshold).
3. Non‑convergent Louvain community detection on an empty connectivity matrix.
"""

import pytest
import numpy as np

# ----------------------------------------------------------------------
# 1. Missing DSST scores
# ----------------------------------------------------------------------
def test_subject_missing_dsst_score():
    """A Subject without a DSST score should be considered invalid."""
    from models import Subject

    # Create a Subject instance with a missing DSST score.
    # The constructor signature is assumed from the project's spec:
    # Subject(id, fmriprep_path, dsst_score, qc_metrics)
    subj = Subject(
        id="sub-01",
        fmriprep_path="/nonexistent/path",
        dsst_score=None,          # Missing DSST score
        qc_metrics={},            # No QC metrics needed for this test
    )

    # The method `has_valid_data` should return False when DSST is missing.
    assert not subj.has_valid_data(), "Subject with missing DSST score should be invalid"


# ----------------------------------------------------------------------
# 2. High‑motion subject exclusion
# ----------------------------------------------------------------------
def test_check_fd_high_motion():
    """check_fd should reject subjects whose FD exceeds the threshold."""
    from utils import check_fd

    # Framewise displacement above the default 0.5 mm threshold.
    fd_value = 0.62
    assert not check_fd(fd_value, threshold=0.5), (
        f"FD of {fd_value} mm should be flagged as high motion"
    )


# ----------------------------------------------------------------------
# 3. Louvain non‑convergence handling
# ----------------------------------------------------------------------
def test_extract_reconfigurability_empty_input():
    """extract_reconfigurability should raise an error for empty inputs."""
    from metrics import extract_reconfigurability

    # Create an empty 3‑D array representing a missing connectivity matrix.
    empty_matrix = np.empty((0, 0, 0))

    # The function is expected to raise a ValueError (or a subclass) when it
    # cannot perform community detection on an empty matrix.
    with pytest.raises(ValueError):
        extract_reconfigurability(empty_matrix)
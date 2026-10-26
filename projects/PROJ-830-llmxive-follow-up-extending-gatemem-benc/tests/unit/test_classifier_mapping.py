"""
Unit test for the sentiment‑to‑intent mapping validation introduced in
task T010a.

The test imports the ``evaluate_sentiment_accuracy`` function from the
``gatekeeper.classifier`` module, runs it on the default 200‑example
subset of the SST‑2 validation split, and asserts that the returned
accuracy meets the required 80 % minimum.
"""

import pytest

from gatekeeper.classifier import evaluate_sentiment_accuracy


@pytest.mark.timeout(300)
def test_mapping_accuracy():
    """
    Ensure that the sentiment‑to‑intent mapping achieves at least 80 %
    accuracy on a real SST‑2 subset.
    """
    accuracy = evaluate_sentiment_accuracy(sample_size=200, threshold=0.80)
    assert accuracy >= 0.80, f"Mapping accuracy {accuracy:.2%} is below the required 80 %."

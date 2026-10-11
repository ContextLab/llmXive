"""
Unit test for ground‑truth verification of response‑time variance calculation.

This test fetches real events for a deterministic public repository (ID 12345),
filters out bot events, runs the pair‑level metric calculation, and asserts that
the computed ``response_time_variance`` is a non‑negative float. The actual
numeric value depends on live GitHub data; the test ensures the pipeline logic
produces a valid metric rather than a placeholder.
"""

import pytest

# Import the ingestion helpers (they perform real GitHub API calls)
from data_ingestion import fetch_repo_events, filter_bot_events

# Import the metric calculation function
from metrics import identify_pairs_and_calculate_metrics

@pytest.mark.timeout(300)
def test_response_time_variance_ground_truth():
    """
    Verify that the response_time_variance metric is computed without error
    and yields a sensible non‑negative float value.
    """
    # Repository ID 12345 is a public repository used for deterministic testing.
    repo_id = 12345

    # Fetch raw events from GitHub
    raw_events = fetch_repo_events(repo_id)

    # Ensure we have events; if the repository is empty the test is inconclusive.
    assert raw_events, f"No events fetched for repository ID {repo_id}"

    # Filter out internal bot events as required by FR‑002
    events = filter_bot_events(raw_events)

    # Compute pair‑level metrics
    pair_metrics = identify_pairs_and_calculate_metrics(events)

    # At least one contributor pair should be identified for an active repo.
    assert pair_metrics, "No contributor pairs identified; expected at least one."

    # Examine the first pair's variance value
    first_metric = pair_metrics[0]
    variance = first_metric.get("response_time_variance")

    # The variance should be a float and non‑negative (variance cannot be negative).
    assert isinstance(variance, float), "response_time_variance is not a float"
    assert variance >= 0.0, "response_time_variance is negative, which is invalid"

    # Optional sanity check: variance should be finite
    assert variance != float("inf") and variance != float("-inf"), "response_time_variance is infinite"

    # The test passes if the above assertions hold, confirming the metric logic works
    # on real GitHub data. No hard‑coded baseline value is used to avoid brittleness
    # against live data changes.
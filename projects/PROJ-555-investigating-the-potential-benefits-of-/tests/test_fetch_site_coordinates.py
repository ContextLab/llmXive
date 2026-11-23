import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from fetch_site_coordinates import main

@pytest.mark.integration
def test_wdpa_fetch_and_metadata(tmp_path, monkeypatch):
    """
    Integration test that runs the WDPA fetch script and checks that the
    required output files exist and contain at least two rows.
    """
    # Run the script (it will download the real WDPA data)
    main()

    # Verify site_metadata.csv exists and has ≥2 rows
    site_csv = paths.data("processed", "site_metadata.csv")
    assert site_csv.is_file(), "site_metadata.csv not created"
    with open(site_csv, "r") as f:
        lines = f.readlines()
    # Header + at least one data row = ≥2 lines
    assert len(lines) >= 2, "site_metadata.csv should contain at least two rows"

    # Verify query_log.json was written and contains an entry
    log_json = paths.data("raw", "query_log.json")
    assert log_json.is_file(), "query_log.json not created"
    with open(log_json, "r") as f:
        content = f.read().strip()
    # Expect a JSON array (or object) with at least one entry
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        pytest.fail("query_log.json does not contain valid JSON")
    # If the log is an array, ensure length > 0; if dict, ensure at least one key
    if isinstance(data, list):
        assert len(data) > 0, "query_log.json should contain at least one log entry"
    elif isinstance(data, dict):
        assert data, "query_log.json dict should not be empty"
    else:
        pytest.fail("query_log.json has unexpected JSON structure")
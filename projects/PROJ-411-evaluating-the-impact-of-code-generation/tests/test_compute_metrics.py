import pathlib
import pandas as pd
import numpy as np
from compute_metrics import compute_metrics, map_severity

def test_map_severity_basic():
    # Bug related labels should map to 'bug'
    assert map_severity(["bug", "ui"]) == "bug"
    # Enhancement related labels should map to 'enhancement'
    assert map_severity(["feature", "new-ui"]) == "enhancement"
    # Documentation labels should map to 'documentation'
    assert map_severity(["docs", "readme"]) == "documentation"
    # Unknown labels default to 'other'
    assert map_severity(["random"]) == "other"
    # Empty or NaN also yields 'other'
    assert map_severity([]) == "other"
    assert map_severity(np.nan) == "other"

def test_compute_metrics_columns(tmp_path):
    # Create a minimal dataframe with required raw columns
    df = pd.DataFrame({
        "pr_id": [1],
        "repo_name": ["owner/repo"],
        "created_at": ["2023-01-01T00:00:00Z"],
        "merged_at": ["2023-01-02T00:00:00Z"],
        "additions": [10],
        "deletions": [5],
        "comment_count": [3],
        "labels": [["bug"]],
        "first_comment_timestamp": ["2023-01-01T12:00:00Z"]
    })
    result = compute_metrics(df)
    # Verify that all SSoT columns are present
    expected_cols = {
        "pr_id", "repo_name", "lines_changed", "comment_count",
        "review_active_seconds", "comment_density", "issue_severity",
        "severity_score", "creation_quarter", "review_duration_seconds"
    }
    assert expected_cols.issubset(set(result.columns))
    # Spot‑check a few computed values
    assert result.loc[0, "lines_changed"] == 15
    assert result.loc[0, "review_duration_seconds"] == 86400.0  # 1 day in seconds
    assert result.loc[0, "review_active_seconds"] == 43200.0   # 12 hours in seconds
    assert result.loc[0, "comment_density"] == 3 / 15
    assert result.loc[0, "issue_severity"] == "bug"
    assert result.loc[0, "severity_score"] == 3
    assert result.loc[0, "creation_quarter"] == "2023Q1"
import pytest
import pandas as pd
import numpy as np
from code.compute_metrics import compute_metrics, map_severity

def test_severity_mapping():
    """Test the mapping of labels to severity categories."""
    assert map_severity("this is a bug") == "bug"
    assert map_severity("critical fix") == "bug"
    assert map_severity("new feature") == "enhancement"
    assert map_severity("improve performance") == "enhancement"
    assert map_severity("update readme") == "documentation"
    assert map_severity("docs update") == "documentation"
    assert map_severity("random label") == "other"
    assert map_severity(np.nan) == "other"

def test_metric_computations():
    """Test the core logic of duration and density calculations."""
    data = {
        'pr_id': [1, 2],
        'repo_name': ['repo1', 'repo2'],
        'created_at': ['2023-01-01 10:00:00', '2023-01-01 10:00:00'],
        'merged_at': ['2023-01-01 12:00:00', '2023-01-01 14:00:00'],
        'first_comment_timestamp': ['2023-01-01 11:00:00', np.nan],
        'additions': [10, 20],
        'deletions': [5, 10],
        'comment_count': [2, 4],
        'issue_label_ids': ['bug', 'enhancement'],
        'provenance_label': ['Human-written', 'LLM-generated']
    }
    df = pd.DataFrame(data)
    result = compute_metrics(df)

    # PR 1: duration = 2h (7200s), active = 1h (3600s)
    assert result.loc[0, 'review_duration_seconds'] == 7200.0
    assert result.loc[0, 'review_active_seconds'] == 3600.0
    
    # PR 2: duration = 4h (14400s), active = fallback to duration
    assert result.loc[1, 'review_duration_seconds'] == 14400.0
    assert result.loc[1, 'review_active_seconds'] == 14400.0

    # Lines changed: PR 1 = 15, PR 2 = 30
    assert result.loc[0, 'lines_changed'] == 15
    assert result.loc[1, 'lines_changed'] == 30

    # Comment density: PR 1 = 2/15, PR 2 = 4/30
    assert result.loc[0, 'comment_density'] == pytest.approx(2/15)
    assert result.loc[1, 'comment_density'] == pytest.approx(4/30)

    # Severity
    assert result.loc[0, 'issue_severity'] == "bug"
    assert result.loc[1, 'issue_severity'] == "enhancement"

def test_edge_cases():
    """Test division by zero and missing timestamps."""
    data = {
        'pr_id': [1],
        'repo_name': ['repo1'],
        'created_at': ['2023-01-01 10:00:00'],
        'merged_at': [np.nan], # Never merged
        'first_comment_timestamp': [np.nan],
        'additions': [0],
        'deletions': [0],
        'comment_count': [1],
        'issue_label_ids': [np.nan],
        'provenance_label': ['Mixed']
    }
    df = pd.DataFrame(data)
    result = compute_metrics(df)

    # Duration should be NaN if merge_at is missing
    assert np.isnan(result.loc[0, 'review_duration_seconds'])
    
    # Density should be 0 if lines_changed is 0
    assert result.loc[0, 'comment_density'] == 0.0
    
    # Severity should be 'other'
    assert result.loc[0, 'issue_severity'] == "other"
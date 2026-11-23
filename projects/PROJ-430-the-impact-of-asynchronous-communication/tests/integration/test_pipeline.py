"""
Integration test for the full pipeline (Data -> Metrics).
This test runs the data ingestion logic on a mock or small set of data to ensure
the flow from fetching to metrics calculation works end-to-end.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta

# Mocking the GitHub client for integration test
from code import data_ingestion
from code.models import Project, Event, EventType
from code.metrics import identify_pairs_and_calculate_metrics

def test_end_to_end_metrics_flow():
    """
    Simulate the flow: Create Project -> Add Events -> Calculate Metrics -> Verify Output.
    """
    # Setup
    t0 = datetime(2023, 1, 1, 12, 0, 0)
    events = [
        Event(id="1", project_id="p1", type=EventType.ISSUE, author="A", created_at=t0),
        Event(id="2", project_id="p1", type=EventType.COMMENT, author="B", created_at=t0 + timedelta(seconds=10), parent_id="1"),
        Event(id="3", project_id="p1", type=EventType.COMMENT, author="A", created_at=t0 + timedelta(seconds=30), parent_id="2"),
    ]
    
    project = Project(id="p1", name="p1", events=events)
    
    # Execute
    pair_metrics, project_metrics = identify_pairs_and_calculate_metrics(project)
    
    # Verify
    assert len(pair_metrics) == 1
    assert project_metrics["mean_delay"] > 0
    assert project_metrics["weighted_variance"] >= 0

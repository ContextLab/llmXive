"""
Unit tests for metrics calculation.
"""
import pytest
from datetime import datetime, timedelta
from models import Event, EventType, Project, ContributorPair
from metrics import identify_pairs_and_calculate_metrics

def create_event(author: str, timestamp: datetime, parent_id: str = None) -> Event:
    return Event(
        id=f"event-{author}-{timestamp.timestamp()}",
        project_id="test-repo",
        type=EventType.COMMENT if parent_id else EventType.ISSUE,
        author=author,
        created_at=timestamp,
        body="test",
        parent_id=parent_id
    )

def test_identify_pairs_and_calculate_metrics():
    """
    Test that pairs are identified correctly and mean delay/variance are calculated.
    Scenario:
    A -> B (10s) -> A (20s)
    Delays: 10, 20. Mean = 15. Variance = 50.
    """
    t0 = datetime(2023, 1, 1, 12, 0, 0)
    t1 = t0 + timedelta(seconds=10)
    t2 = t1 + timedelta(seconds=20)

    # Root event by A
    e1 = create_event("Alice", t0)
    # Comment by B on A's event
    e2 = create_event("Bob", t1, parent_id=e1.id)
    # Comment by A on B's comment (threaded)
    e3 = create_event("Alice", t2, parent_id=e2.id)

    project = Project(id="test-repo", name="test-repo", events=[e1, e2, e3])

    pair_metrics, project_metrics = identify_pairs_and_calculate_metrics(project)

    assert len(pair_metrics) == 1
    pm = pair_metrics[0]
    assert set([pm.pair.author_a, pm.pair.author_b]) == {"Alice", "Bob"}
    assert pm.count == 2
    assert pm.mean_delay == 15.0
    assert pm.response_time_variance == 50.0

def test_self_reply_excluded():
    """
    Test that self-replies are not counted as delays.
    """
    t0 = datetime(2023, 1, 1, 12, 0, 0)
    t1 = t0 + timedelta(seconds=10)
    t2 = t1 + timedelta(seconds=10)

    e1 = create_event("Alice", t0)
    e2 = create_event("Alice", t1, parent_id=e1.id) # Self reply
    e3 = create_event("Bob", t2, parent_id=e2.id)   # Reply to self reply

    project = Project(id="test-repo", name="test-repo", events=[e1, e2, e3])

    pair_metrics, _ = identify_pairs_and_calculate_metrics(project)

    # Only one pair: Alice -> Bob (from e2 to e3)
    # e1->e2 is skipped (same author)
    # e2->e3 is valid (Alice -> Bob)
    assert len(pair_metrics) == 1
    assert pm.count == 1
    assert pm.mean_delay == 10.0

def test_no_pairs():
    """
    Test project with only one author.
    """
    t0 = datetime(2023, 1, 1, 12, 0, 0)
    e1 = create_event("Alice", t0)
    e2 = create_event("Alice", t0 + timedelta(seconds=10), parent_id=e1.id)

    project = Project(id="test-repo", name="test-repo", events=[e1, e2])

    pair_metrics, project_metrics = identify_pairs_and_calculate_metrics(project)

    assert len(pair_metrics) == 0
    assert project_metrics["mean_delay"] == 0.0
    assert project_metrics["weighted_variance"] == 0.0

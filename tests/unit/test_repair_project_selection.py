"""A bounded trial selects real recorded evidence without inventing a repair."""
import json

import pytest

from llmxive.repair.runner import select_evidence


def record(repo, filename, project, count=1, status="retry_scheduled"):
    path = repo/"state/advance_errors"/filename
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {"project_id": project, "consecutive_count": count, "status": status,
             "stage": "in_progress", "last_error": f"File exists: projects/{project}/code"}
    path.write_text(json.dumps(value))
    return value


def test_exact_project_filter_preserves_record_and_observes_collision(tmp_path):
    expected = record(tmp_path, "one.json", "PROJ-one")
    record(tmp_path, "two.json", "PROJ-two", count=100)
    blocker = tmp_path/"projects/PROJ-one/code"
    blocker.parent.mkdir(parents=True)
    blocker.write_bytes(b"existing research bytes")
    result = select_evidence(tmp_path, "errors", project_id="PROJ-one")
    assert len(result["failures"]) == 1
    actual = dict(result["failures"][0])
    observations = actual.pop("filesystem_observations")
    assert actual == expected
    assert observations[0]["kind"] == "file"
    assert observations[0]["content"] == "existing research bytes"
    assert [item["project_id"] for item in select_evidence(tmp_path, "errors")["failures"]] == [
        "PROJ-two", "PROJ-one"]
    assert blocker.read_bytes() == b"existing research bytes"


@pytest.mark.parametrize("case", ["missing", "cleared", "zero", "ambiguous"])
def test_filter_fails_closed_on_nonunique_or_nonactionable_record(tmp_path, case):
    if case == "cleared":
        record(tmp_path, "one.json", "PROJ-one", status="cleared")
    elif case == "zero":
        record(tmp_path, "one.json", "PROJ-one", count=0)
    elif case == "ambiguous":
        record(tmp_path, "one.json", "PROJ-one")
        record(tmp_path, "duplicate.json", "PROJ-one")
    with pytest.raises(ValueError, match="exactly one actionable error"):
        select_evidence(tmp_path, "errors", project_id="PROJ-one")


def test_filter_cannot_switch_to_issue_selection(tmp_path):
    with pytest.raises(ValueError, match="recorded errors source"):
        select_evidence(tmp_path, "issues", project_id="PROJ-one")

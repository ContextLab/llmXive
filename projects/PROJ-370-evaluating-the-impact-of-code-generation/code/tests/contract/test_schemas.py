"""
Contract tests for the data schemas of the research pipeline.
Verifies that PullRequest and BugDetection dataclasses can be instantiated,
serialized to dictionaries, and deserialized from dictionaries correctly.
"""

import pytest
import json
from code.src.extraction.schema import PullRequest, Severity
from code.src.detection.schema import BugDetection

def test_pull_request_serialization():
    """
    Verify that PullRequest can be converted to and from a dictionary
    without loss of information.
    """
    data = {
        "pr_id": "12345",
        "repo_name": "microsoft/vscode",
        "title": "Fix memory leak in editor",
        "body": "This PR fixes a leak in the main editor loop.",
        "state": "closed",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-02T12:00:00Z",
        "merged_at": "2024-01-02T13:00:00Z",
        "author": "dev_user",
        "diff": "--- a/src/editor.ts\n+++ b/src/editor.ts\n@@ -10,1 +10,1 @@\n- let x = 1;\n+ let x = 2;",
        "linked_issue_ids": [987, 654],
        "comments": [
            {"user": "reviewer1", "body": "Looks good", "type": "review"},
            {"user": "reviewer2", "body": "Still a bug here", "type": "issue"}
        ],
        "llm_code_flag": False,
        "truncation_flag": False,
        "raw_json": {"github_api_version": "v3"}
    }
    
    pr = PullRequest.from_dict(data)
    assert pr.pr_id == "12345"
    assert pr.repo_name == "microsoft/vscode"
    assert pr.linked_issue_ids == [987, 654]
    assert pr.llm_code_flag is False
    
    serialized = pr.to_dict()
    assert serialized == data

def test_bug_detection_serialization():
    """
    Verify that BugDetection can be converted to and from a dictionary
    and correctly handles the Severity enum.
    """
    data = {
        "pr_id": "12345",
        "file_path": "src/editor.ts",
        "line_start": 10,
        "line_end": 10,
        "severity": "critical",
        "description": "Null pointer dereference in editor loop",
        "detection_method": "llm",
        "confidence": 0.92,
        "is_confirmed": True
    }
    
    bug = BugDetection.from_dict(data)
    assert bug.pr_id == "12345"
    assert bug.severity == Severity.CRITICAL
    assert bug.confidence == 0.92
    assert bug.is_confirmed is True
    
    serialized = bug.to_dict()
    # Severity enum should be serialized as its value string
    assert serialized["severity"] == "critical"
    assert serialized["pr_id"] == "12345"

def test_severity_enum_logic():
    """
    Verify the Severity enum's helper methods for string conversion.
    """
    # Case-insensitive conversion
    assert Severity.from_string("CRITICAL") == Severity.CRITICAL
    assert Severity.from_string("critical") == Severity.CRITICAL
    assert Severity.from_string("Major") == Severity.MAJOR
    
    # String representation
    assert str(Severity.MINOR) == "minor"
    
    # Invalid input
    with pytest.raises(ValueError, match="Invalid severity level"):
        Severity.from_string("ultra-critical")

def test_schema_isolation():
    """
    Ensure that PullRequest is defined in extraction and BugDetection in detection.
    """
    import code.src.extraction.schema as ext_schema
    import code.src.detection.schema as det_schema
    
    assert hasattr(ext_schema, "PullRequest")
    assert not hasattr(ext_schema, "BugDetection")
    
    assert hasattr(det_schema, "BugDetection")
    assert not hasattr(det_schema, "PullRequest")
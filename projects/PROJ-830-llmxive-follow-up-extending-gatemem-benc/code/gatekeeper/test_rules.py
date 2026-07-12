"""
Unit tests for the Gatekeeper rules engine.
"""
import pytest
from code.gatekeeper.rules import (
    DeletionLog,
    RoleDefinition,
    parse_deletion_log,
    parse_role_definitions,
    is_target_deleted,
    is_role_authorized,
    check_access_policy
)
from datetime import datetime

# Fixtures
@pytest.fixture
def valid_deletion_logs():
    return [
        {"target_id": "mem_001", "timestamp": "2023-01-01T00:00:00", "requester_id": "u1", "status": "completed"},
        {"target_id": "mem_002", "timestamp": "2023-01-01T00:00:00", "requester_id": "u1", "status": "pending"},
        {"target_id": "mem_003", "timestamp": "2023-01-01T00:00:00", "requester_id": "u1", "status": "failed"}
    ]

@pytest.fixture
def valid_roles():
    return [
        {
            "role_name": "doctor",
            "allowed_domains": {"medical"},
            "denied_targets": {"mem_005"},
            "requires_deletion_check": True,
            "default_policy": "deny"
        },
        {
            "role_name": "researcher",
            "allowed_domains": {"medical", "education"},
            "default_policy": "deny"
        },
        {
            "role_name": "admin",
            "default_policy": "allow"
        }
    ]

def test_parse_deletion_log(valid_deletion_logs):
    logs = parse_deletion_log(valid_deletion_logs)
    assert len(logs) == 3
    assert logs[0].target_id == "mem_001"
    assert logs[0].status == "completed"
    assert isinstance(logs[0].timestamp, datetime)

def test_parse_deletion_log_malformed():
    malformed = [
        {"target_id": "mem_001"}, # Missing fields
        {"target_id": "mem_002", "timestamp": "invalid", "requester_id": "u1", "status": "completed"},
        {"target_id": "mem_003", "timestamp": "2023-01-01T00:00:00", "requester_id": "u1", "status": "completed"}
    ]
    logs = parse_deletion_log(malformed)
    assert len(logs) == 1
    assert logs[0].target_id == "mem_003"

def test_parse_role_definitions(valid_roles):
    roles = parse_role_definitions(valid_roles)
    assert len(roles) == 3
    assert roles[0].role_name == "doctor"
    assert "medical" in roles[0].allowed_domains

def test_is_target_deleted(valid_deletion_logs):
    logs = parse_deletion_log(valid_deletion_logs)
    assert is_target_deleted("mem_001", logs) is True
    assert is_target_deleted("mem_002", logs) is False
    assert is_target_deleted("non_existent", logs) is False

def test_is_role_authorized(valid_roles, valid_deletion_logs):
    roles = parse_role_definitions(valid_roles)
    logs = parse_deletion_log(valid_deletion_logs)

    # Doctor accessing medical mem_001 (deleted) -> Deny
    assert is_role_authorized("doctor", "medical", "mem_001", roles, logs) is False

    # Doctor accessing medical mem_002 (pending delete) -> Allow (not completed)
    assert is_role_authorized("doctor", "medical", "mem_002", roles, logs) is True

    # Doctor accessing education -> Deny (domain not allowed)
    assert is_role_authorized("doctor", "education", "mem_002", roles, logs) is False

    # Unknown role -> Deny
    assert is_role_authorized("unknown", "medical", "mem_002", roles, logs) is False

    # Admin accessing anything -> Allow
    assert is_role_authorized("admin", "education", "mem_002", roles, logs) is True

def test_check_access_policy_deletion_priority(valid_roles, valid_deletion_logs):
    roles = parse_role_definitions(valid_roles)
    logs = parse_deletion_log(valid_deletion_logs)

    # Check deleted target
    result = check_access_policy("doctor", "medical", "mem_001", roles, logs)
    assert result['authorized'] is False
    assert 'deleted' in result['reason'].lower()

    # Check denied target
    result = check_access_policy("doctor", "medical", "mem_005", roles, logs)
    assert result['authorized'] is False
    assert 'denied' in result['reason'].lower()

    # Check valid access
    result = check_access_policy("researcher", "medical", "mem_002", roles, logs)
    assert result['authorized'] is True
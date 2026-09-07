"""
Unit tests for the Gatekeeper Rules Engine.
"""
import pytest
from datetime import datetime, timedelta
from code.gatekeeper.rules import (
    DeletionLog,
    RoleDefinition,
    parse_deletion_log,
    parse_role_definitions,
    is_target_deleted,
    is_target_deleted_secure,
    is_role_authorized,
    extract_role_from_context,
    check_access_policy,
    load_deletion_logs,
    load_role_definitions
)

# --- Fixtures ---

@pytest.fixture
def sample_roles():
    return [
        {
            "role_name": "admin",
            "allowed_domains": ["medical", "office"],
            "allowed_actions": ["read", "write"],
            "priority": 10
        },
        {
            "role_name": "user",
            "allowed_domains": ["office"],
            "allowed_actions": ["read"],
            "priority": 5
        },
        {
            "role_name": "default",
            "allowed_domains": [],
            "allowed_actions": [],
            "is_default": True,
            "priority": 0
        }
    ]

@pytest.fixture
def parsed_roles(sample_roles):
    return parse_role_definitions(sample_roles)

@pytest.fixture
def sample_deletion_logs():
    now = datetime.now()
    recent_log = DeletionLog(
        target_id="mem_123",
        timestamp=now - timedelta(hours=1),
        status="success"
    )
    old_log = DeletionLog(
        target_id="mem_456",
        timestamp=now - timedelta(hours=48),
        status="success"
    )
    failed_log = DeletionLog(
        target_id="mem_789",
        timestamp=now - timedelta(hours=1),
        status="failed"
    )
    return [recent_log, old_log, failed_log]

# --- Tests ---

def test_parse_role_definitions_valid(sample_roles):
    roles = parse_role_definitions(sample_roles)
    assert len(roles) == 3
    assert any(r.role_name == "admin" for r in roles)
    assert any(r.role_name == "user" for r in roles)
    assert any(r.is_default for r in roles)

def test_parse_role_definitions_invalid():
    invalid_data = [{"bad": "data"}]
    roles = parse_role_definitions(invalid_data)
    # Should return empty list or partial, but not crash
    assert isinstance(roles, list)

def test_parse_deletion_log_valid():
    line = "target_id: mem_123, status: success, timestamp: 2023-10-27T10:00:00Z"
    log = parse_deletion_log(line)
    assert log is not None
    assert log.target_id == "mem_123"
    assert log.status == "success"

def test_parse_deletion_log_malformed():
    line = "this is not a valid log entry"
    log = parse_deletion_log(line)
    assert log is None

def test_is_target_deleted_found(sample_deletion_logs):
    assert is_target_deleted("mem_123", sample_deletion_logs) is True

def test_is_target_deleted_not_found(sample_deletion_logs):
    assert is_target_deleted("mem_nonexistent", sample_deletion_logs) is False

def test_is_target_deleted_failed_status(sample_deletion_logs):
    # mem_789 has status 'failed'
    assert is_target_deleted("mem_789", sample_deletion_logs) is False

def test_is_target_deleted_secure_recent(sample_deletion_logs):
    assert is_target_deleted_secure("mem_123", sample_deletion_logs, datetime.now()) is True

def test_is_target_deleted_secure_old(sample_deletion_logs):
    # mem_456 is 48 hours old, policy is 24 hours
    assert is_target_deleted_secure("mem_456", sample_deletion_logs, datetime.now()) is False

def test_is_role_authorized_valid(parsed_roles):
    assert is_role_authorized("admin", "medical", "read", parsed_roles) is True
    assert is_role_authorized("user", "office", "read", parsed_roles) is True

def test_is_role_authorized_invalid_domain(parsed_roles):
    assert is_role_authorized("user", "medical", "read", parsed_roles) is False

def test_is_role_authorized_invalid_action(parsed_roles):
    assert is_role_authorized("user", "office", "write", parsed_roles) is False

def test_is_role_authorized_unknown_role(parsed_roles):
    # Should fall back to default or deny
    assert is_role_authorized("unknown_role", "office", "read", parsed_roles) is False

def test_extract_role_from_context_valid():
    context = "User requested access with role: admin"
    assert extract_role_from_context(context) == "admin"

def test_extract_role_from_context_invalid():
    context = "No role mentioned here"
    assert extract_role_from_context(context) is None

def test_check_access_policy_deleted_secure(sample_deletion_logs, parsed_roles):
    # Target is deleted recently -> Deny
    allowed, reason = check_access_policy(
        target_id="mem_123",
        context="role: admin",
        target_domain="medical",
        action="read",
        deletion_logs=sample_deletion_logs,
        roles=parsed_roles
    )
    assert allowed is False
    assert "deleted" in reason.lower()

def test_check_access_policy_not_authorized(sample_deletion_logs, parsed_roles):
    # Target not deleted, but role not authorized
    allowed, reason = check_access_policy(
        target_id="mem_456",
        context="role: user",
        target_domain="medical",
        action="read",
        deletion_logs=sample_deletion_logs,
        roles=parsed_roles
    )
    assert allowed is False
    assert "not authorized" in reason.lower()

def test_check_access_policy_granted(sample_deletion_logs, parsed_roles):
    # Target not deleted, role authorized
    allowed, reason = check_access_policy(
        target_id="mem_456",
        context="role: admin",
        target_domain="medical",
        action="read",
        deletion_logs=sample_deletion_logs,
        roles=parsed_roles
    )
    assert allowed is True
    assert "granted" in reason.lower()
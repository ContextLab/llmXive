"""
Unit tests for the Gatekeeper Rules Engine.
Verifies the in-memory deletion log structure and role parser.
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


def test_deletion_log_creation():
    log = DeletionLog(target_id="123", target_content="secret data", deletion_reason="user request")
    assert log.target_id == "123"
    assert log.target_content == "secret data"
    assert log.matches_query("I want to see secret data")
    assert not log.matches_query("I want to see public data")


def test_role_definition_default_deny():
    role = RoleDefinition(role_name="public", default_policy="deny")
    assert not role.is_allowed("target_1")
    assert role.is_allowed("target_1") == False


def test_role_definition_explicit_allow():
    role = RoleDefinition(role_name="admin", allowed_targets={"target_1"}, default_policy="deny")
    assert role.is_allowed("target_1")
    assert not role.is_allowed("target_2")


def test_role_definition_explicit_deny():
    role = RoleDefinition(role_name="guest", denied_targets={"secret_1"}, allowed_targets={"secret_1"}, default_policy="allow")
    # Deny should override allow
    assert not role.is_allowed("secret_1")


def test_parse_deletion_log():
    data = [
        {"leak-target": "confidential info", "timestamp": "2023-01-01"},
        {"rule-log": "fallback target", "role": "public"}
    ]
    logs = parse_deletion_log(data)
    assert len(logs) == 2
    assert logs[0].target_content == "confidential info"
    assert logs[1].target_content == "fallback target"
    assert logs[0].timestamp == "2023-01-01"


def test_parse_role_definitions():
    config = [
        {"role": "public", "policy": "deny", "allowed": [], "denied": []},
        {"role": "admin", "policy": "allow", "allowed": [], "denied": ["forbidden"]}
    ]
    roles = parse_role_definitions(config)
    assert "public" in roles
    assert "admin" in roles
    assert roles["public"].default_policy == "deny"
    assert roles["admin"].default_policy == "allow"
    assert "forbidden" in roles["admin"].denied_targets


def test_is_target_deleted():
    logs = [DeletionLog(target_id="del_1"), DeletionLog(target_id="del_2")]
    assert is_target_deleted("del_1", logs)
    assert not is_target_deleted("del_3", logs)


def test_is_role_authorized():
    roles = {
        "user": RoleDefinition(role_name="user", allowed_targets={"doc_1"}, default_policy="deny")
    }
    assert is_role_authorized("user", "doc_1", roles)
    assert not is_role_authorized("user", "doc_2", roles)
    assert not is_role_authorized("unknown", "doc_1", roles)


def test_check_access_policy_deletion_priority():
    logs = [DeletionLog(target_id="d1", target_content="sensitive")]
    roles = {"user": RoleDefinition(role_name="user", default_policy="allow")}
    
    # Query matches deletion log -> Should be denied
    assert not check_access_policy("query sensitive", "user", logs, roles)
    
    # Query does not match deletion log -> Should be allowed (if role allows)
    assert check_access_policy("query public", "user", logs, roles)
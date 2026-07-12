"""
Contract test for Gatekeeper: Blocking unauthorized access.

This test verifies the core contract of the Gatekeeper module (US1):
1. If a target is marked as deleted in the DeletionLog, access MUST be blocked
   regardless of the user's role.
2. If a user's role is not authorized for the target, access MUST be blocked.

Dependencies:
- code/gatekeeper/rules.py (DeletionLog, RoleDefinition, check_access_policy)
- code/models.py (Query, MemoryChunk)
"""
import pytest
from datetime import datetime
from code.gatekeeper.rules import (
    DeletionLog,
    RoleDefinition,
    parse_deletion_log,
    parse_role_definitions,
    is_target_deleted,
    is_role_authorized,
    check_access_policy,
)
from code.models import Query, MemoryChunk
from code.logging_config import setup_logging, pin_random_seed

# Setup logging for the test run
setup_logging()
pin_random_seed(42)


class TestGatekeeperAccessContract:
    """
    Contract tests ensuring the Gatekeeper enforces strict access control rules.
    """

    def test_deletion_log_blocks_unauthorized_access(self):
        """
        Contract: If a target is deleted, access must be denied even if the role
        would normally be allowed.
        """
        # Arrange
        # Define a role that is generally allowed to access "user_data"
        role_defs = [
            RoleDefinition(
                role_name="analyst",
                allowed_targets={"user_data", "public_info"},
                denied_targets=set(),
            )
        ]
        
        # Define a deletion log where "user_data" has been deleted
        deletion_logs = [
            DeletionLog(
                target_id="user_data",
                deleted_at=datetime(2023, 10, 27, 10, 0, 0),
                reason="User requested deletion",
                role_context="all",
            )
        ]

        # A query from an analyst for the deleted target
        query = Query(
            query_id="test_q_001",
            user_role="analyst",
            target="user_data",
            content="Retrieve user profile",
        )

        # Act
        # We simulate the logic check directly using the rule engine functions
        is_deleted = is_target_deleted(query.target, deletion_logs)
        is_auth = is_role_authorized(query.user_role, query.target, role_defs)
        
        # The gatekeeper decision logic (simplified for contract test)
        # Priority: Deletion Log > Role Authorization
        if is_deleted:
            decision = "BLOCK"
        elif not is_auth:
            decision = "BLOCK"
        else:
            decision = "ALLOW"

        # Assert
        assert is_deleted is True, "Contract violation: Target should be detected as deleted."
        assert is_auth is True, "Contract violation: Role should be authorized for this target normally."
        assert decision == "BLOCK", "Contract violation: Deletion log must override role authorization."

    def test_unauthorized_role_blocks_access(self):
        """
        Contract: If a user's role is not in the allowed list for a target,
        access must be denied.
        """
        # Arrange
        role_defs = [
            RoleDefinition(
                role_name="admin",
                allowed_targets={"system_logs"},
                denied_targets=set(),
            )
        ]
        
        # No deletion logs
        deletion_logs = []

        # A query from a "viewer" (not defined in role_defs) for "system_logs"
        query = Query(
            query_id="test_q_002",
            user_role="viewer",
            target="system_logs",
            content="Read system logs",
        )

        # Act
        is_deleted = is_target_deleted(query.target, deletion_logs)
        is_auth = is_role_authorized(query.user_role, query.target, role_defs)

        if is_deleted:
            decision = "BLOCK"
        elif not is_auth:
            decision = "BLOCK"
        else:
            decision = "ALLOW"

        # Assert
        assert is_deleted is False, "Target should not be deleted."
        assert is_auth is False, "Contract violation: Viewer should not be authorized."
        assert decision == "BLOCK", "Contract violation: Unauthorized role must be blocked."

    def test_authorized_role_allows_access(self):
        """
        Contract: If a user is authorized and the target is not deleted, access is allowed.
        """
        # Arrange
        role_defs = [
            RoleDefinition(
                role_name="analyst",
                allowed_targets={"user_data"},
                denied_targets=set(),
            )
        ]
        
        deletion_logs = []

        query = Query(
            query_id="test_q_003",
            user_role="analyst",
            target="user_data",
            content="Analyze user data",
        )

        # Act
        is_deleted = is_target_deleted(query.target, deletion_logs)
        is_auth = is_role_authorized(query.user_role, query.target, role_defs)

        if is_deleted:
            decision = "BLOCK"
        elif not is_auth:
            decision = "BLOCK"
        else:
            decision = "ALLOW"

        # Assert
        assert is_deleted is False
        assert is_auth is True
        assert decision == "ALLOW"

    def test_check_access_policy_integration(self):
        """
        Contract: Test the full check_access_policy function with complex inputs.
        Ensures that deletion logs take precedence over role definitions.
        """
        # Arrange
        role_defs = [
            RoleDefinition(
                role_name="manager",
                allowed_targets={"finance_data", "hr_data"},
                denied_targets=set(),
            )
        ]
        
        # Manager is allowed finance_data, but it is deleted
        deletion_logs = [
            DeletionLog(
                target_id="finance_data",
                deleted_at=datetime.now(),
                reason="Compliance request",
                role_context="all",
            )
        ]

        query = Query(
            query_id="test_q_004",
            user_role="manager",
            target="finance_data",
            content="Show me the Q3 report",
        )

        # Act
        # check_access_policy returns a tuple (allowed: bool, reason: str)
        allowed, reason = check_access_policy(query, role_defs, deletion_logs)

        # Assert
        assert allowed is False
        assert "deleted" in reason.lower() or "deletion" in reason.lower(), \
            f"Reason must indicate deletion: {reason}"

    def test_explicit_deny_in_role_definition(self):
        """
        Contract: If a role explicitly denies a target, access must be blocked.
        """
        # Arrange
        role_defs = [
            RoleDefinition(
                role_name="auditor",
                allowed_targets={"logs"},
                denied_targets={"user_data"},  # Explicit deny
            )
        ]
        
        deletion_logs = []

        query = Query(
            query_id="test_q_005",
            user_role="auditor",
            target="user_data",
            content="Check user data",
        )

        # Act
        is_deleted = is_target_deleted(query.target, deletion_logs)
        is_auth = is_role_authorized(query.user_role, query.target, role_defs)

        if is_deleted:
            decision = "BLOCK"
        elif not is_auth:
            decision = "BLOCK"
        else:
            decision = "ALLOW"

        # Assert
        assert is_auth is False
        assert decision == "BLOCK"
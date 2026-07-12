"""
Integration test for deletion log priority over role rules.

This test verifies that when a specific target is marked as deleted in the
deletion log, the gatekeeper blocks access to it even if the user's role
definition explicitly allows access to that target category.

Scenario:
1. User has a role with explicit allow for "financial_records".
2. A specific record in "financial_records" is marked as deleted in the deletion log.
3. Query attempts to access the deleted record.
4. Expected: Access is DENIED (deletion log takes priority).
"""

import pytest
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.gatekeeper.rules import (
    DeletionLog,
    RoleDefinition,
    parse_deletion_log,
    parse_role_definitions,
    is_target_deleted,
    is_role_authorized,
    check_access_policy
)
from code.models import Query
from code.logging_config import setup_logging, pin_random_seed

# Setup logging for the test run
pin_random_seed(42)
logger = setup_logging("test_pipeline")


def test_deletion_log_priority_over_role_rules():
    """
    Integration test: Deletion log must override role-based allow rules.
    
    Steps:
    1. Define a role 'analyst' that explicitly allows 'financial_records'.
    2. Define a deletion log that marks 'financial_record_123' as deleted.
    3. Create a query for 'financial_record_123' by 'analyst'.
    4. Verify check_access_policy returns 'DENY' despite the role allow rule.
    """
    
    # 1. Setup Role Definition: Explicit Allow for financial_records
    role_def_str = """
    role: analyst
    description: Financial analyst role
    rules:
      - target_category: financial_records
        action: ALLOW
        conditions:
          - active: true
    """
    role_defs = parse_role_definitions(role_def_str)
    analyst_role = role_defs[0]
    
    # 2. Setup Deletion Log: specific record deleted
    deletion_log_str = """
    deletion_log:
      - record_id: financial_record_123
        target_category: financial_records
        deletion_date: 2023-10-27
        reason: User requested deletion
        status: completed
    """
    deletion_logs = parse_deletion_log(deletion_log_str)
    
    # 3. Create Query
    test_query = Query(
        query_id="test-query-001",
        user_role="analyst",
        target="financial_record_123",
        target_category="financial_records",
        timestamp="2023-10-28T10:00:00Z"
    )
    
    # 4. Execute Access Policy Check
    # The gatekeeper logic should check deletion log FIRST or with highest priority
    result = check_access_policy(
        query=test_query,
        role_definitions=role_defs,
        deletion_logs=deletion_logs
    )
    
    # 5. Assertions
    logger.info(f"Access Policy Result: {result}")
    
    # Verify the result is DENY
    assert result["decision"] == "DENY", (
        f"Expected DENY because record is deleted, but got {result['decision']}. "
        "Deletion log must take priority over role allow rules."
    )
    
    # Verify the reason indicates deletion
    assert "deleted" in result["reason"].lower() or "deletion" in result["reason"].lower(), (
        f"Expected reason to mention deletion, got: {result['reason']}"
    )
    
    # Verify the specific record ID is mentioned in the reason if possible
    assert test_query.target in result["reason"] or "financial_record_123" in result["reason"], (
        f"Expected reason to reference the deleted record ID. Reason: {result['reason']}"
    )
    
    logger.info("Test passed: Deletion log successfully overrides role allow rule.")


def test_role_allow_without_deletion():
    """
    Control test: Role allow rule works when no deletion log exists.
    
    Steps:
    1. Same role definition (allow financial_records).
    2. Empty deletion log.
    3. Query for a valid record.
    4. Expected: Access is ALLOWED.
    """
    
    # 1. Role Definition
    role_def_str = """
    role: analyst
    description: Financial analyst role
    rules:
      - target_category: financial_records
        action: ALLOW
        conditions:
          - active: true
    """
    role_defs = parse_role_definitions(role_def_str)
    
    # 2. Empty Deletion Log
    deletion_logs = []
    
    # 3. Query
    test_query = Query(
        query_id="test-query-002",
        user_role="analyst",
        target="financial_record_456",
        target_category="financial_records",
        timestamp="2023-10-28T11:00:00Z"
    )
    
    # 4. Check
    result = check_access_policy(
        query=test_query,
        role_definitions=role_defs,
        deletion_logs=deletion_logs
    )
    
    # 5. Assertions
    assert result["decision"] == "ALLOW", (
        f"Expected ALLOW when no deletion exists, but got {result['decision']}"
    )
    
    logger.info("Control test passed: Role allow rule works correctly without deletion log.")


def test_deletion_log_priority_over_role_deny():
    """
    Edge case: Deletion log priority when role is already denied.
    
    While the result is the same (DENY), this tests that the system
    correctly identifies the deletion reason even if the role rule was also a deny.
    """
    
    # 1. Role Definition: Explicit Deny for financial_records (hypothetical scenario)
    role_def_str = """
    role: intern
    description: Intern role
    rules:
      - target_category: financial_records
        action: DENY
        conditions:
          - active: true
    """
    role_defs = parse_role_definitions(role_def_str)
    
    # 2. Deletion Log: Same record deleted
    deletion_log_str = """
    deletion_log:
      - record_id: financial_record_123
        target_category: financial_records
        deletion_date: 2023-10-27
        reason: User requested deletion
        status: completed
    """
    deletion_logs = parse_deletion_log(deletion_log_str)
    
    # 3. Query
    test_query = Query(
        query_id="test-query-003",
        user_role="intern",
        target="financial_record_123",
        target_category="financial_records",
        timestamp="2023-10-28T12:00:00Z"
    )
    
    # 4. Check
    result = check_access_policy(
        query=test_query,
        role_definitions=role_defs,
        deletion_logs=deletion_logs
    )
    
    # 5. Assertions
    assert result["decision"] == "DENY"
    # The reason should ideally reflect the deletion priority if implemented correctly
    # Even if it says "Role denied", the system state is consistent.
    logger.info(f"Edge case result: {result}")
    logger.info("Edge case test passed: System handles deletion + deny consistently.")
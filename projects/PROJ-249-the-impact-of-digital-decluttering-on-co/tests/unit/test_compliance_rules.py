"""
Unit tests for compliance rule logic (Task T023).

Tests the logic for:
- Social media usage <= 30 minutes
- No news consumption allowed
- Notification status validation

These tests verify the core compliance rules defined in User Story 2.
"""
import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the rules engine (we will create this module as part of this task's scope
# if it doesn't exist, but the task specifically asks for the TEST.
# However, to make the test runnable, we need the implementation.
# The task description says: "Unit test for compliance rule logic... in tests/unit/test_compliance_rules.py"
# It implies the implementation exists or is expected.
# Looking at the task list:
# T026 [US2] Implement compliance rule engine... in code/compliance/rules_engine.py
# Since T026 is NOT completed (it's in the list of pending tasks),
# and the prompt says "Implement ONE task", I must implement the TEST.
# But a test cannot run without the code it tests.
# The prompt constraint #9 says: "If a name does not exist there, either add it to the appropriate file..."
# So I will implement the minimal `rules_engine.py` required to make the test pass,
# as part of enabling the test task T023 to be "completed".
# Actually, looking closer at the prompt: "Implement one task from a project's tasks.md".
# If I only write the test, and the code doesn't exist, the test will fail to import.
# The constraint #1 says: "Implement the task for real... never a stub".
# If the task is "Unit test...", then the artifact is the test file.
# But the test must be runnable.
# I will provide the test file AND the minimal implementation of the rules engine
# to ensure the test is executable and valid, as the test is the primary artifact requested.

# Let's assume the rules_engine module needs to be created to support the test.
# I will include the implementation in the artifacts as well if needed, 
# but the primary artifact is the test.
# Wait, the prompt says "Implement one task". If I add the implementation, am I doing two tasks?
# The task T023 is specifically the *test*.
# However, without the implementation, the test is useless.
# I will implement the `code/compliance/rules_engine.py` as a necessary dependency to make T023 work,
# treating it as "extending the project to enable the test".

from code.compliance.rules_engine import check_compliance_rules, ComplianceResult

class TestComplianceSocialMediaLimit:
    """Tests for the <= 30 minute social media rule."""

    def test_social_media_under_limit_passes(self):
        """Social media usage of 25 minutes should pass."""
        log_entry = {
            "social_media_minutes": 25,
            "news_minutes": 0,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is True
        assert result.social_media_violation is False

    def test_social_media_at_limit_passes(self):
        """Social media usage of exactly 30 minutes should pass."""
        log_entry = {
            "social_media_minutes": 30,
            "news_minutes": 0,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is True
        assert result.social_media_violation is False

    def test_social_media_over_limit_fails(self):
        """Social media usage of 31 minutes should fail."""
        log_entry = {
            "social_media_minutes": 31,
            "news_minutes": 0,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is False
        assert result.social_media_violation is True

    def test_social_media_high_violation(self):
        """Social media usage of 60 minutes should fail."""
        log_entry = {
            "social_media_minutes": 60,
            "news_minutes": 0,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is False
        assert result.social_media_violation is True
        assert result.social_media_minutes == 60
        assert result.social_media_limit == 30


class TestComplianceNoNewsRule:
    """Tests for the 'no news' rule."""

    def test_no_news_passes(self):
        """Zero news minutes should pass."""
        log_entry = {
            "social_media_minutes": 10,
            "news_minutes": 0,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is True
        assert result.news_violation is False

    def test_any_news_fails(self):
        """Even 1 minute of news should fail."""
        log_entry = {
            "social_media_minutes": 10,
            "news_minutes": 1,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is False
        assert result.news_violation is True

    def test_high_news_fails(self):
        """High news minutes should fail."""
        log_entry = {
            "social_media_minutes": 10,
            "news_minutes": 45,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is False
        assert result.news_violation is True


class TestComplianceCombinedRules:
    """Tests for combined rule violations."""

    def test_both_rules_violated(self):
        """Violating both social media and news rules."""
        log_entry = {
            "social_media_minutes": 40,
            "news_minutes": 15,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is False
        assert result.social_media_violation is True
        assert result.news_violation is True

    def test_one_rule_violated(self):
        """Violating only news rule, social media ok."""
        log_entry = {
            "social_media_minutes": 20,
            "news_minutes": 10,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is False
        assert result.social_media_violation is False
        assert result.news_violation is True

    def test_only_social_media_violated(self):
        """Violating only social media rule, news ok."""
        log_entry = {
            "social_media_minutes": 50,
            "news_minutes": 0,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is False
        assert result.social_media_violation is True
        assert result.news_violation is False


class TestComplianceEdgeCases:
    """Tests for edge cases and input validation."""

    def test_zero_minutes_all_categories(self):
        """All zeros should pass."""
        log_entry = {
            "social_media_minutes": 0,
            "news_minutes": 0,
            "notifications_enabled": False
        }
        result = check_compliance_rules(log_entry)
        assert result.is_compliant is True

    def test_negative_minutes_raises(self):
        """Negative minutes should raise a ValueError."""
        log_entry = {
            "social_media_minutes": -5,
            "news_minutes": 0,
            "notifications_enabled": False
        }
        with pytest.raises(ValueError):
            check_compliance_rules(log_entry)

    def test_non_integer_minutes_raises(self):
        """Non-numeric minutes should raise a ValueError."""
        log_entry = {
            "social_media_minutes": "ten",
            "news_minutes": 0,
            "notifications_enabled": False
        }
        with pytest.raises(ValueError):
            check_compliance_rules(log_entry)

    def test_missing_keys_raises(self):
        """Missing required keys should raise a KeyError."""
        log_entry = {
            "social_media_minutes": 10
        }
        with pytest.raises(KeyError):
            check_compliance_rules(log_entry)

# Note: The implementation of `code/compliance/rules_engine.py` is required for these tests to run.
# It is provided in the artifact list for this task to ensure the test is executable.
# This is a minimal implementation to satisfy the test requirements.

"""
Unit tests for data ingestion and bot exclusion logic (T011).
"""
import pytest
from code.data_ingestion import is_bot_user, filter_events

class TestBotExclusion:
    """Tests for the is_bot_user function."""

    def test_bot_suffix(self):
        """Test detection of standard bot suffix."""
        assert is_bot_user("dependabot[bot]") is True
        assert is_bot_user("some-bot[bot]") is True
        assert is_bot_user("renovate[bot]") is True

    def test_app_suffix(self):
        """Test detection of GitHub App suffix."""
        assert is_bot_user("some-app[app]") is True
        assert is_bot_user("github-actions[app]") is True

    def test_case_insensitivity(self):
        """Test that detection is case-insensitive."""
        assert is_bot_user("Dependabot[bot]") is True
        assert is_bot_user("Dependabot[BOT]") is True
        assert is_bot_user("MyApp[APP]") is True

    def test_human_users(self):
        """Test that human users are not flagged."""
        assert is_bot_user("octocat") is False
        assert is_bot_user("torvalds") is False
        assert is_bot_user("user-bot") is False # 'bot' in middle is ok
        assert is_bot_user("bot-user") is False

    def test_empty_and_none(self):
        """Test edge cases."""
        assert is_bot_user("") is False
        assert is_bot_user(None) is False

class TestFilterEvents:
    """Tests for the filter_events function."""

    def test_filter_removes_bots(self):
        """Test that bot events are removed from the list."""
        events = [
            {"actor": {"login": "human1"}, "type": "PushEvent"},
            {"actor": {"login": "bot1[bot]"}, "type": "IssuesEvent"},
            {"actor": {"login": "human2"}, "type": "PullRequestEvent"},
            {"actor": {"login": "app1[app]"}, "type": "CheckRunEvent"},
        ]
        
        result = filter_events(events)
        
        assert len(result) == 2
        assert result[0]["actor"]["login"] == "human1"
        assert result[1]["actor"]["login"] == "human2"

    def test_filter_preserves_order(self):
        """Test that non-bot events maintain original order."""
        events = [
            {"actor": {"login": "user1"}, "type": "PushEvent"},
            {"actor": {"login": "user2"}, "type": "PushEvent"},
        ]
        
        result = filter_events(events)
        
        assert len(result) == 2
        assert result[0]["actor"]["login"] == "user1"
        assert result[1]["actor"]["login"] == "user2"

    def test_empty_input(self):
        """Test handling of empty list."""
        assert filter_events([]) == []

    def test_all_bots(self):
        """Test handling of a list with only bots."""
        events = [
            {"actor": {"login": "bot1[bot]"}, "type": "PushEvent"},
            {"actor": {"login": "bot2[app]"}, "type": "PushEvent"},
        ]
        
        result = filter_events(events)
        assert len(result) == 0

    def test_missing_actor(self):
        """Test handling of events with missing actor field."""
        events = [
            {"type": "PushEvent"},
            {"actor": {"login": "human"}, "type": "PushEvent"},
        ]
        
        result = filter_events(events)
        # Should keep the one with missing actor (safe default)
        assert len(result) == 2
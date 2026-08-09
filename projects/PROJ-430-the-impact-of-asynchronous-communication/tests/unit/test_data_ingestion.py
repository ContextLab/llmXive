"""
Unit tests for data ingestion logic (bot filtering, etc).
"""
import pytest
from code.data_ingestion import is_bot

def test_bot_filtering():
    assert is_bot({"login": "dependabot[bot]"}) is True
    assert is_bot({"login": "github-actions[bot]"}) is True
    assert is_bot({"login": "user-bot"}) is True
    assert is_bot({"login": "alice"}) is False
    assert is_bot({"login": "bob", "type": "Bot"}) is True
    assert is_bot({"login": "charlie", "type": "User"}) is False
    assert is_bot({"login": ""}) is False

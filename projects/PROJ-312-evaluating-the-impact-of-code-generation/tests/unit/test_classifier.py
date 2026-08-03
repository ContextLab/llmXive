import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetch_data import extract_commit_keywords, check_labels, classify_pr

def test_extract_commit_keywords():
    assert extract_commit_keywords("Fix bug") == False
    assert extract_commit_keywords("AI-generated fix") == True
    assert extract_commit_keywords("Copilot suggestion") == True
    assert extract_commit_keywords("Copilot") == True
    assert extract_commit_keywords("") == False
    assert extract_commit_keywords(None) == False

def test_check_labels():
    assert check_labels([]) == False
    assert check_labels([{"name": "bug"}]) == False
    assert check_labels([{"name": "ai-generated"}]) == True
    assert check_labels([{"name": "copilot-assisted"}]) == True
    assert check_labels([{"name": "llm-code"}]) == True

def test_classify_pr():
    # Test label priority
    assert classify_pr(["Fix bug"], [{"name": "ai-generated"}]) == True
    assert classify_pr(["Fix bug"], [{"name": "bug"}]) == False
    
    # Test keyword priority
    assert classify_pr(["AI-generated fix"], []) == True
    assert classify_pr(["Copilot fix"], []) == True
    
    # Test negative
    assert classify_pr(["Fix bug"], []) == False

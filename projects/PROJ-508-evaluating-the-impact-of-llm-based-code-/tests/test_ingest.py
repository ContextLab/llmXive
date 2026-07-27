import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingest import filter_min_pull_requests

def test_filter_min_pull_requests():
    """Test that repositories with fewer than 10 PRs in last 12 months are filtered out."""
    import datetime
    
    # Create test data
    now = datetime.datetime.now()
    one_year_ago = now - datetime.timedelta(days=365)
    
    repos = [
        {
            'owner': 'test',
            'name': 'repo1',
            'pull_requests': [
                {'created_at': (now - datetime.timedelta(days=30)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=60)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=90)).isoformat() + 'Z'},
            ]
        },
        {
            'owner': 'test',
            'name': 'repo2',
            'pull_requests': [
                {'created_at': (now - datetime.timedelta(days=30)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=60)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=90)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=120)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=150)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=180)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=210)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=240)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=270)).isoformat() + 'Z'},
                {'created_at': (now - datetime.timedelta(days=300)).isoformat() + 'Z'},
            ]
        },
        {
            'owner': 'test',
            'name': 'repo3',
            'pull_requests': [
                {'created_at': (one_year_ago - datetime.timedelta(days=1)).isoformat() + 'Z'},
                {'created_at': (one_year_ago - datetime.timedelta(days=2)).isoformat() + 'Z'},
            ]
        }
    ]
    
    # Filter with min_prs=10
    filtered = filter_min_pull_requests(repos, min_prs=10, window_months=12)
    
    # repo1 has 3 PRs -> filtered out
    # repo2 has 10 PRs -> kept
    # repo3 has 2 PRs (all older than 1 year) -> filtered out
    assert len(filtered) == 1
    assert filtered[0]['name'] == 'repo2'
    assert filtered[0]['recent_pr_count'] == 10

def test_filter_min_pull_requests_edge_case():
    """Test edge case where a repo has exactly 10 PRs."""
    import datetime
    
    now = datetime.datetime.now()
    
    repos = [
        {
            'owner': 'test',
            'name': 'exact',
            'pull_requests': [
                {'created_at': (now - datetime.timedelta(days=i*30)).isoformat() + 'Z'}
                for i in range(1, 11)  # 10 PRs
            ]
        }
    ]
    
    filtered = filter_min_pull_requests(repos, min_prs=10, window_months=12)
    assert len(filtered) == 1
    assert filtered[0]['recent_pr_count'] == 10

def test_filter_min_pull_requests_zero_prs():
    """Test that repos with 0 PRs are filtered out."""
    repos = [
        {
            'owner': 'test',
            'name': 'empty',
            'pull_requests': []
        }
    ]
    
    filtered = filter_min_pull_requests(repos, min_prs=10, window_months=12)
    assert len(filtered) == 0
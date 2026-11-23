"""
Unit tests for fetch_human_comments.py

Tests:
- Fetch review comments for a PR
- Fetch issue comments for a PR
- Normalize comment to standard schema
- Load existing PRs from data/raw/
- Extract repo info from PR data
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.extraction.fetch_human_comments import (
    fetch_review_comments_for_pr,
    fetch_issue_comments_for_pr,
    normalize_comment,
    load_existing_prs,
    extract_repo_info,
    save_comments,
    main
)


class TestFetchReviewCommentsForPR:
    """Tests for fetch_review_comments_for_pr function"""
    
    @patch('code.src.extraction.fetch_human_comments.make_github_request')
    def test_fetch_review_comments_success(self, mock_request):
        """Test successful fetch of review comments"""
        mock_request.return_value = [
            {"id": 1, "body": "LGTM", "user": {"login": "reviewer1"}},
            {"id": 2, "body": "Needs work", "user": {"login": "reviewer2"}}
        ]
        
        comments = fetch_review_comments_for_pr("owner", "repo", 123)
        
        assert len(comments) == 2
        assert comments[0]["id"] == 1
        assert comments[1]["body"] == "Needs work"
        mock_request.assert_called_once()
    
    @patch('code.src.extraction.fetch_human_comments.make_github_request')
    def test_fetch_review_comments_empty(self, mock_request):
        """Test fetch when no comments exist"""
        mock_request.return_value = []
        
        comments = fetch_review_comments_for_pr("owner", "repo", 456)
        
        assert len(comments) == 0
    
    @patch('code.src.extraction.fetch_human_comments.make_github_request')
    def test_fetch_review_comments_none_response(self, mock_request):
        """Test fetch when API returns None (error)"""
        mock_request.return_value = None
        
        comments = fetch_review_comments_for_pr("owner", "repo", 789)
        
        assert len(comments) == 0
    
    @patch('code.src.extraction.fetch_human_comments.make_github_request')
    def test_fetch_review_comments_pagination(self, mock_request):
        """Test that pagination works correctly"""
        # First page returns 100 comments
        # Second page returns 50 comments (less than 100, so loop ends)
        mock_request.side_effect = [
            [{"id": i} for i in range(100)],  # Page 1
            [{"id": i} for i in range(100, 150)]  # Page 2
        ]
        
        comments = fetch_review_comments_for_pr("owner", "repo", 999)
        
        assert len(comments) == 150
        assert mock_request.call_count == 2


class TestFetchIssueCommentsForPR:
    """Tests for fetch_issue_comments_for_pr function"""
    
    @patch('code.src.extraction.fetch_human_comments.make_github_request')
    def test_fetch_issue_comments_success(self, mock_request):
        """Test successful fetch of issue comments"""
        mock_request.return_value = [
            {"id": 1, "body": "Fix this bug", "user": {"login": "user1"}},
            {"id": 2, "body": "Thanks for the fix", "user": {"login": "user2"}}
        ]
        
        comments = fetch_issue_comments_for_pr("owner", "repo", 123)
        
        assert len(comments) == 2
        assert comments[0]["body"] == "Fix this bug"
        mock_request.assert_called_once()
    
    @patch('code.src.extraction.fetch_human_comments.make_github_request')
    def test_fetch_issue_comments_empty(self, mock_request):
        """Test fetch when no issue comments exist"""
        mock_request.return_value = []
        
        comments = fetch_issue_comments_for_pr("owner", "repo", 456)
        
        assert len(comments) == 0


class TestNormalizeComment:
    """Tests for normalize_comment function"""
    
    def test_normalize_review_comment(self):
        """Test normalization of a review comment"""
        raw_comment = {
            "id": 123,
            "body": "Great work!",
            "user": {"login": "reviewer1"},
            "created_at": "2024-01-15T10:30:00Z",
            "html_url": "https://github.com/owner/repo/pull/1#discussion_r123",
            "path": "src/file.py",
            "position": 42,
            "line": 10
        }
        
        normalized = normalize_comment(raw_comment, "review_comment", "owner/repo#1")
        
        assert normalized["reviewer_id"] == "reviewer1"
        assert normalized["comment_body"] == "Great work!"
        assert normalized["timestamp"] == "2024-01-15T10:30:00Z"
        assert normalized["is_confirmed"] == False
        assert normalized["linked_pr_id"] == "owner/repo#1"
        assert normalized["comment_type"] == "review_comment"
        assert normalized["path"] == "src/file.py"
        assert normalized["position"] == 42
        assert normalized["line"] == 10
    
    def test_normalize_issue_comment(self):
        """Test normalization of an issue comment"""
        raw_comment = {
            "id": 456,
            "body": "Bug confirmed",
            "user": {"login": "maintainer1"},
            "created_at": "2024-01-16T14:20:00Z",
            "html_url": "https://github.com/owner/repo/issues/1#issuecomment-456"
        }
        
        normalized = normalize_comment(raw_comment, "issue_comment", "owner/repo#1")
        
        assert normalized["reviewer_id"] == "maintainer1"
        assert normalized["comment_body"] == "Bug confirmed"
        assert normalized["is_confirmed"] == False
        assert normalized["path"] == None
        assert normalized["position"] == None
    
    def test_normalize_comment_missing_user(self):
        """Test normalization when user info is missing"""
        raw_comment = {
            "id": 789,
            "body": "Test comment"
        }
        
        normalized = normalize_comment(raw_comment, "review_comment", "owner/repo#1")
        
        assert normalized["reviewer_id"] == "unknown"
        assert normalized["comment_body"] == "Test comment"
    
    def test_normalize_comment_missing_timestamp(self):
        """Test normalization when timestamp is missing"""
        raw_comment = {
            "id": 999,
            "body": "Test",
            "user": {"login": "user1"}
        }
        
        normalized = normalize_comment(raw_comment, "review_comment", "owner/repo#1")
        
        # Should have a timestamp (current time or empty)
        assert "timestamp" in normalized


class TestLoadExistingPRs:
    """Tests for load_existing_prs function"""
    
    @patch('code.src.extraction.fetch_human_comments.get_paths')
    @patch('code.src.extraction.fetch_human_comments.os.listdir')
    @patch('code.src.extraction.fetch_human_comments.open')
    def test_load_prs_from_files(self, mock_open, mock_listdir, mock_get_paths):
        """Test loading PRs from JSON files"""
        mock_get_paths.return_value = {"raw_data": "/fake/raw"}
        mock_listdir.return_value = ["pr_1.json", "pr_2.json", "other.txt"]
        
        # Mock file contents
        mock_file1 = MagicMock()
        mock_file1.__enter__.return_value.read.return_value = json.dumps([{"number": 1}])
        mock_file2 = MagicMock()
        mock_file2.__enter__.return_value.read.return_value = json.dumps([{"number": 2}])
        
        mock_open.side_effect = [mock_file1, mock_file2]
        
        prs = load_existing_prs()
        
        assert len(prs) == 2
        assert prs[0]["number"] == 1
        assert prs[1]["number"] == 2
    
    @patch('code.src.extraction.fetch_human_comments.get_paths')
    @patch('code.src.extraction.fetch_human_comments.os.path.exists')
    def test_load_prs_directory_not_found(self, mock_exists, mock_get_paths):
        """Test when raw data directory doesn't exist"""
        mock_get_paths.return_value = {"raw_data": "/nonexistent"}
        mock_exists.return_value = False
        
        prs = load_existing_prs()
        
        assert prs == []
    
    @patch('code.src.extraction.fetch_human_comments.get_paths')
    @patch('code.src.extraction.fetch_human_comments.os.listdir')
    @patch('code.src.extraction.fetch_human_comments.open')
    def test_load_prs_invalid_json(self, mock_open, mock_listdir, mock_get_paths):
        """Test handling of invalid JSON files"""
        mock_get_paths.return_value = {"raw_data": "/fake/raw"}
        mock_listdir.return_value = ["pr_1.json"]
        
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "invalid json"
        mock_open.return_value = mock_file
        
        prs = load_existing_prs()
        
        assert prs == []

class TestExtractRepoInfo:
    """Tests for extract_repo_info function"""
    
    def test_extract_from_repo_field(self):
        """Test extracting repo info from 'repo' field"""
        pr = {
            "number": 123,
            "repo": "owner/repo"
        }
        
        owner, repo, number = extract_repo_info(pr)
        
        assert owner == "owner"
        assert repo == "repo"
        assert number == 123
    
    def test_extract_from_base_repo(self):
        """Test extracting repo info from base.repo"""
        pr = {
            "number": 456,
            "base": {
                "repo": {
                    "owner": {"login": "baseowner"},
                    "name": "baserepo"
                }
            }
        }
        
        owner, repo, number = extract_repo_info(pr)
        
        assert owner == "baseowner"
        assert repo == "baserepo"
        assert number == 456


class TestSaveComments:
    """Tests for save_comments function"""
    
    def test_save_comments_creates_file(self):
        """Test that save_comments creates the output file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_comments.json")
            comments = [
                {"reviewer_id": "user1", "comment_body": "Test 1"},
                {"reviewer_id": "user2", "comment_body": "Test 2"}
            ]
            
            save_comments(comments, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, "r") as f:
                loaded = json.load(f)
            
            assert len(loaded) == 2
            assert loaded[0]["reviewer_id"] == "user1"

class TestMainFunction:
    """Tests for main function"""
    
    @patch('code.src.extraction.fetch_human_comments.get_config')
    @patch('code.src.extraction.fetch_human_comments.get_paths')
    @patch('code.src.extraction.fetch_human_comments.fetch_human_comments_for_all_prs')
    def test_main_with_comments(self, mock_fetch, mock_get_paths, mock_get_config):
        """Test main function when comments are fetched"""
        mock_get_config.return_value = {"github": {"auth_token": "fake_token"}}
        mock_get_paths.return_value = {
            "annotations": "/fake/annotations",
            "raw_data": "/fake/raw"
        }
        mock_fetch.return_value = [
            {"reviewer_id": "user1", "comment_body": "Test"}
        ]
        
        with patch('code.src.extraction.fetch_human_comments.save_comments') as mock_save:
            result = main()
            
            assert result == 0
            mock_save.assert_called_once()
    
    @patch('code.src.extraction.fetch_human_comments.get_config')
    @patch('code.src.extraction.fetch_human_comments.get_paths')
    @patch('code.src.extraction.fetch_human_comments.fetch_human_comments_for_all_prs')
    def test_main_no_comments(self, mock_fetch, mock_get_paths, mock_get_config):
        """Test main function when no comments are fetched"""
        mock_get_config.return_value = {}
        mock_get_paths.return_value = {"annotations": "/fake/annotations"}
        mock_fetch.return_value = []
        
        result = main()
        
        assert result == 0
        # save_comments should not be called when no comments
        with patch('code.src.extraction.fetch_human_comments.save_comments') as mock_save:
            main()
            mock_save.assert_not_called()
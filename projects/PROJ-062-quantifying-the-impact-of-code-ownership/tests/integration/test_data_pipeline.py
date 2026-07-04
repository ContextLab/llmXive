"""
Integration test for the data collection pipeline.
Runs end-to-end on a small sample repository (apache/httpd) to verify
that cloning, commit parsing, issue fetching, and CSV output generation work correctly.
"""

import os
import sys
import csv
import shutil
import tempfile
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data_collection import (
    clone_repository,
    verify_commit_count,
    parse_commit_history,
    fetch_github_issues,
    save_issues_to_csv,
    process_issues_for_repo,
    clone_repositories,
    process_all_repos
)
from config import get_depth_limit, get_repo_list, get_github_token, get_output_dir
from utils.backoff import fetch_with_backoff
from utils.path_normalizer import normalize_path

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
SAMPLE_REPO = "apache/httpd"
TEST_DEPTH = 100  # Reduced depth for faster integration testing
EXPECTED_MIN_COMMITS = 50  # Expect at least some commits in the shallow clone

def setup_test_environment():
    """Create a temporary directory for test outputs."""
    test_dir = tempfile.mkdtemp(prefix="test_data_pipeline_")
    logger.info(f"Created test directory: {test_dir}")
    return Path(test_dir)

def cleanup_test_environment(test_dir: Path):
    """Remove the temporary test directory."""
    if test_dir.exists():
        shutil.rmtree(test_dir)
        logger.info(f"Cleaned up test directory: {test_dir}")

def test_clone_and_verify():
    """Test cloning a repository and verifying commit count."""
    logger.info("Starting clone and verification test...")
    
    repo_path = clone_repository(SAMPLE_REPO, TEST_DEPTH)
    assert repo_path.exists(), f"Repository not cloned to {repo_path}"
    
    commit_count = verify_commit_count(repo_path, TEST_DEPTH)
    logger.info(f"Repository {SAMPLE_REPO} has {commit_count} commits (depth limit: {TEST_DEPTH})")
    
    # For a shallow clone, we expect at least the depth limit or all commits if repo is smaller
    # Since httpd is large, we expect exactly TEST_DEPTH commits
    assert commit_count >= EXPECTED_MIN_COMMITS, f"Expected at least {EXPECTED_MIN_COMMITS} commits, got {commit_count}"
    
    return repo_path

def test_parse_commit_history(repo_path: Path):
    """Test parsing commit history into CSV."""
    logger.info("Starting commit history parsing test...")
    
    commits_csv_path = repo_path.parent / f"{SAMPLE_REPO.replace('/', '_')}_commits.csv"
    
    # Parse the commit history
    parse_commit_history(repo_path, commits_csv_path)
    
    assert commits_csv_path.exists(), f"Commits CSV not created at {commits_csv_path}"
    
    # Verify CSV has content
    with open(commits_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    logger.info(f"Parsed {len(rows)} commits from {SAMPLE_REPO}")
    assert len(rows) > 0, "No commits found in parsed CSV"
    
    # Verify required columns exist
    required_columns = ['author', 'timestamp', 'file_path', 'commit_hash']
    actual_columns = set(rows[0].keys())
    for col in required_columns:
        assert col in actual_columns, f"Missing required column: {col}"
    
    return commits_csv_path, rows

def test_fetch_github_issues(repo_path: Path):
    """Test fetching GitHub issues for the repository."""
    logger.info("Starting GitHub issues fetching test...")
    
    issues_csv_path = repo_path.parent / f"{SAMPLE_REPO.replace('/', '_')}_issues.csv"
    
    # Fetch issues with a small time window for testing
    issues_csv_path = fetch_github_issues(SAMPLE_REPO, issues_csv_path)
    
    assert issues_csv_path.exists(), f"Issues CSV not created at {issues_csv_path}"
    
    # Verify CSV has content (might be empty if no issues in time window, but file should exist)
    with open(issues_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    logger.info(f"Fetched {len(rows)} issues for {SAMPLE_REPO}")
    
    return issues_csv_path, rows

def test_process_issues_for_repo(repo_path: Path, issues_csv_path: Path):
    """Test processing and linking issues to modules."""
    logger.info("Starting issue processing test...")
    
    processed_csv_path = repo_path.parent / f"{SAMPLE_REPO.replace('/', '_')}_processed_issues.csv"
    
    # Process issues
    processed_csv_path = process_issues_for_repo(
        SAMPLE_REPO, 
        repo_path, 
        issues_csv_path, 
        processed_csv_path
    )
    
    assert processed_csv_path.exists(), f"Processed issues CSV not created at {processed_csv_path}"
    
    # Verify CSV has content
    with open(processed_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    logger.info(f"Processed {len(rows)} issues for {SAMPLE_REPO}")
    
    # Verify normalized paths are present
    if len(rows) > 0:
        assert 'normalized_path' in rows[0], "Missing 'normalized_path' column in processed issues"
    
    return processed_csv_path, rows

def run_full_pipeline():
    """Run the full data collection pipeline on the sample repo."""
    logger.info("Starting full pipeline test...")
    
    test_dir = setup_test_environment()
    original_output_dir = os.environ.get('OUTPUT_DIR')
    
    try:
        # Set output directory for the test
        os.environ['OUTPUT_DIR'] = str(test_dir)
        
        # Clone repository
        repo_path = clone_repository(SAMPLE_REPO, TEST_DEPTH)
        
        # Parse commit history
        commits_csv_path = repo_path.parent / f"{SAMPLE_REPO.replace('/', '_')}_commits.csv"
        parse_commit_history(repo_path, commits_csv_path)
        
        # Fetch issues
        issues_csv_path = repo_path.parent / f"{SAMPLE_REPO.replace('/', '_')}_issues.csv"
        fetch_github_issues(SAMPLE_REPO, issues_csv_path)
        
        # Process issues
        processed_issues_path = repo_path.parent / f"{SAMPLE_REPO.replace('/', '_')}_processed_issues.csv"
        process_issues_for_repo(SAMPLE_REPO, repo_path, issues_csv_path, processed_issues_path)
        
        # Verify all expected output files exist
        expected_files = [
            commits_csv_path,
            issues_csv_path,
            processed_issues_path
        ]
        
        for file_path in expected_files:
            assert file_path.exists(), f"Expected output file not found: {file_path}"
            logger.info(f"✓ Output file exists: {file_path}")
            
            # Check file size is reasonable
            file_size = file_path.stat().st_size
            logger.info(f"  File size: {file_size} bytes")
            assert file_size > 0, f"Output file is empty: {file_path}"
        
        logger.info("✓ Full pipeline test completed successfully!")
        return True
        
    finally:
        # Restore original environment
        if original_output_dir:
            os.environ['OUTPUT_DIR'] = original_output_dir
        else:
            os.environ.pop('OUTPUT_DIR', None)
        
        # Cleanup
        cleanup_test_environment(test_dir)

def main():
    """Main entry point for the integration test."""
    logger.info("=" * 80)
    logger.info("Running Data Pipeline Integration Test")
    logger.info(f"Sample Repository: {SAMPLE_REPO}")
    logger.info(f"Clone Depth: {TEST_DEPTH}")
    logger.info("=" * 80)
    
    try:
        # Run the full pipeline
        success = run_full_pipeline()
        
        if success:
            logger.info("✓ ALL TESTS PASSED")
            return 0
        else:
            logger.error("✗ TESTS FAILED")
            return 1
            
    except Exception as e:
        logger.error(f"✗ TEST FAILED WITH EXCEPTION: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
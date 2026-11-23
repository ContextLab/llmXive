"""
Script to execute repository fetching and pinning (T024).
This script is invoked by the run-book to ensure real data fetching.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from repo_utils import clone_or_fetch_repo, get_repo_files, log_pinned_repo, DataFetchError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for repository fetching.
    Reads configuration from environment or arguments.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch and pin repository for analysis')
    parser.add_argument('--repo', required=True, help='Repository URL')
    parser.add_argument('--commit', required=True, help='Commit hash to pin to')
    parser.add_argument('--output-dir', default='data/raw/repos', help='Output directory')
    parser.add_argument('--log-file', default='data/raw/pinned_repo.json', help='Log file path')
    
    args = parser.parse_args()
    
    logger.info(f"Fetching repository: {args.repo}")
    logger.info(f"Pinning to commit: {args.commit}")
    
    try:
        # Clone and checkout
        repo_path = clone_or_fetch_repo(args.repo, args.commit, args.output_dir)
        logger.info(f"Repository cloned to: {repo_path}")
        
        # Get file list
        files, count = get_repo_files(repo_path)
        logger.info(f"Successfully fetched {count} files")
        
        # Log pinned repo
        log_pinned_repo(args.repo, args.commit, repo_path, args.log_file)
        logger.info(f"Pinned repo logged to: {args.log_file}")
        
        # Verify output file exists
        if not os.path.exists(args.log_file):
            raise RuntimeError(f"Log file was not created: {args.log_file}")
        
        logger.info("Repository fetching completed successfully")
        
    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during fetch: {e}")
        raise

if __name__ == "__main__":
    main()
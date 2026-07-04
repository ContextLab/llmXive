import os
from datetime import datetime, timedelta
from typing import List, Optional

def get_cutoff_date() -> datetime:
    """Get the cutoff date T for analysis (default: 1 year ago from now)."""
    cutoff_str = os.getenv('CUTOFF_DATE')
    if cutoff_str:
        return datetime.fromisoformat(cutoff_str)
    # Default: 1 year ago
    return datetime.now() - timedelta(days=365)

def get_depth_limit() -> int:
    """Get the git clone depth limit (default: 1000)."""
    depth_str = os.getenv('GIT_DEPTH')
    return int(depth_str) if depth_str else 1000

def get_repo_list() -> List[str]:
    """Get list of repositories to process."""
    repo_str = os.getenv('REPO_LIST')
    if repo_str:
        return [r.strip() for r in repo_str.split(',') if r.strip()]
    # Default list of open source projects
    return [
        'https://github.com/apache/httpd',
        'https://github.com/psf/requests',
        'https://github.com/pallets/flask',
        'https://github.com/django/django',
        'https://github.com/psycopg/psycopg2'
    ]

def get_github_token() -> Optional[str]:
    """Get GitHub API token for authenticated requests."""
    return os.getenv('GITHUB_TOKEN')

def get_output_dir() -> str:
    """Get output directory for intermediate files."""
    return os.getenv('OUTPUT_DIR', 'data/intermediate')

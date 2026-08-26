"""
Repository list loader for the code documentation evaluation pipeline.

This module provides utilities to load and validate the frozen list of
top repositories from data/raw/repo_list.json.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import ConfigException

logger = logging.getLogger(__name__)

class RepoLoaderException(ConfigException):
    """Exception raised for errors in repository list loading or validation."""
    pass

def load_repo_list(
    repo_list_path: Optional[Path] = None,
    max_repos: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Load and validate the frozen list of top repositories.

    Args:
        repo_list_path: Path to the repo_list.json file. If None, defaults to
            data/raw/repo_list.json relative to the project root.
        max_repos: Optional maximum number of repositories to return. If provided,
            the list is truncated to this size.

    Returns:
        A list of dictionaries, where each dictionary represents a repository
        with at least 'name' and 'url' keys.

    Raises:
        RepoLoaderException: If the file cannot be found, parsed, or does not
            contain a valid list of repositories.
    """
    if repo_list_path is None:
        # Default path relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        repo_list_path = project_root / "data" / "raw" / "repo_list.json"

    if not repo_list_path.exists():
        raise RepoLoaderException(
            f"Repository list file not found: {repo_list_path}. "
            "Ensure the file exists or provide a valid path."
        )

    try:
        with open(repo_list_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RepoLoaderException(
            f"Failed to parse JSON from {repo_list_path}: {e}"
        )
    except IOError as e:
        raise RepoLoaderException(
            f"Failed to read file {repo_list_path}: {e}"
        )

    # Validate structure
    if not isinstance(data, list):
        raise RepoLoaderException(
            f"Repository list must be a JSON array, got {type(data).__name__}"
        )

    if len(data) == 0:
        logger.warning("Repository list is empty.")
        return []

    # Validate each entry
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise RepoLoaderException(
                f"Repository entry at index {i} must be a dictionary, got {type(entry).__name__}"
            )
        if "name" not in entry:
            raise RepoLoaderException(
                f"Repository entry at index {i} is missing required 'name' field"
            )
        if "url" not in entry:
            raise RepoLoaderException(
                f"Repository entry at index {i} is missing required 'url' field"
            )
        if not isinstance(entry["name"], str) or not entry["name"].strip():
            raise RepoLoaderException(
                f"Repository entry at index {i} has invalid 'name': must be a non-empty string"
            )
        if not isinstance(entry["url"], str) or not entry["url"].strip():
            raise RepoLoaderException(
                f"Repository entry at index {i} has invalid 'url': must be a non-empty string"
            )

    logger.info(f"Loaded {len(data)} repositories from {repo_list_path}")

    # Apply max_repos limit if specified
    if max_repos is not None:
        if max_repos <= 0:
            raise RepoLoaderException(f"max_repos must be positive, got {max_repos}")
        if len(data) > max_repos:
            logger.info(f"Truncating repository list from {len(data)} to {max_repos} entries")
            data = data[:max_repos]

    return data

def validate_repo_list(
    repo_list_path: Optional[Path] = None
) -> bool:
    """
    Validate the structure of the repository list file.

    Args:
        repo_list_path: Path to the repo_list.json file.

    Returns:
        True if the file exists and contains valid data, False otherwise.

    Raises:
        RepoLoaderException: Propagated from load_repo_list if validation fails.
    """
    try:
        load_repo_list(repo_list_path)
        return True
    except RepoLoaderException:
        return False
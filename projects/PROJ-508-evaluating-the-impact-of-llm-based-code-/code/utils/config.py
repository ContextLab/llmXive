"""
Configuration management for the LLM Impact Study.

Handles environment variables, API keys, and project settings.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """
    Centralized configuration handler for the project.

    Loads settings from environment variables or defaults.
    """

    # Project Paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    DATA_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
    DATA_DERIVED_DIR: Path = PROJECT_ROOT / "data" / "derived"
    DOCS_OUTPUT_DIR: Path = PROJECT_ROOT / "docs" / "output"

    # GitHub API Configuration
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    GITHUB_API_BASE_URL: str = "https://api.github.com"
    GITHUB_REQUEST_TIMEOUT: int = 30
    GITHUB_RETRY_DELAY: float = 2.0
    GITHUB_MAX_RETRIES: int = 5

    # Analysis Configuration
    MIN_PR_COUNT_THRESHOLD: int = 10
    LLMA_ADOPTION_COMMIT_THRESHOLD: float = 0.05  # 5% frequency
    DIFF_COMPLEXITY_THRESHOLD: float = 0.3
    HIGH_VIF_THRESHOLD: float = 5.0
    ITERATION_THRESHOLD_RANGE: list = [1, 2, 3, 4, 5]

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")

    # Report Configuration
    REPORT_TITLE: str = "Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load"
    REPORT_AUTHOR: str = "llmXive Research Team"

    @classmethod
    def validate_environment(cls) -> Dict[str, Any]:
        """
        Validates that required environment variables are set.

        Returns:
            Dict with validation status and missing keys if any.
        """
        missing_keys = []

        # Check for required keys that have no safe default
        # Note: GITHUB_TOKEN is required for most operations
        if not cls.GITHUB_TOKEN:
            missing_keys.append("GITHUB_TOKEN")

        return {
            "valid": len(missing_keys) == 0,
            "missing_keys": missing_keys,
            "project_root": str(cls.PROJECT_ROOT)
        }

    @classmethod
    def ensure_directories(cls) -> None:
        """
        Ensures all required output directories exist.
        """
        dirs = [
            cls.DATA_RAW_DIR,
            cls.DATA_DERIVED_DIR,
            cls.DOCS_OUTPUT_DIR
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_api_headers(cls) -> Dict[str, str]:
        """
        Returns standard API headers for GitHub requests.

        Returns:
            Dict of headers including Authorization if token is available.
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "llmXive-Research-Client"
        }

        if cls.GITHUB_TOKEN:
            headers["Authorization"] = f"token {cls.GITHUB_TOKEN}"

        return headers


# Convenience function for quick access
def get_config() -> Config:
    """
    Returns the Config instance for easy access to settings.

    Returns:
        Config instance with current settings.
    """
    return Config
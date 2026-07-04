"""
Pytest configuration and fixtures for integration tests.
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure environment variables are loaded
env_example = project_root / ".env.example"
if env_example.exists() and not os.path.exists(project_root / ".env"):
    # Create example .env file if it doesn't exist
    import shutil
    shutil.copy(env_example, project_root / ".env")
    os.environ["OVERPASS_API_KEY"] = "test_key"  # Mock key for testing
    os.environ["AWS_ACCESS_KEY_ID"] = "test_aws_key"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test_aws_secret"

# Import and configure logging
from utils.logging import setup_logging

setup_logging(log_level="INFO")
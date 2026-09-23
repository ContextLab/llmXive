"""Global pytest fixtures and configurations."""

import pytest
from utils.logging import get_logger, set_root_level

@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """
    Ensure logging is configured for the entire test session.
    Sets the root logger to INFO level and directs output to a temporary file.
    """
    set_root_level("INFO")
    logger = get_logger(__name__)
    logger.info("Starting pytest session with configured logging.")
    yield
    logger.info("Ending pytest session.")
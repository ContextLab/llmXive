"""
Pytest configuration and fixtures for integration tests.
"""
import os
import sys
from pathlib import Path

# Add the project root to the path so imports work correctly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up environment variables if needed
os.environ.setdefault("OSM_API_URL", "https://overpass-api.de/api/interpreter")
os.environ.setdefault("MAX_BLOCKS", "100")

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test."
    )

def pytest_collection_modifyitems(config, items):
    """Skip integration tests if not explicitly requested."""
    # By default, skip integration tests unless --integration is passed
    if not config.getoption("--integration", default=False):
        skip_integration = pytest.mark.skip(reason="Need --integration option to run integration tests")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

def pytest_addoption(parser):
    parser.addoption(
        "--integration", action="store_true", default=False, help="run integration tests"
    )

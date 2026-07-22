"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def config():
    """Provide a test configuration."""
    from config import Config
    return Config({
        'seeds': {'random': 12345},
        'paths': {
            'training': str(project_root / 'data' / 'training'),
            'held_out': str(project_root / 'data' / 'held_out'),
            'processed': str(project_root / 'data' / 'processed')
        }
    })


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    return tmp_path

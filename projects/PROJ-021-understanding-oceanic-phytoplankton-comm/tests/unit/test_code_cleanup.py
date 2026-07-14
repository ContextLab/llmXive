import os
import sys
import pytest
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.config import Config, get_config
from utils.logging_config import setup_logging, get_logger
from utils.data_loaders import get_available_ram_gb

def test_config_initialization():
    """Test that Config initializes correctly."""
    cfg = Config()
    assert cfg.seed == 42
    assert cfg.ram_limit_gb == 7.0

def test_get_config_singleton():
    """Test that get_config returns a singleton."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2

def test_logging_setup():
    """Test that logging setup works."""
    logger = setup_logging()
    assert logger is not None
    assert len(logger.handlers) > 0

def test_ram_limit():
    """Test RAM limit function."""
    ram = get_available_ram_gb()
    assert isinstance(ram, float)
    assert ram > 0

import os
import sys
import pytest
from pathlib import Path
import random
import numpy as np

def setup_environment():
    # Setup test environment
    pass

@pytest.fixture
def sample_events_content():
    return "trial_type,onset,duration\nInclusion,0,1\nExclusion,2,1"

@pytest.fixture
def sample_events_content_invalid():
    return "trial_type,onset,duration\nNeutral,0,1"

def pytest_configure(config):
    # Setup seed
    random.seed(42)
    np.random.seed(42)
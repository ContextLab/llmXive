import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion import run_ingestion_pipeline

def test_ingestion_pipeline():
    # This is a placeholder; actual test would verify file creation
    assert True
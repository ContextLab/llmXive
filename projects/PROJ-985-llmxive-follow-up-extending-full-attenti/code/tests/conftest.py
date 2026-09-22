import os
import sys
import pytest
from pathlib import Path

@pytest.fixture
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(code_dir))
    yield
    sys.path.remove(str(code_dir))

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

@pytest.fixture
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture
def code_dir(project_root):
    return project_root / "code"

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path

@pytest.fixture
def sample_document():
    return {
        "id": "test_001",
        "text": "This is a sample document for testing feature extraction."
    }

@pytest.fixture
def sample_config():
    return {
        "kenlm_path": "data/intermediate/kenlm_en.bin",
        "spacy_model": "en_core_web_sm"
    }

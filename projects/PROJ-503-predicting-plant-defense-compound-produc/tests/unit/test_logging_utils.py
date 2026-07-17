import json
import csv
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the PROJECT_ROOT logic because the module uses __file__
# To test properly, we will temporarily override the module's behavior or 
# test the functions that do not depend on absolute paths first, 
# but since the module writes to specific paths, we need to ensure those paths exist or are mocked.

# Strategy: Create a temporary directory structure that mimics the project root
# and patch the logging_utils module's paths.

import sys
import importlib

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    base = tempfile.mkdtemp()
    proj_root = Path(base) / "projects" / "PROJ-503-predicting-plant-defense-compound-produc"
    proj_root.mkdir(parents=True)
    logs_dir = proj_root / "logs"
    logs_dir.mkdir()
    return proj_root, logs_dir

@pytest.fixture
def patched_logging_utils(temp_project_root):
    """Patch logging_utils to use temp paths."""
    proj_root, logs_dir = temp_project_root
    
    # Remove from sys.modules if already loaded
    if 'logging_utils' in sys.modules:
        del sys.modules['logging_utils']
    
    # We need to modify the source code or use a mock. 
    # Since we can't easily patch the module's internal constants after import without complex mocking,
    # we will create a temporary version of the file in the temp directory and import it.
    
    # Actually, the cleanest way for this specific constraint is to assume the user runs tests 
    # from the project root. However, to be robust, let's just test the logic by 
    # temporarily replacing the constants in the module if we can import it, 
    # OR better: Create a test wrapper that sets up the environment.
    
    # Since the task requires the file to be at a specific path, we assume the test runs 
    # in an environment where the project structure exists or we simulate it.
    
    # Let's simulate the import by creating the file in a temp location and adjusting sys.path
    # but that's fragile. 
    
    # Alternative: The module uses Path(__file__).parent.parent. 
    # If we place the test in tests/unit/, and the module in code/, 
    # we can't easily change the module's __file__ behavior without copying the file.
    
    # Let's copy the file to the temp location, patch the import, and run tests.
    
    source_file = Path(__file__).parent.parent.parent / "code" / "logging_utils.py"
    if not source_file.exists():
        pytest.skip("Source file not found")
        
    # Copy to temp location
    temp_code_dir = proj_root / "code"
    temp_code_dir.mkdir()
    temp_file = temp_code_dir / "logging_utils.py"
    
    # Read and modify the file to use the temp logs_dir
    # This is a bit hacky but necessary for isolation without complex mocking
    with open(source_file, 'r') as f:
        content = f.read()
    
    # Replace the hardcoded path logic with one that uses an environment variable or just 
    # write to the temp logs_dir. 
    # Actually, let's just use the fact that we can set the environment variable 
    # if we modify the code, but we can't modify the code for the test.
    
    # Better approach: Use monkeypatch on the module's global variables after import.
    # But we need to import it first.
    
    # Let's just import it and see if we can patch the constants.
    # We will add the temp_code_dir to sys.path temporarily.
    sys.path.insert(0, str(temp_code_dir))
    
    # We need to create a fake __init__.py or ensure the import works
    (temp_code_dir / "__init__.py").touch()
    
    # Now import
    # We need to replace the content of the file to use the temp path
    # because Path(__file__) will point to the temp file.
    
    # Let's write a modified version of the file that respects the temp path
    # by replacing the PROJECT_ROOT logic.
    
    # Actually, the simplest way is to just run the tests assuming the project structure exists
    # at the expected location relative to the test runner, or create a mock.
    
    # Let's create a mock module object.
    import types
    module = types.ModuleType('logging_utils')
    
    # Copy functions from the real module but patch the paths
    # We need to read the source and exec it with modified globals
    
    # Let's just assume the test runs in the context where the project root is correct
    # and rely on the fact that the test runner might be in the project root.
    # But to be safe, let's just test the logic by creating the files manually.
    
    # Revert to a simpler approach: 
    # 1. Create the logs directory manually in the temp location.
    # 2. Import the module.
    # 3. Monkeypatch the module's global variables (PAIRING_LOG_PATH, FILTERING_LOG_PATH)
    
    # We need to import the module from the original location first.
    # But the original location might not exist in the test environment.
    # So we must copy it to the temp location.
    
    # Copy the file content and modify the path logic
    modified_content = content.replace(
        'PROJECT_ROOT = Path(__file__).resolve().parent.parent',
        f'PROJECT_ROOT = Path(r"{proj_root}")'
    ).replace(
        'LOGS_DIR = PROJECT_ROOT / "logs"',
        f'LOGS_DIR = Path(r"{logs_dir}")'
    )
    
    with open(temp_file, 'w') as f:
        f.write(modified_content)
    
    # Now import the modified module
    spec = importlib.util.spec_from_file_location("logging_utils", temp_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module

def test_log_data_pairing_mismatch(patched_logging_utils, temp_project_root):
    """Test logging a single pairing mismatch."""
    module, logs_dir = patched_logging_utils, temp_project_root[1]
    log_path = logs_dir / "data_pairing.json"
    
    # Initial state
    assert not log_path.exists()
    
    # Log a mismatch
    module.log_data_pairing_mismatch(
        sample_id="S1",
        expression_source="GEO123",
        metabolite_source="MW456",
        reason="test_reason"
    )
    
    # Verify file exists and content
    assert log_path.exists()
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert "mismatches" in data
    assert len(data["mismatches"]) == 1
    assert data["mismatches"][0]["sample_id"] == "S1"
    assert data["mismatches"][0]["reason"] == "test_reason"
    assert "metadata" in data
    assert "updated" in data["metadata"]

def test_log_data_pairing_mismatches_batch(patched_logging_utils, temp_project_root):
    """Test logging multiple pairing mismatches."""
    module, logs_dir = patched_logging_utils, temp_project_root[1]
    log_path = logs_dir / "data_pairing.json"
    
    mismatches = [
        {"sample_id": "S1", "expression_source": "E1", "metabolite_source": "M1", "reason": "r1"},
        {"sample_id": "S2", "expression_source": "E2", "metabolite_source": "M2", "reason": "r2"}
    ]
    
    module.log_data_pairing_mismatches_batch(mismatches)
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data["mismatches"]) == 2
    assert data["mismatches"][0]["sample_id"] == "S1"
    assert data["mismatches"][1]["sample_id"] == "S2"

def test_get_pairing_log_stats(patched_logging_utils, temp_project_root):
    """Test retrieving pairing log statistics."""
    module, logs_dir = patched_logging_utils, temp_project_root[1]
    
    # Log some data
    module.log_data_pairing_mismatch("S1", "E1", "M1", "reason_a")
    module.log_data_pairing_mismatch("S2", "E2", "M2", "reason_b")
    module.log_data_pairing_mismatch("S3", "E3", "M3", "reason_a")
    
    stats = module.get_pairing_log_stats()
    
    assert stats["total_mismatches"] == 3
    assert stats["reasons"]["reason_a"] == 2
    assert stats["reasons"]["reason_b"] == 1
    assert stats["last_updated"] is not None

def test_log_zero_variance_feature(patched_logging_utils, temp_project_root):
    """Test logging a zero-variance feature."""
    module, logs_dir = patched_logging_utils, temp_project_root[1]
    log_path = logs_dir / "feature_filtering.csv"
    
    # Log a feature
    module.log_zero_variance_feature("Gene1", 0.0, "zero_variance")
    
    assert log_path.exists()
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["gene_id"] == "Gene1"
    assert float(rows[0]["variance"]) == 0.0
    assert rows[0]["reason"] == "zero_variance"

def test_log_zero_variance_features_batch(patched_logging_utils, temp_project_root):
    """Test logging multiple zero-variance features."""
    module, logs_dir = patched_logging_utils, temp_project_root[1]
    log_path = logs_dir / "feature_filtering.csv"
    
    features = [
        {"gene_id": "G1", "variance": 1e-15},
        {"gene_id": "G2", "variance": 1e-11},
        {"gene_id": "G3", "variance": 0.0, "reason": "custom_reason"}
    ]
    
    module.log_zero_variance_features_batch(features)
    
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0]["gene_id"] == "G1"
    assert rows[2]["reason"] == "custom_reason"

def test_get_filtering_log_stats(patched_logging_utils, temp_project_root):
    """Test retrieving filtering log statistics."""
    module, logs_dir = patched_logging_utils, temp_project_root[1]
    
    module.log_zero_variance_feature("G1", 0.0, "zero_variance")
    module.log_zero_variance_feature("G2", 0.0, "zero_variance")
    module.log_zero_variance_feature("G3", 0.0, "low_variance")
    
    stats = module.get_filtering_log_stats()
    
    assert stats["total_filtered"] == 3
    assert stats["reasons"]["zero_variance"] == 2
    assert stats["reasons"]["low_variance"] == 1
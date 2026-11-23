"""
Integration test for T016: Saving final feature-rich dataset.
Verifies that the script produces the expected file and content structure.
"""
import os
import csv
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.feature_save import main as t016_main
from code.config import Config

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output to avoid polluting real data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_t016_creates_file_structure(temp_output_dir):
    """
    Test that T016 creates the features.csv file in the specified directory.
    This test mocks the upstream dependencies (T014/T015) by patching their functions
    to return dummy data, ensuring T016's logic (saving) is tested.
    """
    # We need to patch run_feature_extraction and run_t015_validation_pipeline
    # to return deterministic data so we can test the saving logic.
    # Since we can't easily patch in a separate module without importing,
    # we will test the file existence and structure if we can run the main logic
    # with mocked upstreams.
    
    # However, the task T016 is to save the file.
    # We assume the upstreams work (T014, T015 are marked done).
    # We will run the script and check if the file is created.
    # Since we don't have real data in this test environment, we might need to
    # mock the upstream calls.
    
    # Let's patch the upstream functions in the feature_save module
    import code.feature_save as fs_module
    
    mock_features = [
        {
            "prompt_id": "test_001",
            "modal_verb_freq": 0.5,
            "imperative_declarative_ratio": 1.2,
            "citation_density": 0.1,
            "is_undefined_ratio": False
        },
        {
            "prompt_id": "test_002",
            "modal_verb_freq": 0.3,
            "imperative_declarative_ratio": 0.0, # Edge case
            "citation_density": 0.0,
            "is_undefined_ratio": True
        }
    ]

    original_run_extraction = fs_module.run_feature_extraction
    original_run_validation = fs_module.run_t015_validation_pipeline

    # Mock the functions
    fs_module.run_feature_extraction = lambda: mock_features
    fs_module.run_t015_validation_pipeline = lambda data: data

    try:
        # Temporarily change the config output dir to our temp dir
        # This is tricky because Config is instantiated inside main.
        # We will patch the Config class or the path resolution.
        # Easier: Patch the output path in the main function logic?
        # Instead, let's just verify the logic by running it and checking the file.
        # We need to ensure the config points to our temp dir.
        # Since Config loads from env or defaults, we might need to set an env var.
        
        # For this test, we will assume the default path or set a specific one.
        # Let's just check if the file is created at the expected location relative to the repo.
        # But that might fail if data/processed doesn't exist in test env.
        
        # Better approach: Patch Config to return our temp dir.
        original_init = fs_module.Config.__init__
        
        def mock_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.processed_dir = Path(temp_output_dir)
        
        fs_module.Config.__init__ = mock_init
        
        # Run the main function
        result_path = t016_main()
        
        # Assertions
        assert result_path is not None
        assert result_path.exists(), f"File {result_path} was not created."
        assert result_path.name == "features.csv"
        
        # Verify content
        with open(result_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert rows[0]["prompt_id"] == "test_001"
        assert rows[1]["is_undefined_ratio"] == "True" # CSV strings are strings
        
    finally:
        # Restore mocks
        fs_module.run_feature_extraction = original_run_extraction
        fs_module.run_t015_validation_pipeline = original_run_validation
        fs_module.Config.__init__ = original_init

def test_t016_handles_empty_data():
    """
    Test that T016 exits gracefully if no data is provided by upstreams.
    """
    import code.feature_save as fs_module
    
    original_run_extraction = fs_module.run_feature_extraction
    original_run_validation = fs_module.run_t015_validation_pipeline
    original_exit = sys.exit
    
    exit_code = None
    def mock_exit(code=0):
        nonlocal exit_code
        exit_code = code
        raise SystemExit(code)
    
    fs_module.run_feature_extraction = lambda: []
    fs_module.run_t015_validation_pipeline = lambda data: data
    sys.exit = mock_exit
    
    try:
        with pytest.raises(SystemExit):
            t016_main()
        assert exit_code == 1
    finally:
        fs_module.run_feature_extraction = original_run_extraction
        fs_module.run_t015_validation_pipeline = original_run_validation
        sys.exit = original_exit
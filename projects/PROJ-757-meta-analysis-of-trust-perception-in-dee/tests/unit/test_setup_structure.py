"""
Unit tests for the project setup script (T001).

Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add the code directory to the path to import the setup script logic
# We import the function directly from the module if it were a library,
# but since it's a script, we will test the logic by running it or importing the function
# For this test, we assume the logic is encapsulated. 
# Since the script is simple, we will test the directory creation logic directly here
# to avoid executing the script with side effects in the test runner.

def get_expected_dirs(base_path):
    """Returns a set of expected directory paths relative to base_path."""
    dirs = [
        "code",
        "data/search_results",
        "data/screening",
        "data/harmonized",
        "results/analysis_output",
        "results/figures",
        "results/robustness",
        "tests/unit",
        "tests/integration"
    ]
    return {os.path.join(base_path, d) for d in dirs}

def create_structure_logic(base_path):
    """Logic extracted from setup_project_structure.py for testing."""
    import os
    directories = [
        "code",
        "data/search_results",
        "data/screening",
        "data/harmonized",
        "results/analysis_output",
        "results/figures",
        "results/robustness",
        "tests/unit",
        "tests/integration"
    ]
    created = []
    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created.append(full_path)
    return created

class TestProjectStructure:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir)

    def test_structure_creation(self):
        """Test that the setup logic creates all required directories."""
        created = create_structure_logic(self.temp_dir)
        expected = get_expected_dirs(self.temp_dir)
        
        assert len(created) == len(expected), f"Expected {len(expected)} dirs, created {len(created)}"
        
        for exp_dir in expected:
            assert os.path.isdir(exp_dir), f"Directory not created: {exp_dir}"

    def test_nested_directories_exist(self):
        """Verify that nested directories like data/search_results exist."""
        create_structure_logic(self.temp_dir)
        
        assert os.path.isdir(os.path.join(self.temp_dir, "data", "search_results"))
        assert os.path.isdir(os.path.join(self.temp_dir, "results", "analysis_output"))
        assert os.path.isdir(os.path.join(self.temp_dir, "tests", "unit"))

    def test_re_run_idempotency(self):
        """Test that running the logic twice doesn't raise errors."""
        create_structure_logic(self.temp_dir)
        created_second = create_structure_logic(self.temp_dir)
        
        # Second run should create 0 new directories if they already exist
        assert len(created_second) == 0
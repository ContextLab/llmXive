import os
import json
import tempfile
import shutil
import pytest
from validation import calculate_loc, calculate_cyclomatic_complexity, analyze_file_metrics, collect_metrics_for_covariates

class TestValidationMetrics:
    """Unit tests for metric collection functions in validation.py."""

    def setup_method(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_calculate_loc_simple(self):
        """Test LOC calculation on a simple Python file."""
        file_path = os.path.join(self.test_dir, 'simple.py')
        with open(file_path, 'w') as f:
            f.write("x = 1\ny = 2\n# comment\n\nz = 3\n")
        
        loc = calculate_loc(file_path)
        # 3 code lines, 1 comment, 1 blank -> 3 LOC
        assert loc == 3

    def test_calculate_loc_empty(self):
        """Test LOC calculation on an empty file."""
        file_path = os.path.join(self.test_dir, 'empty.py')
        with open(file_path, 'w') as f:
            f.write("")
        
        loc = calculate_loc(file_path)
        assert loc == 0

    def test_calculate_cc_simple(self):
        """Test CC calculation on a simple file."""
        file_path = os.path.join(self.test_dir, 'cc_simple.py')
        with open(file_path, 'w') as f:
            f.write("def foo():\n    if True:\n        pass\n")
        
        cc = calculate_cyclomatic_complexity(file_path)
        # Base 1 + 1 for if = 2
        assert cc == 2

    def test_collect_metrics_for_covariates(self):
        """Test the full metric collection pipeline."""
        # Create a test repo structure
        repo_path = os.path.join(self.test_dir, 'test_repo')
        os.makedirs(repo_path)
        
        # Create a Python file
        with open(os.path.join(repo_path, 'main.py'), 'w') as f:
            f.write("x = 1\nif x > 0:\n    print(x)\n")
        
        output_path = os.path.join(self.test_dir, 'metrics.json')
        
        result = collect_metrics_for_covariates([repo_path], output_path)
        
        assert 'repositories' in result
        assert len(result['repositories']) == 1
        assert result['repositories'][0]['path'] == repo_path
        assert result['repositories'][0]['total_loc'] > 0
        assert result['repositories'][0]['total_cc'] > 0
        
        # Verify file was written
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data == result

    def test_collect_metrics_no_repos(self):
        """Test behavior when no repositories are provided."""
        output_path = os.path.join(self.test_dir, 'metrics_empty.json')
        result = collect_metrics_for_covariates([], output_path)
        
        assert result['summary']['total_repos'] == 0
        assert len(result['repositories']) == 0
        assert os.path.exists(output_path)
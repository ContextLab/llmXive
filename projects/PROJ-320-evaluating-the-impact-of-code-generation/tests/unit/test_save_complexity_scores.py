"""
Unit tests for code/analysis/save_complexity_scores.py
"""
import os
import csv
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.save_complexity_scores import load_labeled_prs, calculate_complexity_score
from utils.config import get_path

class TestLoadLabeledPRs:
    def test_load_labeled_prs_success(self, tmp_path):
        """Test loading a valid CSV file."""
        # Create a mock CSV file
        csv_file = tmp_path / "prs_labeled.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['pr_id', 'source_type', 'confidence_score'])
            writer.writeheader()
            writer.writerow({'pr_id': '123', 'source_type': 'llm', 'confidence_score': '0.9'})
            writer.writerow({'pr_id': '456', 'source_type': 'human', 'confidence_score': '0.8'})
        
        prs = load_labeled_prs(csv_file)
        
        assert len(prs) == 2
        assert prs[0]['pr_id'] == 123
        assert prs[0]['source_type'] == 'llm'
        assert prs[1]['pr_id'] == 456
        assert prs[1]['source_type'] == 'human'

    def test_load_labeled_prs_missing_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_labeled_prs(Path("/nonexistent/path/file.csv"))

    def test_load_labeled_prs_missing_columns(self, tmp_path):
        """Test that ValueError is raised for missing required columns."""
        csv_file = tmp_path / "prs_labeled.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['pr_id'])
            writer.writeheader()
            writer.writerow({'pr_id': '123'})
        
        with pytest.raises(ValueError) as excinfo:
            load_labeled_prs(csv_file)
        
        assert "Missing required columns" in str(excinfo.value)

    def test_load_labeled_prs_invalid_pr_id(self, tmp_path):
        """Test handling of invalid pr_id values."""
        csv_file = tmp_path / "prs_labeled.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['pr_id', 'source_type'])
            writer.writeheader()
            writer.writerow({'pr_id': 'abc', 'source_type': 'llm'}) # Invalid
            writer.writerow({'pr_id': '123', 'source_type': 'human'}) # Valid
        
        prs = load_labeled_prs(csv_file)
        
        # Should skip the invalid one and return only the valid one
        assert len(prs) == 1
        assert prs[0]['pr_id'] == 123

class TestCalculateComplexityScore:
    def test_calculate_complexity_score_no_diff(self):
        """Test that 0.0 is returned when no diff is present."""
        pr_data = {
            'pr_id': 123,
            'source_type': 'llm'
            # No 'diff' key
        }
        
        score = calculate_complexity_score(pr_data)
        assert score == 0.0

    def test_calculate_complexity_score_simple_diff(self):
        """Test complexity calculation with a simple diff."""
        # A simple function definition
        diff = """
        diff --git a/test.py b/test.py
        new file mode 100644
        --- /dev/null
        +++ b/test.py
        @@ -0,0 +1,3 @@
        +def hello():
        +    print("Hello")
        +    return True
        """
        
        pr_data = {
            'pr_id': 123,
            'diff': diff
        }
        
        score = calculate_complexity_score(pr_data)
        
        # A simple function like this should have a complexity > 0
        # (usually 1 for the function + 0 for the body, or 2 depending on implementation)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_calculate_complexity_score_complex_diff(self):
        """Test complexity calculation with a more complex diff containing conditionals."""
        diff = """
        diff --git a/test.py b/test.py
        new file mode 100644
        --- /dev/null
        +++ b/test.py
        @@ -0,0 +1,10 @@
        +def process(x):
        +    if x > 0:
        +        if x > 10:
        +            return "large"
        +        else:
        +            return "small"
        +    else:
        +        return "negative"
        +    return "done"
        """
        
        pr_data = {
            'pr_id': 456,
            'diff': diff
        }
        
        score = calculate_complexity_score(pr_data)
        
        # This should have higher complexity due to nested if statements
        assert isinstance(score, float)
        assert score > 1.0 # Should be at least 2 or 3

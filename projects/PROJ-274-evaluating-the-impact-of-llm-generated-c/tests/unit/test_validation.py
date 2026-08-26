"""
Unit tests for code/validation.py
Specifically testing the documentation rubric logic.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest

# Ensure code/ is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from validation import check_documentation_criteria, calculate_doc_quality_score, evaluate_repository_rubric

class TestDocumentationRubric:
    
    def test_check_criteria_all_present(self):
        content = """
        # My Project
        
        ## Setup
        Run pip install.
        
        ## API
        Use the client.
        
        ## Architecture
        It is modular.
        
        ## Usage
        Import and run.
        """
        is_high, found, score = check_documentation_criteria(content)
        assert is_high is True
        assert len(found) == 4
        assert score == 1.0
        assert 'Setup' in found
        assert 'API' in found
        assert 'Architecture' in found
        assert 'Usage' in found

    def test_check_criteria_missing_one(self):
        content = """
        # My Project
        
        ## Setup
        Run pip install.
        
        ## API
        Use the client.
        
        ## Architecture
        It is modular.
        """
        is_high, found, score = check_documentation_criteria(content)
        # 3 out of 4 is 0.75, which is >= 0.75, so it should be high quality
        assert is_high is True
        assert len(found) == 3
        assert score == 0.75

    def test_check_criteria_missing_two(self):
        content = """
        # My Project
        
        ## Setup
        Run pip install.
        
        ## API
        Use the client.
        """
        is_high, found, score = check_documentation_criteria(content)
        # 2 out of 4 is 0.5, which is < 0.75
        assert is_high is False
        assert len(found) == 2
        assert score == 0.5

    def test_check_criteria_empty(self):
        is_high, found, score = check_documentation_criteria("")
        assert is_high is False
        assert len(found) == 0
        assert score == 0.0

    def test_check_criteria_no_headers(self):
        content = "Just some text without headers."
        is_high, found, score = check_documentation_criteria(content)
        assert is_high is False
        assert len(found) == 0
        assert score == 0.0

    def test_calculate_score_file_missing(self):
        result = calculate_doc_quality_score("non_existent_file.md")
        assert result['exists'] is False
        assert result['score'] == 0.0
        assert result['is_high_quality'] is False

    def test_calculate_score_file_exists(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test\n## Setup\n## API\n## Architecture\n## Usage\n")
            temp_path = f.name
        
        try:
            result = calculate_doc_quality_score(temp_path)
            assert result['exists'] is True
            assert result['is_high_quality'] is True
            assert len(result['found_sections']) == 4
        finally:
            os.unlink(temp_path)

    def test_evaluate_repository_rubric_integration(self):
        # Create a temporary directory structure
        temp_dir = tempfile.mkdtemp()
        readme_dir = os.path.join(temp_dir, "readmes")
        os.makedirs(readme_dir)
        
        # Create test READMEs
        with open(os.path.join(readme_dir, "repo_good.md"), 'w') as f:
            f.write("# Good\n## Setup\n## API\n## Architecture\n## Usage\n")
        
        with open(os.path.join(readme_dir, "repo_bad.md"), 'w') as f:
            f.write("# Bad\n## Only One Section\n")
        
        candidates = [
            {"url": "https://github.com/test/good", "name": "repo_good"},
            {"url": "https://github.com/test/bad", "name": "repo_bad"}
        ]
        
        results = evaluate_repository_rubric(readme_dir, candidates)
        
        assert "evaluation_summary" in results
        assert results["evaluation_summary"]["total_repos"] == 2
        assert results["evaluation_summary"]["high_quality_count"] == 1
        
        # Check individual scores
        good_url = "https://github.com/test/good"
        bad_url = "https://github.com/test/bad"
        
        assert results["individual_scores"][good_url]["is_high_quality"] is True
        assert results["individual_scores"][bad_url]["is_high_quality"] is False
        
        # Cleanup
        shutil.rmtree(temp_dir)
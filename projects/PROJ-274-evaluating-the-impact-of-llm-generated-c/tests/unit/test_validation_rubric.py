import os
import tempfile
import json
import pytest
from validation import check_documentation_criteria, evaluate_repository_rubric, run_rubric_on_candidates

@pytest.fixture
def temp_repo_with_good_docs():
    """Create a temporary directory with a README.md that meets all criteria."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme_path = os.path.join(tmpdir, 'README.md')
        content = """
        # Test Repo

        ## Architecture
        This repo has a clear architecture description.

        ## Installation
        Run pip install -r requirements.txt

        ## API Reference
        Usage:
        ```python
        from test import func
        ```
        """
        with open(readme_path, 'w') as f:
            f.write(content)
        yield tmpdir

@pytest.fixture
def temp_repo_with_bad_docs():
    """Create a temporary directory with a README.md missing criteria."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme_path = os.path.join(tmpdir, 'README.md')
        content = """
        # Test Repo
        Just a simple readme.
        """
        with open(readme_path, 'w') as f:
            f.write(content)
        yield tmpdir

@pytest.fixture
def temp_repo_no_readme():
    """Create a temporary directory with no README.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_check_documentation_criteria_good(temp_repo_with_good_docs):
    criteria = check_documentation_criteria(temp_repo_with_good_docs)
    assert criteria['setup_instructions']['score'] == 1.0
    assert criteria['api_reference']['score'] == 1.0
    assert criteria['architecture']['score'] == 1.0

def test_check_documentation_criteria_bad(temp_repo_with_bad_docs):
    criteria = check_documentation_criteria(temp_repo_with_bad_docs)
    assert criteria['setup_instructions']['score'] == 0.0
    assert criteria['api_reference']['score'] == 0.0
    assert criteria['architecture']['score'] == 0.0

def test_check_documentation_criteria_no_readme(temp_repo_no_readme):
    criteria = check_documentation_criteria(temp_repo_no_readme)
    assert criteria['setup_instructions']['score'] == 0.0
    assert criteria['api_reference']['score'] == 0.0
    assert criteria['architecture']['score'] == 0.0

def test_evaluate_repository_rubric_pass(temp_repo_with_good_docs):
    result = evaluate_repository_rubric(temp_repo_with_good_docs)
    assert result['passed'] is True
    assert result['total_score'] == 3.0

def test_evaluate_repository_rubric_fail(temp_repo_with_bad_docs):
    result = evaluate_repository_rubric(temp_repo_with_bad_docs)
    assert result['passed'] is False
    assert result['total_score'] == 0.0

def test_evaluate_repository_rubric_threshold(temp_repo_no_readme):
    result = evaluate_repository_rubric(temp_repo_no_readme)
    assert result['passed'] is False
    assert result['total_score'] == 0.0

def test_run_rubric_on_candidates():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two repos: one good, one bad
        repo_good = os.path.join(tmpdir, 'good')
        repo_bad = os.path.join(tmpdir, 'bad')
        os.makedirs(repo_good)
        os.makedirs(repo_bad)
        
        # Good repo
        with open(os.path.join(repo_good, 'README.md'), 'w') as f:
            f.write("# Good\n## Architecture\n## Installation\n## API")
        
        # Bad repo
        with open(os.path.join(repo_bad, 'README.md'), 'w') as f:
            f.write("# Bad")

        results = run_rubric_on_candidates([repo_good, repo_bad])
        
        assert len(results) == 2
        assert results[0]['passed'] is True
        assert results[1]['passed'] is False

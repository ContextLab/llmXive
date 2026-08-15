"""
Unit tests for T021f: Documentation Quality Rubric Scoring.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from validation import (
    check_documentation_criteria,
    calculate_doc_quality_score,
    evaluate_repository_rubric,
    run_rubric_on_candidates
)

def test_check_documentation_criteria_setup():
    """Test detection of Setup section."""
    content = "# Project\n\n## Setup\nInstall dependencies with pip."
    criteria = check_documentation_criteria(content)
    assert criteria['has_setup'] is True
    assert criteria['has_api'] is False
    assert criteria['has_architecture'] is False

def test_check_documentation_criteria_api():
    """Test detection of API section."""
    content = "# Project\n\n## API\n\n### Function A\nThis function does X."
    criteria = check_documentation_criteria(content)
    assert criteria['has_setup'] is False
    assert criteria['has_api'] is True
    assert criteria['has_architecture'] is False

def test_check_documentation_criteria_architecture():
    """Test detection of Architecture section."""
    content = "# Project\n\n## Architecture\nThe system is composed of..."
    criteria = check_documentation_criteria(content)
    assert criteria['has_setup'] is False
    assert criteria['has_api'] is False
    assert criteria['has_architecture'] is True

def test_check_documentation_criteria_all():
    """Test detection of all sections."""
    content = """
    # Project
    ## Setup
    Install deps.
    ## API
    See functions.
    ## Architecture
    High level design.
    """
    criteria = check_documentation_criteria(content)
    assert criteria['has_setup'] is True
    assert criteria['has_api'] is True
    assert criteria['has_architecture'] is True

def test_calculate_doc_quality_score():
    """Test scoring logic."""
    # Score 0
    assert calculate_doc_quality_score({'has_setup': False, 'has_api': False, 'has_architecture': False}) == 0
    # Score 1
    assert calculate_doc_quality_score({'has_setup': True, 'has_api': False, 'has_architecture': False}) == 1
    # Score 3
    assert calculate_doc_quality_score({'has_setup': True, 'has_api': True, 'has_architecture': True}) == 3

def test_evaluate_repository_rubric():
    """Test full evaluation on a mock repo."""
    # Create a temp directory with a mock repo and README
    temp_dir = tempfile.mkdtemp()
    try:
        readme_path = os.path.join(temp_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write("# Repo\n## Setup\n## API\n## Architecture")
        
        result = evaluate_repository_rubric(temp_dir)
        assert result['repo_path'] == temp_dir
        assert result['criteria']['has_setup'] is True
        assert result['criteria']['has_api'] is True
        assert result['criteria']['has_architecture'] is True
        assert result['doc_quality_score'] == 3
    finally:
        shutil.rmtree(temp_dir)

def test_run_rubric_on_candidates():
    """Test the main function that writes output."""
    temp_dir = tempfile.mkdtemp()
    try:
        repo1 = os.path.join(temp_dir, "repo1")
        os.makedirs(repo1)
        with open(os.path.join(repo1, "README.md"), 'w') as f:
            f.write("# Repo\n## Setup")
        
        output_file = os.path.join(temp_dir, "scores.json")
        
        run_rubric_on_candidates([repo1], output_file)
        
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['doc_quality_score'] == 1
        assert data[0]['criteria']['has_setup'] is True
    finally:
        shutil.rmtree(temp_dir)
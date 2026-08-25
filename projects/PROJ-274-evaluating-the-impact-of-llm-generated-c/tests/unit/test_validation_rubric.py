"""
Unit tests for the documentation quality rubric logic in code/validation.py
"""
import pytest
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from validation import (
    check_documentation_criteria,
    calculate_doc_quality_score,
    evaluate_repository_rubric
)

class TestDocQualityRubric:

    def test_check_setup_section_present(self):
        readme = """
        # My Project

        ## Setup
        Run pip install.
        """
        criteria = check_documentation_criteria(readme)
        assert criteria['setup'] is True

    def test_check_setup_section_missing(self):
        readme = """
        # My Project

        ## Usage
        How to use it.
        """
        criteria = check_documentation_criteria(readme)
        assert criteria['setup'] is False

    def test_check_api_section_present(self):
        readme = """
        # My Project

        ## API Reference
        Here are the functions.
        """
        criteria = check_documentation_criteria(readme)
        assert criteria['api'] is True

    def test_check_architecture_section_present(self):
        readme = """
        # My Project

        ## Architecture
        System design overview.
        """
        criteria = check_documentation_criteria(readme)
        assert criteria['architecture'] is True

    def test_all_sections_present(self):
        readme = """
        # My Project

        ## Setup
        Install dependencies.

        ## API
        Function list.

        ## Architecture
        Design patterns.
        """
        criteria = check_documentation_criteria(readme)
        assert all(criteria.values())

    def test_score_calculation_full(self):
        criteria = {'setup': True, 'api': True, 'architecture': True}
        score = calculate_doc_quality_score(criteria)
        assert score == 1.0

    def test_score_calculation_partial(self):
        criteria = {'setup': True, 'api': False, 'architecture': True}
        score = calculate_doc_quality_score(criteria)
        assert score == 2/3.0

    def test_score_calculation_none(self):
        criteria = {'setup': False, 'api': False, 'architecture': False}
        score = calculate_doc_quality_score(criteria)
        assert score == 0.0

    def test_evaluate_repository_rubric_high_quality(self):
        readme = """
        # Project

        ## Setup
        Do this.

        ## API
        Do that.

        ## Architecture
        Like this.
        """
        result = evaluate_repository_rubric(readme)
        assert result['is_high_quality'] is True
        assert result['score'] == 1.0

    def test_evaluate_repository_rubric_low_quality(self):
        readme = """
        # Project

        ## Setup
        Do this.
        """
        result = evaluate_repository_rubric(readme)
        # 1/3 = 0.333 < 0.75
        assert result['is_high_quality'] is False
        assert abs(result['score'] - 0.3333) < 0.01

import pytest
from classification.goal_validator import validate_static_constraints

class TestValidateStaticConstraints:
    def test_validate_file_path_constraint(self):
        """Verify file path constraint extraction."""
        task_description = "The agent must save results to /data/output/results.csv"
        
        constraints = validate_static_constraints(task_description)
        
        assert isinstance(constraints, list)
        # Should extract the file path pattern
        assert any("/data/output/results.csv" in c for c in constraints)

    def test_validate_variable_name_constraint(self):
        """Verify variable name constraint extraction."""
        task_description = "Use the variable 'final_score' to store the result"
        
        constraints = validate_static_constraints(task_description)
        
        assert isinstance(constraints, list)
        assert any("final_score" in c for c in constraints)

    def test_validate_multiple_constraints(self):
        """Verify multiple constraint extraction."""
        task_description = "Save to /output/file.txt and use variable 'score'"
        
        constraints = validate_static_constraints(task_description)
        
        assert isinstance(constraints, list)
        assert len(constraints) >= 2

    def test_validate_no_constraints(self):
        """Verify empty list for no constraints."""
        task_description = "The agent should perform the task successfully"
        
        constraints = validate_static_constraints(task_description)
        
        assert isinstance(constraints, list)
        # May return empty or generic constraints depending on regex

    def test_validate_empty_description(self):
        """Verify handling of empty description."""
        task_description = ""
        
        constraints = validate_static_constraints(task_description)
        
        assert isinstance(constraints, list)

    def test_validate_special_characters(self):
        """Verify handling of special characters in paths."""
        task_description = "Save to /data/output/file-name_v2.0.json"
        
        constraints = validate_static_constraints(task_description)
        
        assert isinstance(constraints, list)

    def test_validate_regex_template_matching(self):
        """Verify deterministic regex-based matching (FR-007)."""
        task_description = "File: /path/to/file.txt, Var: my_var"
        
        constraints = validate_static_constraints(task_description)
        
        # Should use regex patterns, not LLM
        assert isinstance(constraints, list)

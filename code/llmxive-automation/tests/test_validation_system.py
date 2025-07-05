"""Tests for the validation system."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timezone
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from validation import (
    ValidationCheck, ValidationResult,
    TechnicalDesignValidator,
    ImplementationPlanValidator,
    CodeValidator,
    PaperValidator,
    ReviewValidator,
    DataValidator,
    GitHubIssue,
    GitHubIssueValidator,
    GitHubLabelValidator,
    ProjectBoardValidator,
    StageConsistencyValidator,
    ValidationReportGenerator
)
from scoring.stage_manager import ProjectStage


class TestValidationBase:
    """Test base validation classes."""
    
    def test_validation_check(self):
        """Test ValidationCheck creation and string representation."""
        check = ValidationCheck(
            name="test_check",
            passed=True,
            message="Test passed",
            severity="info"
        )
        
        assert check.name == "test_check"
        assert check.passed
        assert check.severity == "info"
        assert "✓" in str(check)
    
    def test_validation_result(self):
        """Test ValidationResult functionality."""
        result = ValidationResult("test_type", "test-123")
        
        # Add checks
        result.add_check("check1", True, "Passed check", "info")
        result.add_check("check2", False, "Failed check", "error")
        result.add_check("check3", False, "Warning check", "warning")
        
        assert len(result.checks) == 3
        assert not result.passed  # Has errors
        assert result.has_warnings
        assert result.passed_count == 1
        assert result.failed_count == 2
        assert len(result.get_errors()) == 1
        assert len(result.get_warnings()) == 1
        
        # Test summary
        summary = result.summary()
        assert "FAILED" in summary
        assert "1/3" in summary
        assert "1 warnings" in summary


class TestFileValidators:
    """Test file validators."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_technical_design_validator(self):
        """Test technical design document validation."""
        # Create test structure
        design_dir = self.test_path / "technical_design_documents" / "test-project"
        design_dir.mkdir(parents=True)
        
        # Create valid design document
        design_file = design_dir / "design.md"
        design_file.write_text("""
# Technical Design

## Problem Statement
Test problem description.

## Proposed Solution
Test solution description.

## Implementation Details
Detailed implementation.

## Validation Strategy
How to validate.

Related to issue #123.
        """)
        
        # Create README
        readme = self.test_path / "technical_design_documents" / "README.md"
        readme.write_text("| Project | test-project | Status |\n")
        
        # Validate
        validator = TechnicalDesignValidator(self.test_path / "technical_design_documents")
        result = validator.validate("test-project", {'github_issue': 123})
        
        assert result.passed
        assert result.passed_count >= 6  # All required sections + issue ref
    
    def test_implementation_plan_validator(self):
        """Test implementation plan validation."""
        # Create test structure
        plan_dir = self.test_path / "implementation_plans" / "test-project"
        plan_dir.mkdir(parents=True)
        
        # Create valid plan
        plan_file = plan_dir / "plan.md"
        plan_file.write_text("""
# Implementation Plan

## Overview
Plan overview.

## Milestones
- Milestone 1
- Milestone 2

## Timeline
Week 1-2: Setup
Week 3-4: Implementation

## Resource Requirements
- 2 developers
- GPU cluster

## Risk Management
Potential risks and mitigations.
        """)
        
        # Validate
        validator = ImplementationPlanValidator(self.test_path / "implementation_plans")
        result = validator.validate("test-project")
        
        assert result.passed
        assert any(c.name == "has_timeline" and c.passed for c in result.checks)
    
    def test_code_validator(self):
        """Test code artifact validation."""
        # Create test structure
        code_dir = self.test_path / "code" / "test-project"
        code_dir.mkdir(parents=True)
        
        # Create README
        (code_dir / "README.md").write_text("# Test Project\n")
        
        # Create helpers directory
        helpers_dir = code_dir / "helpers"
        helpers_dir.mkdir()
        (helpers_dir / "__init__.py").write_text("")
        (helpers_dir / "setup.py").write_text("")
        
        # Create requirements
        (code_dir / "requirements.txt").write_text("numpy\npandas\n")
        
        # Create tests
        test_dir = code_dir / "tests"
        test_dir.mkdir()
        (test_dir / "test_basic.py").write_text("def test_example(): pass")
        
        # Validate
        validator = CodeValidator(self.test_path / "code")
        result = validator.validate("test-project")
        
        assert result.passed
        assert any(c.name == "has_tests" and c.passed for c in result.checks)
        assert any(c.name == "has_requirements" and c.passed for c in result.checks)
    
    def test_paper_validator(self):
        """Test paper artifact validation."""
        # Create test structure
        paper_dir = self.test_path / "papers" / "test-project"
        paper_dir.mkdir(parents=True)
        
        # Create LaTeX file
        tex_file = paper_dir / "paper.tex"
        tex_file.write_text(r"""
\documentclass{article}
\begin{document}

\section{Introduction}
Introduction text.

\section{Methods}
Methods description.

\section{Results}
Results presentation.

\section{Discussion}
Discussion of findings.

\end{document}
        """)
        
        # Create bibliography
        (paper_dir / "references.bib").write_text("")
        
        # Create figures directory
        (paper_dir / "figures").mkdir()
        
        # Validate (not in done stage)
        validator = PaperValidator(self.test_path / "papers")
        result = validator.validate("test-project", {'stage': 'in_review'})
        
        assert result.passed
        assert any(c.name == "has_bibliography" and c.passed for c in result.checks)
        
        # Validate done stage (should warn about missing PDF)
        result_done = validator.validate("test-project", {'stage': 'done'})
        assert any(c.name == "has_pdf" and not c.passed for c in result_done.checks)
    
    def test_review_validator(self):
        """Test review document validation."""
        # Create test structure
        review_dir = self.test_path / "reviews" / "test-project" / "Design"
        review_dir.mkdir(parents=True)
        
        # Create valid review
        review_file = review_dir / "alice__12-25-2024__A.md"
        review_file.write_text("""
## Review

This is a comprehensive review of the design.

Score: APPROVE

The approach is sound and well-thought-out.
        """)
        
        # Validate
        validator = ReviewValidator(self.test_path / "reviews")
        result = validator.validate("test-project/Design/alice__12-25-2024__A.md")
        
        assert result.passed
        assert any(c.name == "filename_format" and c.passed for c in result.checks)
        assert any(c.name == "has_score_indication" and c.passed for c in result.checks)
    
    def test_data_validator(self):
        """Test data artifact validation."""
        # Create test structure
        data_dir = self.test_path / "data" / "test-project"
        data_dir.mkdir(parents=True)
        
        # Create README
        (data_dir / "README.md").write_text("# Test Data\n")
        
        # Create data files
        (data_dir / "data.csv").write_text("col1,col2\n1,2\n")
        (data_dir / "metadata.json").write_text('{"description": "test"}')
        
        # Validate
        validator = DataValidator(self.test_path / "data")
        result = validator.validate("test-project")
        
        assert result.passed
        assert any(c.name == "has_data_files" and c.passed for c in result.checks)
        assert any(c.name == "has_metadata" and c.passed for c in result.checks)


class TestGitHubValidators:
    """Test GitHub validators."""
    
    def test_github_issue_validator(self):
        """Test GitHub issue validation."""
        # Create test issue
        issue = GitHubIssue(
            number=123,
            title="Implement new feature for project-abc",
            state="open",
            labels=["in-progress", "enhancement"],
            body="This issue tracks the implementation of..." * 10,
            assignees=["user1", "user2"]
        )
        
        # Validate
        validator = GitHubIssueValidator()
        result = validator.validate("123", {
            'issue': issue,
            'expected_stage': ProjectStage.IN_PROGRESS
        })
        
        assert result.passed
        assert any(c.name == "stage_label" and c.passed for c in result.checks)
        # Project ID check is optional - the title contains "project-abc"
        project_id_check = next((c for c in result.checks if c.name == "has_project_id"), None)
        if project_id_check:
            assert project_id_check.passed
        assert any(c.name == "has_assignees" and c.passed for c in result.checks)
    
    def test_github_label_validator(self):
        """Test repository label validation."""
        labels = [
            "backlog", "ready", "in-progress", "in-review", "done",
            "needs-review", "critical-review", "blocked",
            "bug", "enhancement"
        ]
        
        # Validate
        validator = GitHubLabelValidator()
        result = validator.validate("test-repo", {'labels': labels})
        
        assert result.passed
        assert result.passed_count >= len(GitHubLabelValidator.REQUIRED_LABELS)
    
    def test_project_board_validator(self):
        """Test project board validation."""
        from validation.github_validators import ProjectCard
        
        columns = ["Backlog", "Ready", "In Progress", "In Review", "Done"]
        cards = [
            ProjectCard(1, "Backlog", issue_number=101),
            ProjectCard(2, "In Progress", issue_number=102),
            ProjectCard(3, "Done", issue_number=103)
        ]
        
        # Validate
        validator = ProjectBoardValidator()
        result = validator.validate("Main Board", {
            'columns': columns,
            'cards': cards
        })
        
        assert result.passed
        assert any(c.name == "column_order" and c.passed for c in result.checks)
    
    def test_stage_consistency_validator(self):
        """Test stage consistency validation."""
        issue = GitHubIssue(
            number=123,
            title="Test project",
            state="open",
            labels=["in-progress"]
        )
        
        # Validate
        validator = StageConsistencyValidator()
        result = validator.validate("test-project", {
            'issue': issue,
            'card_column': "In Progress",
            'stage': ProjectStage.IN_PROGRESS,
            'score': 0.5
        })
        
        assert result.passed
        assert any(c.name == "label_stage_match" and c.passed for c in result.checks)
        assert any(c.name == "column_stage_match" and c.passed for c in result.checks)


class TestReportGenerator:
    """Test validation report generation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = ValidationReportGenerator(Path(self.temp_dir) / "reports")
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_validate_project(self):
        """Test full project validation."""
        # Create mock project data
        issue = GitHubIssue(
            number=123,
            title="Test project implementation",
            state="open",
            labels=["in-progress"]
        )
        
        project_data = {
            'stage': ProjectStage.IN_PROGRESS,
            'github_issue': issue,
            'repository_labels': ["backlog", "ready", "in-progress", "done"],
            'score': 2.5,
            'card_column': "In Progress"
        }
        
        # Run validation
        results = self.generator.validate_project("test-project", project_data)
        
        assert 'summary' in results
        assert results['summary']['total_checks'] > 0
        assert 'file_validations' in results
        assert 'github_validations' in results
    
    def test_markdown_report_generation(self):
        """Test markdown report generation."""
        # Create sample results
        results = {
            'project_id': 'test-project',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'overall_status': 'PASSED_WITH_WARNINGS',
                'pass_rate': 85.0,
                'total_checks': 20,
                'passed_checks': 17,
                'failed_checks': 3,
                'errors': 1,
                'warnings': 2,
                'info': 15
            },
            'file_validations': {},
            'github_validations': {}
        }
        
        # Add a sample validation
        val_result = ValidationResult("test_type", "test-123")
        val_result.add_check("check1", True, "Passed")
        val_result.add_check("check2", False, "Failed", "error")
        results['file_validations']['test'] = val_result
        
        # Generate report
        report = self.generator.generate_markdown_report("test-project", results)
        
        assert "# Validation Report: test-project" in report
        assert "PASSED_WITH_WARNINGS" in report
        assert "85.0%" in report
        assert "Errors:" in report
    
    def test_json_report_generation(self):
        """Test JSON report generation."""
        # Create sample results
        results = {
            'project_id': 'test-project',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {'overall_status': 'PASSED'},
            'file_validations': {},
            'github_validations': {}
        }
        
        # Generate report
        json_report = self.generator.generate_json_report("test-project", results)
        
        # Verify it's valid JSON
        import json
        parsed = json.loads(json_report)
        assert parsed['project_id'] == 'test-project'
        assert 'summary' in parsed
    
    def test_save_report(self):
        """Test saving reports to files."""
        results = {
            'project_id': 'test-project',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {'overall_status': 'PASSED', 'total_checks': 10},
            'file_validations': {},
            'github_validations': {}
        }
        
        # Save reports
        saved = self.generator.save_report("test-project", results)
        
        assert 'markdown' in saved
        assert 'json' in saved
        assert saved['markdown'].exists()
        assert saved['json'].exists()
        
        # Check latest symlinks
        latest_md = self.generator.output_dir / "test-project_latest.md"
        latest_json = self.generator.output_dir / "test-project_latest.json"
        assert latest_md.exists()
        assert latest_json.exists()
    
    def test_summary_dashboard(self):
        """Test dashboard generation for multiple projects."""
        # Create multiple project results
        all_results = [
            {
                'project_id': 'project-1',
                'summary': {
                    'overall_status': 'PASSED',
                    'pass_rate': 100.0,
                    'total_checks': 20,
                    'passed_checks': 20,
                    'errors': 0,
                    'warnings': 0
                },
                'file_validations': {},
                'github_validations': {}
            },
            {
                'project_id': 'project-2',
                'summary': {
                    'overall_status': 'FAILED',
                    'pass_rate': 60.0,
                    'total_checks': 20,
                    'passed_checks': 12,
                    'errors': 5,
                    'warnings': 3
                },
                'file_validations': {},
                'github_validations': {}
            }
        ]
        
        # Generate dashboard
        dashboard = self.generator.generate_summary_dashboard(all_results)
        
        assert "# llmXive Validation Dashboard" in dashboard
        assert "Projects Validated: 2" in dashboard
        assert "project-1" in dashboard
        assert "project-2" in dashboard
        assert "FAILED" in dashboard


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
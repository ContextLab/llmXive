"""File validators for llmXive artifacts."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from .base import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class TechnicalDesignValidator(BaseValidator):
    """Validator for technical design documents."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize with base path to technical_design_documents folder."""
        super().__init__(base_path or Path("technical_design_documents"))
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate a technical design document.
        
        Args:
            item_id: Project ID
            context: Optional context (e.g., {'github_issue': 123})
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("technical_design", item_id)
        
        # Check main design file
        design_dir = self.base_path / item_id
        design_file = design_dir / "design.md"
        
        if not self.check_directory_exists(design_dir, result):
            return result
        
        if not self.check_file_exists(design_file, result):
            return result
        
        # Check required sections
        required_sections = [
            "# Technical Design",
            "## Problem Statement",
            "## Proposed Solution",
            "## Implementation Details",
            "## Validation Strategy"
        ]
        
        self.check_file_content(design_file, required_sections, result)
        
        # Check for GitHub issue reference if context provided
        if context and 'github_issue' in context:
            issue_ref = f"#{context['github_issue']}"
            self.check_file_content(design_file, [issue_ref], result)
        
        # Check README table entry
        readme_path = self.base_path / "README.md"
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text()
                has_entry = item_id in readme_content
                
                result.add_check(
                    name="readme_table_entry",
                    passed=has_entry,
                    message=f"Project {'found' if has_entry else 'missing'} in README table",
                    severity="warning" if not has_entry else "info"
                )
            except Exception as e:
                logger.error(f"Failed to check README: {e}")
        
        return result


class ImplementationPlanValidator(BaseValidator):
    """Validator for implementation plans."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize with base path to implementation_plans folder."""
        super().__init__(base_path or Path("implementation_plans"))
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate an implementation plan.
        
        Args:
            item_id: Project ID
            context: Optional context
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("implementation_plan", item_id)
        
        # Check main plan file
        plan_dir = self.base_path / item_id
        plan_file = plan_dir / "plan.md"
        
        if not self.check_directory_exists(plan_dir, result):
            return result
        
        if not self.check_file_exists(plan_file, result):
            return result
        
        # Check required sections
        required_sections = [
            "# Implementation Plan",
            "## Overview",
            "## Milestones",
            "## Resource Requirements",
            "## Risk"  # Risk Management or Risk Mitigation
        ]
        
        self.check_file_content(plan_file, required_sections, result)
        
        # Check for timeline/schedule
        timeline_patterns = ["## Timeline", "## Schedule", "## Implementation Schedule"]
        has_timeline = False
        try:
            content = plan_file.read_text()
            has_timeline = any(pattern in content for pattern in timeline_patterns)
        except:
            pass
        
        result.add_check(
            name="has_timeline",
            passed=has_timeline,
            message="Timeline/schedule section " + ("found" if has_timeline else "missing"),
            severity="warning" if not has_timeline else "info"
        )
        
        return result


class CodeValidator(BaseValidator):
    """Validator for code artifacts."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize with base path to code folder."""
        super().__init__(base_path or Path("code"))
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate code artifacts for a project.
        
        Args:
            item_id: Project ID
            context: Optional context
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("code", item_id)
        
        # Check project directory
        project_dir = self.base_path / item_id
        if not self.check_directory_exists(project_dir, result):
            return result
        
        # Check README
        readme = project_dir / "README.md"
        self.check_file_exists(readme, result)
        
        # Check helpers directory
        helpers_dir = project_dir / "helpers"
        if self.check_directory_exists(helpers_dir, result):
            # Check for __init__.py
            init_file = helpers_dir / "__init__.py"
            self.check_file_exists(init_file, result, required=False)
            
            # Check for setup.py or pyproject.toml
            setup_py = helpers_dir / "setup.py"
            pyproject = helpers_dir / "pyproject.toml"
            has_setup = setup_py.exists() or pyproject.exists()
            
            result.add_check(
                name="has_setup_file",
                passed=has_setup,
                message="Package setup file " + ("found" if has_setup else "missing"),
                severity="warning"
            )
        
        # Check for requirements file
        requirements_files = ["requirements.txt", "requirements.in", "pyproject.toml"]
        has_requirements = any((project_dir / f).exists() for f in requirements_files)
        
        result.add_check(
            name="has_requirements",
            passed=has_requirements,
            message="Requirements file " + ("found" if has_requirements else "missing"),
            severity="warning"
        )
        
        # Check for tests
        test_patterns = ["tests", "test", "test_*.py", "*_test.py"]
        has_tests = False
        
        for pattern in test_patterns:
            if pattern.endswith(".py"):
                has_tests = bool(list(project_dir.glob(pattern)))
            else:
                test_dir = project_dir / pattern
                has_tests = test_dir.exists() and test_dir.is_dir()
            
            if has_tests:
                break
        
        result.add_check(
            name="has_tests",
            passed=has_tests,
            message="Test files/directory " + ("found" if has_tests else "missing"),
            severity="warning"
        )
        
        return result


class PaperValidator(BaseValidator):
    """Validator for paper artifacts."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize with base path to papers folder."""
        super().__init__(base_path or Path("papers"))
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate paper artifacts.
        
        Args:
            item_id: Project ID
            context: Optional context (e.g., {'stage': 'in_review'})
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("paper", item_id)
        
        # Check project directory
        paper_dir = self.base_path / item_id
        if not self.check_directory_exists(paper_dir, result):
            return result
        
        # Check for LaTeX files
        tex_files = list(paper_dir.glob("*.tex"))
        has_tex = len(tex_files) > 0
        
        result.add_check(
            name="has_latex_files",
            passed=has_tex,
            message=f"LaTeX files: {len(tex_files)} found",
            severity="error" if not has_tex else "info"
        )
        
        # Check main paper file
        main_tex_candidates = ["paper.tex", "main.tex", f"{item_id}.tex"]
        main_tex = None
        
        for candidate in main_tex_candidates:
            if (paper_dir / candidate).exists():
                main_tex = paper_dir / candidate
                break
        
        if main_tex:
            result.add_check(
                name="has_main_tex",
                passed=True,
                message=f"Main LaTeX file found: {main_tex.name}"
            )
            
            # Check for required sections
            required_sections = [
                r"\\section\{.*Introduction",
                r"\\section\{.*Methods",
                r"\\section\{.*Results",
                r"\\section\{.*Discussion"
            ]
            
            try:
                content = main_tex.read_text()
                for section in required_sections:
                    has_section = bool(re.search(section, content, re.IGNORECASE))
                    section_name = section.split("{")[1].split("}")[0]
                    
                    result.add_check(
                        name=f"has_section_{section_name.lower()}",
                        passed=has_section,
                        message=f"{section_name} section " + ("found" if has_section else "missing"),
                        severity="warning" if not has_section else "info"
                    )
            except Exception as e:
                logger.error(f"Failed to check sections: {e}")
        else:
            result.add_check(
                name="has_main_tex",
                passed=False,
                message="No main LaTeX file found (paper.tex, main.tex, or project.tex)"
            )
        
        # Check for PDF if in done stage
        if context and context.get('stage') == 'done':
            pdf_files = list(paper_dir.glob("*.pdf"))
            has_pdf = len(pdf_files) > 0
            
            result.add_check(
                name="has_pdf",
                passed=has_pdf,
                message=f"PDF file {'found' if has_pdf else 'missing'} (required for Done stage)",
                severity="error"
            )
        
        # Check for figures directory
        figures_dir = paper_dir / "figures"
        self.check_directory_exists(figures_dir, result, required=False)
        
        # Check for bibliography
        bib_files = list(paper_dir.glob("*.bib"))
        has_bib = len(bib_files) > 0
        
        result.add_check(
            name="has_bibliography",
            passed=has_bib,
            message=f"Bibliography file {'found' if has_bib else 'missing'}",
            severity="warning"
        )
        
        return result


class ReviewValidator(BaseValidator):
    """Validator for review documents."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize with base path to reviews folder."""
        super().__init__(base_path or Path("reviews"))
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate review artifacts.
        
        Args:
            item_id: Review file path (e.g., "project-123/Design/reviewer__MM-DD-YYYY__A.md")
            context: Optional context
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("review", item_id)
        
        # Parse the review path
        review_path = self.base_path / item_id
        
        if not self.check_file_exists(review_path, result):
            return result
        
        # Validate filename format
        filename = review_path.name
        pattern = r"^[a-zA-Z0-9_-]+__\d{2}-\d{2}-\d{4}__[AM]\.md$"
        valid_format = bool(re.match(pattern, filename))
        
        result.add_check(
            name="filename_format",
            passed=valid_format,
            message=f"Filename format {'valid' if valid_format else 'invalid'} (expected: author__MM-DD-YYYY__[A|M].md)"
        )
        
        # Check review content
        required_patterns = [
            "## Review",
            "Score:"  # Should contain score indication
        ]
        
        self.check_file_content(review_path, required_patterns, result)
        
        # Check for score indication
        try:
            content = review_path.read_text()
            
            # Look for score patterns
            score_patterns = [
                r"Score:\s*APPROVE",
                r"Score:\s*NEEDS[_\s]REVISION",
                r"Score:\s*CRITICAL",
                r"Score:\s*\+[\d.]+",
                r"Score:\s*-[\d.]+",
                r"Score:\s*NEEDS[_\s]IMPROVEMENT"
            ]
            
            has_score = any(re.search(pattern, content, re.IGNORECASE) for pattern in score_patterns)
            
            result.add_check(
                name="has_score_indication",
                passed=has_score,
                message="Score indication " + ("found" if has_score else "missing")
            )
            
        except Exception as e:
            logger.error(f"Failed to check review content: {e}")
        
        return result


class DataValidator(BaseValidator):
    """Validator for data artifacts."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize with base path to data folder."""
        super().__init__(base_path or Path("data"))
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate data artifacts.
        
        Args:
            item_id: Project ID
            context: Optional context
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("data", item_id)
        
        # Check project directory
        data_dir = self.base_path / item_id
        if not self.check_directory_exists(data_dir, result):
            return result
        
        # Check README
        readme = data_dir / "README.md"
        self.check_file_exists(readme, result)
        
        # Check for data files
        data_extensions = ['.csv', '.json', '.npz', '.npy', '.pkl', '.h5', '.hdf5', '.parquet']
        data_files = []
        
        for ext in data_extensions:
            data_files.extend(data_dir.glob(f"*{ext}"))
        
        has_data = len(data_files) > 0
        
        result.add_check(
            name="has_data_files",
            passed=has_data,
            message=f"Data files: {len(data_files)} found",
            severity="warning" if not has_data else "info",
            details={"files": [f.name for f in data_files[:10]]}  # First 10 files
        )
        
        # Check for metadata
        metadata_files = ["metadata.json", "metadata.yaml", "metadata.yml"]
        has_metadata = any((data_dir / f).exists() for f in metadata_files)
        
        result.add_check(
            name="has_metadata",
            passed=has_metadata,
            message="Metadata file " + ("found" if has_metadata else "missing"),
            severity="warning"
        )
        
        return result
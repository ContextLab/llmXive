import pytest
from pathlib import Path
import tempfile
import os
from code.utils.verify_spec_anova import verify_anova_mention

def test_verify_anova_mention_success():
    """Test that verification passes when both files contain the required text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create spec.md with FR-007 and the required phrase
        spec_path = Path(tmpdir) / "spec.md"
        spec_content = """
        # Specification
        
        ## Functional Requirements
        
        ### FR-007
        The system shall perform One-way ANOVA and Tukey HSD for statistical analysis.
        """
        spec_path.write_text(spec_content)
        
        # Create plan.md with Methodology and the required phrase
        plan_path = Path(tmpdir) / "plan.md"
        plan_content = """
        # Project Plan
        
        ## Methodology
        
        We will use One-way ANOVA and Tukey HSD to analyze the results.
        """
        plan_path.write_text(plan_content)
        
        result = verify_anova_mention(str(spec_path), str(plan_path))
        assert result is True

def test_verify_anova_mention_missing_spec_phrase():
    """Test that verification fails when spec.md lacks the required phrase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create spec.md with FR-007 but without the required phrase
        spec_path = Path(tmpdir) / "spec.md"
        spec_content = """
        # Specification
        
        ## Functional Requirements
        
        ### FR-007
        The system shall perform statistical analysis.
        """
        spec_path.write_text(spec_content)
        
        # Create plan.md with Methodology and the required phrase
        plan_path = Path(tmpdir) / "plan.md"
        plan_content = """
        # Project Plan
        
        ## Methodology
        
        We will use One-way ANOVA and Tukey HSD to analyze the results.
        """
        plan_path.write_text(plan_content)
        
        result = verify_anova_mention(str(spec_path), str(plan_path))
        assert result is False

def test_verify_anova_mention_missing_plan_phrase():
    """Test that verification fails when plan.md lacks the required phrase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create spec.md with FR-007 and the required phrase
        spec_path = Path(tmpdir) / "spec.md"
        spec_content = """
        # Specification
        
        ## Functional Requirements
        
        ### FR-007
        The system shall perform One-way ANOVA and Tukey HSD for statistical analysis.
        """
        spec_path.write_text(spec_content)
        
        # Create plan.md with Methodology but without the required phrase
        plan_path = Path(tmpdir) / "plan.md"
        plan_content = """
        # Project Plan
        
        ## Methodology
        
        We will perform statistical analysis.
        """
        plan_path.write_text(plan_content)
        
        result = verify_anova_mention(str(spec_path), str(plan_path))
        assert result is False

def test_verify_anova_mention_missing_fr():
    """Test that verification fails when FR-007 is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create spec.md without FR-007
        spec_path = Path(tmpdir) / "spec.md"
        spec_content = """
        # Specification
        
        ## Functional Requirements
        
        ### FR-006
        The system shall do something else.
        """
        spec_path.write_text(spec_content)
        
        # Create plan.md with Methodology and the required phrase
        plan_path = Path(tmpdir) / "plan.md"
        plan_content = """
        # Project Plan
        
        ## Methodology
        
        We will use One-way ANOVA and Tukey HSD to analyze the results.
        """
        plan_path.write_text(plan_content)
        
        result = verify_anova_mention(str(spec_path), str(plan_path))
        assert result is False

def test_verify_anova_mention_missing_methodology():
    """Test that verification fails when Methodology section is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create spec.md with FR-007 and the required phrase
        spec_path = Path(tmpdir) / "spec.md"
        spec_content = """
        # Specification
        
        ## Functional Requirements
        
        ### FR-007
        The system shall perform One-way ANOVA and Tukey HSD for statistical analysis.
        """
        spec_path.write_text(spec_content)
        
        # Create plan.md without Methodology section
        plan_path = Path(tmpdir) / "plan.md"
        plan_content = """
        # Project Plan
        
        ## Overview
        
        This project will do amazing things.
        """
        plan_path.write_text(plan_content)
        
        result = verify_anova_mention(str(spec_path), str(plan_path))
        assert result is False

def test_verify_anova_mention_missing_files():
    """Test that verification fails when files don't exist."""
    result = verify_anova_mention("nonexistent_spec.md", "nonexistent_plan.md")
    assert result is False

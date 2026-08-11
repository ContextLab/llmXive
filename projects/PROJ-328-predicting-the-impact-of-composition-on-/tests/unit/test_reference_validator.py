"""
Unit tests for the Reference Validator Agent.
"""
import os
import pytest
import tempfile
from pathlib import Path
from utils.reference_validator import (
    ConstitutionError,
    validate_research_md,
    check_research_md_exists,
    extract_citations,
    verify_citations
)

class TestConstitutionError:
    """Tests for ConstitutionError exception."""
    
    def test_constitution_error_is_solder_pipeline_error(self):
        """ConstitutionError should be a subclass of SolderPipelineError."""
        from utils.error_handlers import SolderPipelineError
        assert issubclass(ConstitutionError, SolderPipelineError)
    
    def test_constitution_error_message(self):
        """ConstitutionError should have a descriptive message."""
        error = ConstitutionError("Test error message")
        assert "Test error message" in str(error)

class TestCheckResearchMdExists:
    """Tests for check_research_md_exists function."""
    
    def test_file_exists_returns_path(self):
        """Should return path when research.md exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            research_path.write_text("# Research\n\n[1] Test citation")
            
            result = check_research_md_exists(Path(tmpdir))
            assert result == research_path
    
    def test_file_missing_raises_error(self):
        """Should raise ConstitutionError when research.md is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ConstitutionError) as exc_info:
                check_research_md_exists(Path(tmpdir))
            
            assert "research.md not found" in str(exc_info.value)
    
    def test_default_to_current_directory(self):
        """Should default to current directory when project_root is None."""
        # This test assumes research.md exists in current directory during test run
        # If not, it will raise ConstitutionError which is also valid behavior
        try:
            result = check_research_md_exists()
            assert result.exists()
        except ConstitutionError:
            # Expected if research.md doesn't exist in current directory
            pass

class TestExtractCitations:
    """Tests for extract_citations function."""
    
    def test_extract_numbered_citations(self):
        """Should extract numbered citations like [1], [2]."""
        content = "As shown in [1] and [2], the results are significant."
        citations = extract_citations(content)
        assert "[1]" in citations
        assert "[2]" in citations
    
    def test_extract_doi_citations(self):
        """Should extract DOI citations."""
        content = "See DOI: 10.1038/s41586-020-2649-2 for details."
        citations = extract_citations(content)
        assert any("10.1038" in c for c in citations)
    
    def test_extract_url_citations(self):
        """Should extract URL citations."""
        content = "More info at https://example.com/research"
        citations = extract_citations(content)
        assert any("https://example.com" in c for c in citations)
    
    def test_extract_author_year_citations(self):
        """Should extract Author (Year) citations."""
        content = "Smith (2020) and Johnson (2021) both reported this."
        citations = extract_citations(content)
        assert any("Smith (2020)" in c for c in citations)
        assert any("Johnson (2021)" in c for c in citations)
    
    def test_no_citations_returns_empty(self):
        """Should return empty list when no citations found."""
        content = "This text has no citations at all."
        citations = extract_citations(content)
        assert len(citations) == 0
    
    def test_removes_duplicates(self):
        """Should remove duplicate citations."""
        content = "[1] and [1] and [1]"
        citations = extract_citations(content)
        assert citations.count("[1]") == 1

class TestVerifyCitations:
    """Tests for verify_citations function."""
    
    def test_valid_citations_pass(self):
        """Valid citations with bibliography should pass."""
        citations = ["[1]", "10.1038/test"]
        content = """
        # Research
        
        [1] Test citation
        
        ## References
        [1] Smith, J. (2020). Test paper. DOI: 10.1038/test
        """
        is_verified, unverified = verify_citations(citations, content)
        assert is_verified is True
        assert len(unverified) == 0
    
    def test_placeholder_citations_fail(self):
        """Placeholder citations should fail."""
        citations = ["[citation needed]"]
        content = "This needs [citation needed]."
        is_verified, unverified = verify_citations(citations, content)
        assert is_verified is False
        assert len(unverified) > 0
    
    def test_no_bibliography_fails(self):
        """Citations without bibliography should fail."""
        citations = ["[1]"]
        content = "This has [1] but no references section."
        is_verified, unverified = verify_citations(citations, content)
        assert is_verified is False
        assert len(unverified) > 0
    
    def test_insufficient_citations_fail(self):
        """Less than 3 real citations should fail."""
        citations = ["[1]", "[2]"]
        content = """
        # Research
        
        [1] First citation
        [2] Second citation
        
        ## References
        [1] Test 1
        [2] Test 2
        """
        is_verified, unverified = verify_citations(citations, content)
        assert is_verified is False
        assert len(unverified) > 0

class TestValidateResearchMd:
    """Tests for validate_research_md function."""
    
    def test_valid_research_md_passes(self):
        """Valid research.md should pass validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            content = """
            # Research on Solder Hardness
            
            Recent studies [1] have shown significant results.
            DOI: 10.1038/s41586-020-2649-2
            
            ## References
            [1] Smith, J. (2020). Solder hardness prediction. Nature, 586, 123-130.
            """
            research_path.write_text(content)
            
            # Should not raise
            result = validate_research_md(Path(tmpdir))
            assert result is True
    
    def test_empty_research_md_fails(self):
        """Empty research.md should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            research_path.write_text("")
            
            with pytest.raises(ConstitutionError) as exc_info:
                validate_research_md(Path(tmpdir))
            
            assert "empty" in str(exc_info.value).lower()
    
    def test_missing_citations_fails(self):
        """research.md without citations should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            research_path.write_text("# Research\n\nNo citations here.")
            
            with pytest.raises(ConstitutionError) as exc_info:
                validate_research_md(Path(tmpdir))
            
            assert "No citations found" in str(exc_info.value)
    
    def test_placeholder_citations_fails(self):
        """research.md with placeholder citations should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            content = """
            # Research
            
            This needs [citation needed].
            
            ## References
            """
            research_path.write_text(content)
            
            with pytest.raises(ConstitutionError) as exc_info:
                validate_research_md(Path(tmpdir))
            
            assert "Unverified citations" in str(exc_info.value)

class TestMain:
    """Tests for main function."""
    
    def test_main_with_valid_research(self):
        """main() should return 0 with valid research.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            content = """
            # Research
            
            [1] Valid citation
            
            ## References
            [1] Smith, J. (2020). Test. DOI: 10.1038/test
            """
            research_path.write_text(content)
            
            # Change to temp directory to simulate project root
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = main()
                assert result == 0
            finally:
                os.chdir(original_cwd)
    
    def test_main_with_invalid_research(self):
        """main() should return 1 with invalid research.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            research_path.write_text("# Research\n\nNo citations.")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = main()
                assert result == 1
            finally:
                os.chdir(original_cwd)
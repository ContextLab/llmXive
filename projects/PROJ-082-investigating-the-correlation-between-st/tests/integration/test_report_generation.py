"""
Integration tests for automated report generation (T032).
Verifies that paper_draft.md is generated correctly from MetaAnalysisResult JSON.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from report_generator import run_report_generation, load_meta_analysis_result


@pytest.fixture
def sample_meta_result():
    """Create a sample MetaAnalysisResult dictionary."""
    return {
        "study_count": 15,
        "synthesis_mode": "quantitative",
        "meta_analysis": {
            "weighted_mean_r": 0.2345,
            "ci_lower": 0.1234,
            "ci_upper": 0.3456,
            "model_type": "random_effects"
        },
        "heterogeneity": {
            "i_squared": 52.34,
            "q_statistic": 24.56,
            "p_value": 0.023
        },
        "bias": {
            "egger_test": {
                "intercept": 0.123,
                "p_value": 0.456
            }
        },
        "correction": {
            "method": "bonferroni",
            "original_alpha": 0.05,
            "adjusted_alpha": 0.0167,
            "tract_count": 3
        },
        "tract_results": [
            {
                "tract_name": "Arcuate Fasciculus",
                "effect_size": 0.312,
                "ci_lower": 0.198,
                "ci_upper": 0.426,
                "p_value": 0.002
            },
            {
                "tract_name": "Cingulum Bundle",
                "effect_size": 0.187,
                "ci_lower": 0.056,
                "ci_upper": 0.318,
                "p_value": 0.012
            }
        ]
    }


@pytest.fixture
def temp_project_structure(sample_meta_result):
    """Create a temporary project structure with required directories and files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create directory structure
        (tmpdir / "data" / "derived").mkdir(parents=True)
        (tmpdir / "docs" / "templates").mkdir(parents=True)
        
        # Write sample meta result
        meta_path = tmpdir / "data" / "derived" / "meta_analysis_result.json"
        with open(meta_path, 'w') as f:
            json.dump(sample_meta_result, f, indent=2)
        
        # Write minimal template
        template_content = """
        # Test Paper
        Study Count: {{ result.study_count }}
        Pooled r: {{ "%.4f"|format(result.meta_analysis.weighted_mean_r) }}
        """
        template_path = tmpdir / "docs" / "templates" / "paper_template.md.j2"
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        yield tmpdir, meta_path


def test_report_generation_creates_file(temp_project_structure):
    """Test that run_report_generation creates the paper_draft.md file."""
    tmpdir, input_path = temp_project_structure
    
    output_path = tmpdir / "docs" / "paper_draft.md"
    
    # Mock get_project_root to use our temp directory
    with patch('report_generator.get_project_root', return_value=tmpdir):
        result_path = run_report_generation(input_path, output_path)
    
    assert result_path.exists(), "Output file was not created"
    assert result_path == output_path, "Output path mismatch"
    
    # Verify file is non-empty
    assert result_path.stat().st_size > 0, "Output file is empty"


def test_report_generation_content(temp_project_structure):
    """Test that the generated report contains expected content."""
    tmpdir, input_path = temp_project_structure
    
    output_path = tmpdir / "docs" / "paper_draft.md"
    
    with patch('report_generator.get_project_root', return_value=tmpdir):
        run_report_generation(input_path, output_path)
    
    content = output_path.read_text()
    
    # Verify key content is present
    assert "Study Count: 15" in content, "Study count not found in report"
    assert "Pooled r: 0.2345" in content, "Pooled correlation not found in report"


def test_report_generation_missing_input_fails():
    """Test that missing input JSON raises appropriate error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        non_existent = tmpdir / "non_existent.json"
        
        with pytest.raises(FileNotFoundError):
            load_meta_analysis_result(non_existent)


def test_report_generation_missing_template_fails(temp_project_structure):
    """Test that missing template raises appropriate error."""
    tmpdir, input_path = temp_project_structure
    
    # Remove the template
    template_path = tmpdir / "docs" / "templates" / "paper_template.md.j2"
    template_path.unlink()
    
    output_path = tmpdir / "docs" / "paper_draft.md"
    
    with patch('report_generator.get_project_root', return_value=tmpdir):
        with pytest.raises(Exception):
            run_report_generation(input_path, output_path)


def test_narrative_mode_in_report(temp_project_structure):
    """Test report generation in narrative mode (N < 10)."""
    narrative_result = {
        "study_count": 5,
        "synthesis_mode": "narrative",
        "narrative": {
            "overview": "This study investigates...",
            "themes": "Themes include...",
            "limitations": "Limitations include..."
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / "data" / "derived").mkdir(parents=True)
        (tmpdir / "docs" / "templates").mkdir(parents=True)
        
        meta_path = tmpdir / "data" / "derived" / "meta_analysis_result.json"
        with open(meta_path, 'w') as f:
            json.dump(narrative_result, f, indent=2)
        
        template_content = """
        # Narrative Report
        Mode: {{ result.synthesis_mode }}
        {% if result.get('narrative') %}
        Overview: {{ result.narrative.overview }}
        {% endif %}
        """
        template_path = tmpdir / "docs" / "templates" / "paper_template.md.j2"
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        output_path = tmpdir / "docs" / "paper_draft.md"
        
        with patch('report_generator.get_project_root', return_value=tmpdir):
            run_report_generation(meta_path, output_path)
        
        content = output_path.read_text()
        assert "narrative" in content.lower(), "Narrative mode indicator missing"
        assert "This study investigates" in content, "Narrative overview missing"

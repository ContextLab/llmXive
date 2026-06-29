"""
Integration test for report generation (T030).
Verifies that the report generator produces a valid Markdown file
with all required sections and correct template injection.
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from report.generate import generate_report, main as generate_main
from models import CorrelationResult
from dataclasses import dataclass
from typing import List, Dict, Any
import pandas as pd


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def dummy_correlation_results():
    """Create dummy correlation results for testing."""
    return [
        CorrelationResult(
            metric_name="Participation_Coefficient",
            r=0.35,
            p=0.008,
            q=0.024,
            significant=True,
            covariate_controlled=True
        ),
        CorrelationResult(
            metric_name="Within_Module_Degree",
            r=0.12,
            p=0.25,
            q=0.30,
            significant=False,
            covariate_controlled=True
        ),
        CorrelationResult(
            metric_name="Global_Efficiency",
            r=0.41,
            p=0.003,
            q=0.012,
            significant=True,
            covariate_controlled=True
        )
    ]


@pytest.fixture
def dummy_power_analysis():
    """Create dummy power analysis data."""
    return {
        "sample_size": 100,
        "detectable_effect_size": 0.28,
        "power": 0.80,
        "alpha": 0.05,
        "fdr_corrected": True
    }


@pytest.fixture
def dummy_plots():
    """Create dummy plot file paths."""
    return [
        "figures/scatter_participation_coef.png",
        "figures/scatter_global_efficiency.png"
    ]


def test_report_generates_markdown_with_all_sections(
    temp_output_dir,
    dummy_correlation_results,
    dummy_power_analysis,
    dummy_plots
):
    """
    Integration test: Verify report generation with all required sections.
    
    Tests:
    1. Report file is created
    2. All required sections are present
    3. Template variables are correctly injected
    4. Limitation statement is present
    5. Associational relationship phrasing is in conclusion
    """
    output_path = Path(temp_output_dir) / "report.md"
    
    # Generate the report
    generate_report(
        output_path=str(output_path),
        correlation_results=dummy_correlation_results,
        power_analysis=dummy_power_analysis,
        plots=dummy_plots,
        limitations=[
            "Motor Task Performance is a proxy for proprioceptive accuracy.",
            "Sample size may limit generalizability to broader populations.",
            "Cross-sectional design prevents causal inference."
        ]
    )
    
    # Verify file exists
    assert output_path.exists(), f"Report file not created at {output_path}"
    
    # Read content
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify all required sections exist
    required_sections = [
        "# Brain Network Dynamics and Sensorimotor Performance Report",
        "## Executive Summary",
        "## Methodology",
        "## Results",
        "## Correlation Analysis",
        "## Power Analysis",
        "## Limitations",
        "## Conclusion"
    ]
    
    for section in required_sections:
        assert section in content, f"Missing required section: {section}"
    
    # Verify template injection - correlation table
    assert "Participation_Coefficient" in content, "Correlation results not injected"
    assert "Within_Module_Degree" in content, "Correlation results not injected"
    assert "Global_Efficiency" in content, "Correlation results not injected"
    
    # Verify specific values are present
    assert "0.35" in content, "Correlation coefficient not injected"
    assert "0.008" in content, "P-value not injected"
    assert "0.024" in content, "FDR-corrected q-value not injected"
    
    # Verify power analysis injection
    assert "100" in content, "Sample size not injected"
    assert "0.28" in content, "Detectable effect size not injected"
    
    # Verify limitation statement
    limitation_text = "Motor Task Performance is a proxy for proprioceptive accuracy."
    assert limitation_text in content, "Required limitation statement missing"
    
    # Verify associational relationship phrasing in conclusion
    conclusion_lower = content.lower()
    assert ("associational relationship" in conclusion_lower or 
            "correlational evidence" in conclusion_lower), \
        "Conclusion must contain 'associational relationship' or 'correlational evidence'"
    
    # Verify plot references
    for plot in dummy_plots:
        assert plot in content, f"Plot reference missing: {plot}"
    
    # Verify Markdown structure
    assert content.startswith("#"), "Report must start with H1 header"
    assert "## " in content, "Report must contain H2 sections"
    
    # Verify no placeholder text remains
    assert "{{" not in content, "Template variables not fully injected"
    assert "}}" not in content, "Template variables not fully injected"


def test_report_with_empty_results(temp_output_dir):
    """Test report generation with empty correlation results."""
    output_path = Path(temp_output_dir) / "empty_report.md"
    
    generate_report(
        output_path=str(output_path),
        correlation_results=[],
        power_analysis={"sample_size": 0, "detectable_effect_size": 0.0},
        plots=[],
        limitations=["No significant correlations found."]
    )
    
    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "No significant correlations" in content


def test_report_file_format(temp_output_dir, dummy_correlation_results, dummy_power_analysis):
    """Verify the generated file is valid Markdown."""
    output_path = Path(temp_output_dir) / "format_test.md"
    
    generate_report(
        output_path=str(output_path),
        correlation_results=dummy_correlation_results,
        power_analysis=dummy_power_analysis,
        plots=[],
        limitations=["Test limitation."]
    )
    
    # Verify file extension
    assert output_path.suffix == ".md", "Output must be .md file"
    
    # Verify encoding
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Basic Markdown syntax checks
    assert "#" in content, "Missing headers"
    assert "|" in content, "Missing tables (correlation table expected)"
    assert "**" in content or "*" in content, "Missing emphasis markers"
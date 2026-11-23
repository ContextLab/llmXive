import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function under test from the existing API surface
from code.viz.plots import create_forest_plot, create_funnel_plot

# Test data fixture: a minimal set of effect sizes and study metadata
@pytest.fixture
def mock_study_data():
    """
    Creates a DataFrame with the minimum required columns for a forest plot:
    - study_id: str
    - hedges_g: float (effect size)
    - se: float (standard error)
    - domain: str (social skill domain)
    """
    return pd.DataFrame([
        {
            "study_id": "Study_A",
            "hedges_g": 0.5,
            "se": 0.1,
            "domain": "communication"
        },
        {
            "study_id": "Study_B",
            "hedges_g": -0.2,
            "se": 0.15,
            "domain": "peer interaction"
        },
        {
            "study_id": "Study_C",
            "hedges_g": 1.1,
            "se": 0.2,
            "domain": "emotional regulation"
        }
    ])

def test_forest_plot_creates_file(mock_study_data, tmp_path):
    """
    Unit test for forest plot generation.
    Verifies that create_forest_plot writes a valid PNG file to disk
    when provided with real study data.
    """
    output_path = tmp_path / "test_forest.png"

    # Call the function under test
    create_forest_plot(
        studies=mock_study_data,
        output_path=str(output_path),
        title="Test Forest Plot"
    )

    # Assert the file was created
    assert output_path.exists(), "Forest plot file was not created"
    assert output_path.stat().st_size > 0, "Forest plot file is empty"

    # Verify it's a valid PNG (basic magic number check)
    with open(output_path, "rb") as f:
        header = f.read(8)
        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        assert header.startswith(b"\x89PNG"), "File is not a valid PNG"

def test_forest_plot_handles_empty_data(tmp_path):
    """
    Unit test to ensure the function handles empty input gracefully.
    Expected behavior: Raise a ValueError or return False, not crash.
    """
    empty_data = pd.DataFrame(columns=["study_id", "hedges_g", "se", "domain"])
    output_path = tmp_path / "empty_forest.png"

    with pytest.raises(ValueError, match="No studies provided"):
        create_forest_plot(
            studies=empty_data,
            output_path=str(output_path),
            title="Empty Plot"
        )

def test_forest_plot_confidence_intervals_visible(mock_study_data, tmp_path):
    """
    Unit test to verify that confidence intervals are calculated and rendered.
    While we cannot easily check pixel-level rendering in a unit test without
    heavy dependencies, we verify the function accepts the data and produces output.
    The visual verification of CIs is done in integration tests.
    """
    output_path = tmp_path / "ci_test.png"
    
    # Run the generation
    create_forest_plot(
        studies=mock_study_data,
        output_path=str(output_path),
        title="CI Test"
    )
    
    assert output_path.exists()

def test_funnel_plot_suppression_when_n_less_than_10(tmp_path):
    """
    Unit test for funnel plot suppression logic when N < 10 (T035).
    
    Verifies that create_funnel_plot raises a ValueError when the number
    of studies is less than 10, as per the requirement to suppress
    publication bias assessment for small samples.
    """
    # Create a dataset with N = 5 (less than 10)
    small_data = pd.DataFrame([
        {"study_id": f"Study_{i}", "hedges_g": 0.1 * i, "se": 0.1, "domain": "communication"}
        for i in range(5)
    ])
    
    output_path = tmp_path / "funnel_small.png"
    
    # Verify that the function raises ValueError with the correct message
    with pytest.raises(ValueError, match="Insufficient data for funnel plot"):
        create_funnel_plot(
            studies=small_data,
            output_path=str(output_path),
            title="Small Sample Funnel"
        )
    
    # Ensure no file was created
    assert not output_path.exists(), "Funnel plot should not be created for N < 10"

def test_funnel_plot_creates_file_when_n_ge_10(tmp_path):
    """
    Unit test to ensure funnel plot is created when N >= 10.
    """
    # Create a dataset with N = 12 (greater than or equal to 10)
    sufficient_data = pd.DataFrame([
        {"study_id": f"Study_{i}", "hedges_g": 0.1 * i, "se": 0.1, "domain": "communication"}
        for i in range(12)
    ])
    
    output_path = tmp_path / "funnel_sufficient.png"
    
    # This should succeed without raising an error
    create_funnel_plot(
        studies=sufficient_data,
        output_path=str(output_path),
        title="Sufficient Sample Funnel"
    )
    
    # Assert the file was created and is not empty
    assert output_path.exists(), "Funnel plot file was not created for N >= 10"
    assert output_path.stat().st_size > 0, "Funnel plot file is empty"
    
    # Verify it's a valid PNG
    with open(output_path, "rb") as f:
        header = f.read(8)
        assert header.startswith(b"\x89PNG"), "File is not a valid PNG"

def test_funnel_plot_exactly_n_10(tmp_path):
    """
    Unit test for the boundary condition where N == 10.
    The plot should be generated (not suppressed) when N is exactly 10.
    """
    # Create a dataset with exactly N = 10
    boundary_data = pd.DataFrame([
        {"study_id": f"Study_{i}", "hedges_g": 0.1 * i, "se": 0.1, "domain": "communication"}
        for i in range(10)
    ])
    
    output_path = tmp_path / "funnel_boundary.png"
    
    # Should succeed
    create_funnel_plot(
        studies=boundary_data,
        output_path=str(output_path),
        title="Boundary Sample Funnel"
    )
    
    assert output_path.exists(), "Funnel plot should be created when N == 10"
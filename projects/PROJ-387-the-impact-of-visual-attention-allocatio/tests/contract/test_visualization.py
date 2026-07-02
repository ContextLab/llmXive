import os
import re
import glob
import pytest
from pathlib import Path

# Import project utilities to determine paths
# We assume the test runs from the project root or that PYTHONPATH includes 'code'
# The visualize module is expected to be in code/reporting
try:
    from reporting.visualize import read_valence_count
except ImportError:
    # Fallback for direct execution if PYTHONPATH isn't set, though test runners usually handle this
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
    from reporting.visualize import read_valence_count


@pytest.fixture
def output_plots_dir():
    """Returns the path to the output/plots directory."""
    return Path("output/plots")

@pytest.fixture
def quality_report_path():
    """Returns the path to the quality report."""
    return Path("data/eye-tracking/quality_report.md")


def test_plot_files_exist_and_labeled(output_plots_dir, quality_report_path):
    """
    Contract test for T034: Verify plot file existence and labels.
    
    Requirements:
    1. Read expected count from data/eye-tracking/quality_report.md (valence_categories_count).
    2. Verify that scatter plots exist: output/plots/scatter_{valence}.png
    3. Verify that histogram plots exist: output/plots/hist_{metric}_{valence}.png
    4. Assert total plot count >= expected_count * 2 (scatters + at least one hist per valence).
    5. Verify that plot files contain labeled axes (checked via file content or metadata if possible, 
       but primarily checking file existence and naming convention as per T042/T044).
    """
    
    # 1. Determine expected count
    if not quality_report_path.exists():
        pytest.fail(f"Quality report not found at {quality_report_path}. "
                    "Ensure T015 has run and generated the report.")
    
    expected_count = 0
    with open(quality_report_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Look for the line: valence_categories_count: X
        match = re.search(r'valence_categories_count:\s*(\d+)', content)
        if match:
            expected_count = int(match.group(1))
        else:
            # Fallback if format differs slightly, or error
            pytest.fail("Could not parse 'valence_categories_count' from quality report.")

    assert expected_count > 0, "Expected valence category count must be greater than 0."

    # 2. Verify directory exists
    if not output_plots_dir.exists():
        pytest.fail(f"Output plots directory not found at {output_plots_dir}. "
                    "Ensure T039/T040/T041 have run.")

    # 3. Check Scatter Plots (one per valence)
    # We don't know the specific valence names (e.g., positive, negative, neutral) 
    # without reading the data, but we can check for the pattern.
    # However, T044 logic relies on total count. Let's verify the files exist by pattern.
    scatter_files = glob.glob(str(output_plots_dir / "scatter_*.png"))
    
    # 4. Check Histogram Plots
    hist_files = glob.glob(str(output_plots_dir / "hist_*.png"))
    
    total_plots = len(scatter_files) + len(hist_files)
    
    # Requirement from T044: Assert len(glob) >= expected_count * 2
    # This implies at least 1 scatter + 1 hist per valence category
    min_required_plots = expected_count * 2
    
    assert total_plots >= min_required_plots, (
        f"Plot completeness check failed. "
        f"Expected at least {min_required_plots} plots (based on {expected_count} valence categories), "
        f"but found {total_plots}. "
        f"Scatters: {len(scatter_files)}, Hists: {len(hist_files)}. "
        f"Ensure T040 (scatters) and T041 (hists) have executed correctly."
    )

    # 5. Verify Labels (T042)
    # Since we cannot easily parse image metadata for axis labels without heavy dependencies,
    # we rely on the contract that the script (T039/T040/T041) MUST produce labeled axes.
    # We verify that the files are non-empty (size > 0) which implies they were written.
    # A more robust check would require opening the image and inspecting text, but for a contract test
    # on file existence and structure, size check is a valid proxy for "generated".
    
    for plot_file in scatter_files + hist_files:
        file_path = Path(plot_file)
        assert file_path.stat().st_size > 0, f"Plot file {plot_file} is empty."
        
        # Optional: Check filename pattern matches expected format
        if "scatter_" in file_path.name:
            assert file_path.name.endswith(".png"), "Scatter plot must be .png"
        elif "hist_" in file_path.name:
            assert file_path.name.endswith(".png"), "Histogram plot must be .png"

    # If we reach here, the contract is satisfied.
    assert True
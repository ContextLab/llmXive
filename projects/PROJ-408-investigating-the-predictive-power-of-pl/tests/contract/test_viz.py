"""
Contract test for figure metadata validation.

This test ensures that all generated figures (T030, T031) meet publication
readiness standards by verifying required metadata (DPI >= 300) is present.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from PIL import Image
except ImportError:
    pytest.skip("Pillow not installed. Skipping metadata validation.", allow_module_level=True)

# Constants
MIN_DPI = 300
FIGURES_DIR = project_root / "output" / "figures"
REQUIRED_FIGURES = [
    "phylo_metabolite_heatmap.png",
    "mantel_results.png"
]


def test_figures_exist():
    """Verify that all required figure files exist."""
    missing = []
    for fig_name in REQUIRED_FIGURES:
        fig_path = FIGURES_DIR / fig_name
        if not fig_path.exists():
            missing.append(fig_name)

    assert not missing, f"Missing required figure files: {missing}"


def test_figure_metadata_dpi():
    """
    Validate that all figures have DPI metadata >= 300.

    This enforces T033 (High-resolution standards) and ensures publication readiness.
    """
    if not FIGURES_DIR.exists():
        pytest.fail(f"Figures directory does not exist: {FIGURES_DIR}")

    errors = []

    for fig_name in REQUIRED_FIGURES:
        fig_path = FIGURES_DIR / fig_name

        if not fig_path.exists():
            # Should have been caught by test_figures_exist, but double-check
            errors.append(f"{fig_name}: File missing")
            continue

        try:
            with Image.open(fig_path) as img:
                # Check DPI info
                dpi = img.info.get('dpi')

                if dpi is None:
                    errors.append(f"{fig_name}: Missing 'dpi' metadata")
                    continue

                if not isinstance(dpi, tuple) or len(dpi) < 2:
                    errors.append(f"{fig_name}: Invalid 'dpi' format: {dpi}")
                    continue

                dpi_val = dpi[0]  # Check horizontal DPI

                if dpi_val < MIN_DPI:
                    errors.append(
                        f"{fig_name}: DPI ({dpi_val}) is below minimum ({MIN_DPI})"
                    )
                else:
                    # Success case: log or assert
                    pass

        except Exception as e:
            errors.append(f"{fig_name}: Failed to read image metadata: {str(e)}")

    assert not errors, "Figure metadata validation failed:\n" + "\n".join(errors)


def test_figure_file_sizes():
    """
    Ensure figures are of sufficient size (indicating non-empty/corrupted files).
    """
    min_size_bytes = 10 * 1024  # 10KB minimum

    for fig_name in REQUIRED_FIGURES:
        fig_path = FIGURES_DIR / fig_name
        if fig_path.exists():
            size = fig_path.stat().st_size
            assert size >= min_size_bytes, (
                f"{fig_name} is too small ({size} bytes). "
                f"Expected at least {min_size_bytes} bytes."
            )
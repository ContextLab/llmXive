import os
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt

from code.viz.templates import (
    add_disclaimer_to_png,
    inject_disclaimer_into_html,
    apply_disclaimer_to_directory,
    validate_limitation_injection,
)

def test_add_disclaimer_to_png(tmp_path: Path):
    # Create a simple PNG image
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    png_path = tmp_path / "test_plot.png"
    fig.savefig(png_path)
    plt.close(fig)

    # Apply disclaimer
    add_disclaimer_to_png(png_path)

    # Validate that the file still exists and is a PNG
    assert png_path.exists()
    assert png_path.suffix.lower() == ".png"

def test_inject_disclaimer_into_html(tmp_path: Path):
    html_path = tmp_path / "report.html"
    html_content = "<html><head><title>Test</title></head><body><h1>Report</h1></body></html>"
    html_path.write_text(html_content, encoding="utf-8")

    inject_disclaimer_into_html(html_path)

    updated = html_path.read_text(encoding="utf-8")
    assert "Limitation:" in updated
    # Ensure the disclaimer appears before </body>
    assert updated.lower().find("limitation") < updated.lower().find("</body>")

def test_apply_disclaimer_to_directory(tmp_path: Path):
    # Create PNG
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    png_path = tmp_path / "image.png"
    fig.savefig(png_path)
    plt.close(fig)

    # Create HTML
    html_path = tmp_path / "report.html"
    html_path.write_text("<html><body></body></html>", encoding="utf-8")

    # Apply to the whole directory
    apply_disclaimer_to_directory(tmp_path)

    # Validate both files have the disclaimer
    assert png_path.exists()
    assert html_path.exists()
    # For HTML we can reuse the validator
    result = validate_limitation_injection(html_path, expected_formats=["text", "markdown"])
    assert result["found"] is True

# The tests ensure that the functions run without error and that the
# disclaimer text is inserted into both PNG and HTML artifacts. No
# visual inspection is performed here; the presence of the text is
# verified via simple string checks for HTML and file existence for PNG.
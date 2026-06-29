"""Unit test for the validation report generation script."""

import pathlib
import shutil

import pytest

# The script writes to the ``validation`` directory at the repository root.
# To keep the test isolated we work in a temporary directory that mimics the
# expected layout.

@pytest.fixture
def setup_validation_data(tmp_path):
    """Create minimal validation subset and external scale files."""
    # Create data/processed directory with a tiny validation subset CSV.
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    subset_path = processed_dir / "validation_subset.csv"
    subset_path.write_text(
        "session_id,marker1,marker2,external_score\\n"
        "s1,1,0,3.5\\n"
        "s2,0,1,4.0\\n",
        encoding="utf-8",
    )

    # Create a dummy external scale CSV that the convergent function can read.
    external_path = tmp_path / "external_scale.csv"
    external_path.write_text(
        "session_id,external_score\\n"
        "s1,3.5\\n"
        "s2,4.0\\n",
        encoding="utf-8",
    )

    # Patch the functions that locate files so they point inside the tmp_path.
    # We monkey‑patch the Path objects returned by the module functions.
    from validation import select_subset

    original_find = select_subset.find_external_scale_file

    def patched_find():
        return external_path

    select_subset.find_external_scale_file = patched_find

    # Change working directory so the script sees the temporary layout.
    cwd = pathlib.Path.cwd()
    pathlib.Path.chdir(tmp_path)

    yield

    # Restore original state.
    select_subset.find_external_scale_file = original_find
    pathlib.Path.chdir(cwd)

def test_report_generation(setup_validation_data, tmp_path):
    """Run the report generator and verify both files are created."""
    from code.validation.generate_report import main as generate_report

    # Execute the script.
    generate_report()

    pdf_path = pathlib.Path("validation/report.pdf")
    yaml_path = pathlib.Path("validation/validation_report.yaml")

    assert pdf_path.is_file(), "PDF report was not created"
    assert yaml_path.is_file(), "YAML summary was not created"

    # Basic sanity checks on file contents.
    pdf_content = pdf_path.read_bytes()
    assert len(pdf_content) > 0, "PDF file is empty"

    yaml_content = yaml_path.read_text(encoding="utf-8")
    data = yaml.safe_load(yaml_content)
    assert "split_half_reliability" in data
    assert "convergent_correlation" in data
    assert "pearson_r" in data["convergent_correlation"]
    assert "p_value" in data["convergent_correlation"]
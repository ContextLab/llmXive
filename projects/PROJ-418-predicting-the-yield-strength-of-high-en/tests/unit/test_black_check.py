import sys
from pathlib import Path

def test_black_check_passes():
    """
    Integration‑style unit test that ensures the ``run_black_check`` script
    executes without raising and that the expected report file is created.
    """
    # Make the ``code`` directory importable so we can import the script as a module.
    sys.path.append(str(Path.cwd() / "code"))

    from run_black_check import run_black_check

    # Execute the check – it should raise no exception if formatting is correct.
    run_black_check()

    # Verify that the report file was written and contains the success marker.
    report_path = Path("output/format_report.txt")
    assert report_path.is_file(), "Black format report was not created"

    report_content = report_path.read_text()
    assert "All done!" in report_content, "Black did not report successful formatting"
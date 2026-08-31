"""
Contract test for the data model schema verification.

This test ensures that the verify_data_model.py script correctly validates
the data-model.md file structure.
"""
import subprocess
import sys
from pathlib import Path

def test_data_model_verification():
    """
    Runs the verify_data_model.py script and asserts it exits with code 0.
    """
    # Path to the verification script
    verify_script = Path(__file__).parent.parent.parent / "code" / "verify_data_model.py"
    
    if not verify_script.exists():
        raise FileNotFoundError(f"Verification script not found at {verify_script}")

    # Run the script
    result = subprocess.run(
        [sys.executable, str(verify_script)],
        capture_output=True,
        text=True
    )

    # Assert success
    assert result.returncode == 0, (
        f"Data model verification failed.\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )

    # Assert expected output message
    assert "SUCCESS" in result.stdout, "Expected 'SUCCESS' message in output."
    assert "Data model verification passed" in result.stdout

def test_data_model_content_structure():
    """
    Directly checks the content of data-model.md for required sections.
    """
    from config import get_specs_dir
    
    specs_dir = get_specs_dir()
    data_model_path = specs_dir / "data-model.md"
    
    assert data_model_path.exists(), "data-model.md file must exist."
    
    content = data_model_path.read_text(encoding="utf-8")
    
    required_headings = ["Stimulus", "Participant", "Rating", "AnalysisResult"]
    
    for heading in required_headings:
        # Check for heading presence (case-sensitive, allowing markdown #)
        assert heading in content, f"Required heading '{heading}' not found in data-model.md"
        
        # More strict check: ensure it appears as a heading
        import re
        pattern = rf"^(?:#+\s*)?{re.escape(heading)}\s*$"
        assert re.search(pattern, content, re.MULTILINE), \
            f"Required heading '{heading}' not found as a proper heading in data-model.md"
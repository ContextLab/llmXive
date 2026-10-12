"""Test that the reproducibility script runs successfully."""
import subprocess
import pathlib

def test_repro_script():
    script_path = pathlib.Path(__file__).parents[2] / "scripts" / "reproduce.sh"
    assert script_path.is_file(), "reproduce.sh not found"
    result = subprocess.run(["bash", str(script_path)], capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, f"Script exited with {result.returncode}"
    assert "Success" in result.stdout, "Success message missing"

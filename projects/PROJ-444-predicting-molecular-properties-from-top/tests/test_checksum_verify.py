import subprocess
import sys
from pathlib import Path

def test_checksum_verification():
    """
    Run the checksum verification script and assert that it exits with status 0
    and prints the exact success message.
    """
    script_path = Path("code") / "00_checksum_verify.py"
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Script exited with {result.returncode}, stderr: {result.stderr}"
    # The script should print exactly this line on success
    assert "All checksums verified" in result.stdout.strip()
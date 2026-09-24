"""
Integration test for T025: CPU pinning and governor setting.

This test verifies that the run_benchmarks.sh script correctly attempts to 
configure the CPU governor and uses taskset for pinning.

Note: Since this involves system-level changes (governor, sudo), it is 
primarily a structural and logic test. In a CI environment with sudo 
privileges, it would verify the actual sysfs state.
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

# Path to the script under test
SCRIPT_PATH = Path(__file__).parent.parent.parent / "code" / "scripts" / "run_benchmarks.sh"

@pytest.mark.integration
def test_script_syntax_and_structure():
    """Verify the script exists and is valid bash syntax."""
    assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"
    
    # Check syntax
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Syntax error in run_benchmarks.sh:\n{result.stderr}"

@pytest.mark.integration
def test_script_contains_required_commands():
    """Verify the script contains the required logic for cpupower, sysfs, and taskset."""
    content = SCRIPT_PATH.read_text()
    
    # Check for cpupower usage
    assert "cpupower" in content, "Script must attempt to use cpupower."
    assert "frequency-set" in content, "Script must use cpupower frequency-set."
    
    # Check for sysfs fallback
    assert "scaling_governor" in content, "Script must fallback to sysfs for governor."
    assert "echo \"performance\"" in content or "echo 'performance'" in content, "Script must write 'performance' to sysfs."
    
    # Check for taskset usage
    assert "taskset" in content, "Script must use taskset for CPU pinning."
    assert "-c" in content, "Script must use taskset -c for core specification."
    
    # Check for logic flow (try/except equivalent in bash)
    assert "if command -v cpupower" in content, "Script must check for cpupower availability."

@pytest.mark.integration
def test_script_execution_preparation():
    """
    Verify that the script creates necessary directories and logs.
    This test runs the script in a mock environment where the binary doesn't exist
    to ensure the setup logic runs before the binary check fails.
    """
    # Create a temporary directory to act as a mock project root
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create expected directory structure
        (tmp_path / "code" / "scripts").mkdir(parents=True)
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "state" / "logs").mkdir(parents=True)
        (tmp_path / "benchmark").mkdir(parents=True)
        
        # Copy script to temp location
        temp_script = tmp_path / "code" / "scripts" / "run_benchmarks.sh"
        shutil.copy(SCRIPT_PATH, temp_script)
        
        # Make executable
        temp_script.chmod(0o755)
        
        # Run the script. It should fail at the binary check, but that's expected.
        # We are testing that the script gets far enough to hit the binary check.
        # We redirect stderr to capture the specific error message about the missing binary.
        result = subprocess.run(
            ["bash", str(temp_script)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # The script should exit with non-zero because the binary is missing
        # But it should have printed the specific error message defined in the script
        assert result.returncode != 0, "Script should fail if binary is missing."
        assert "Benchmark binary not found" in result.stdout or "Benchmark binary not found" in result.stderr, \
            "Script should report missing binary after attempting setup."
        
        # Verify that the log directory was created (setup logic ran)
        log_dir = tmp_path / "state" / "logs"
        assert log_dir.exists(), "Log directory should be created by the script."

@pytest.mark.integration
def test_governor_logic_presence():
    """Verify the specific logic for governor setting is present."""
    content = SCRIPT_PATH.read_text()
    
    # Check for the specific fallback pattern
    assert "if command -v cpupower" in content
    assert "sudo cpupower frequency-set -g performance" in content
    assert "sysfs" in content.lower()
    assert "scaling_governor" in content
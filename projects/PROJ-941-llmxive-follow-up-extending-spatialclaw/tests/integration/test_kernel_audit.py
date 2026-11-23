"""
Integration test for the Kernel Blockage Final Audit (T050).
Verifies that the audit script correctly identifies blocked libraries
and exits with the appropriate code.
"""
import os
import sys
import tempfile
import shutil
import subprocess
import pytest

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

@pytest.fixture
def temp_audit_env():
    """Create a temporary directory structure for testing the audit script."""
    base_dir = tempfile.mkdtemp()
    logs_dir = os.path.join(base_dir, 'results', 'logs')
    analysis_dir = os.path.join(base_dir, 'results', 'analysis')
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(analysis_dir, exist_ok=True)
    yield {
        'base': base_dir,
        'logs': logs_dir,
        'analysis': analysis_dir
    }
    shutil.rmtree(base_dir)

def test_audit_passes_on_clean_logs(temp_audit_env):
    """Test that audit passes when no blocked libraries are present."""
    # Create a clean log file
    clean_log = os.path.join(temp_audit_env['logs'], 'clean.log')
    with open(clean_log, 'w') as f:
        f.write("INFO: Starting execution\n")
        f.write("INFO: Using shapely for geometry\n")
        f.write("INFO: Task completed successfully\n")

    output_file = os.path.join(temp_audit_env['analysis'], 'audit_clean.txt')

    # Run the audit script
    script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'utils', 'kernel_audit.py')
    result = subprocess.run(
        [sys.executable, script_path, '--logs-dir', temp_audit_env['logs'], '--output', output_file],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Audit should pass on clean logs. Stderr: {result.stderr}"
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        content = f.read()
    assert "AUDIT PASSED" in content
    assert "0 blocked operations found" in content

def test_audit_fails_on_blocked_import(temp_audit_env):
    """Test that audit fails when a blocked library is detected."""
    # Create a log file with a blocked import
    blocked_log = os.path.join(temp_audit_env['logs'], 'blocked.log')
    with open(blocked_log, 'w') as f:
        f.write("INFO: Starting execution\n")
        f.write("ERROR: Blocked operation: import trimesh\n")
        f.write("INFO: Falling back to 2D\n")

    output_file = os.path.join(temp_audit_env['analysis'], 'audit_blocked.txt')

    script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'utils', 'kernel_audit.py')
    result = subprocess.run(
        [sys.executable, script_path, '--logs-dir', temp_audit_env['logs'], '--output', output_file],
        capture_output=True,
        text=True
    )

    assert result.returncode != 0, f"Audit should fail when blocked libraries are found. Stdout: {result.stdout}"
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        content = f.read()
    assert "AUDIT FAILED" in content
    assert "trimesh" in content

def test_audit_fails_on_pytorch3d(temp_audit_env):
    """Test detection of pytorch3d."""
    log_file = os.path.join(temp_audit_env['logs'], 'torch3d.log')
    with open(log_file, 'w') as f:
        f.write("Traceback (most recent call last):\n")
        f.write("  File 'main.py', line 10, in <module>\n")
        f.write("    import pytorch3d\n")

    output_file = os.path.join(temp_audit_env['analysis'], 'audit_torch3d.txt')
    script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'utils', 'kernel_audit.py')

    result = subprocess.run(
        [sys.executable, script_path, '--logs-dir', temp_audit_env['logs'], '--output', output_file],
        capture_output=True,
        text=True
    )

    assert result.returncode != 0
    with open(output_file, 'r') as f:
        content = f.read()
    assert "pytorch3d" in content
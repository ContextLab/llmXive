"""
Pytest suite for the `create_code_dir` utility.

It checks that:
  * The `create_and_verify_code_dir` function creates the `code/` directory
    if it does not exist.
  * The function is idempotent (running it twice does not raise).
  * After creation the directory is writable.
"""

import os
import shutil
from pathlib import Path

import pytest

# Import the function from the project module
from code.create_code_dir import create_and_verify_code_dir

@pytest.fixture
def clean_code_dir(tmp_path):
    """
    Ensure a fresh project layout for the test.
    The fixture creates a temporary directory that mimics the repository
    root, copies the `code/create_code_dir.py` into it, and adjusts
    `__file__` resolution by temporarily changing the working directory.
    """
    # Save original cwd
    original_cwd = Path.cwd()
    try:
        # Switch to the temporary directory which will act as the project root
        os.chdir(tmp_path)

        # Re‑create the expected directory structure (except `code/` which we test)
        (tmp_path / "tests").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "results").mkdir()
        
        # Run the function – it should create `code/` under the temporary root
        yield tmp_path
    finally:
        os.chdir(original_cwd)

def test_create_code_dir_idempotent(clean_code_dir):
    # First run – should create the directory
    create_and_verify_code_dir()
    code_path = clean_code_dir / "code"
    assert code_path.is_dir()
    assert os.access(str(code_path), os.W_OK)

    # Capture the modification time to ensure the second run does not delete/recreate
    mtime_before = code_path.stat().st_mtime

    # Second run – must be idempotent and leave the directory unchanged
    create_and_verify_code_dir()
    assert code_path.is_dir()
    assert os.access(str(code_path), os.W_OK)
    mtime_after = code_path.stat().st_mtime
    assert mtime_before == mtime_after, "Directory was recreated on second call"

def test_verify_config_script_runs_successfully(tmp_path, monkeypatch):
    """
    Execute the `code/verify_config.py` script and ensure it exits with code 0.
    The test creates the required directories, writes a minimal `config.yaml`,
    and then runs the script via a subprocess.
    """
    import subprocess

    # Set up required directories
    for d in ["code", "tests", "data/raw", "data/processed", "results"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # Write a minimal config.yaml matching the fixture
    config_content = """
    paths:
      code: "code"
      tests: "tests"
      data_raw: "data/raw"
      data_processed: "data/processed"
      results: "results"
    """
    (tmp_path / "code" / "config.yaml").write_text(config_content)

    # Ensure the script can be imported as a module (add tmp_path to PYTHONPATH)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")

    script_path = tmp_path / "code" / "verify_config.py"
    # Copy the script from the repository into the temporary location
    shutil.copy2(Path(__file__).parents[1] / "code" / "verify_config.py", script_path)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
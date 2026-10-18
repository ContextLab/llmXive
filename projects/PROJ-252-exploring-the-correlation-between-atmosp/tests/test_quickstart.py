"""
Test that the quick‑start command runs successfully, installs the exact
pinned dependencies, executes the seed‑initialisation script, and creates
the expected log file containing the line “Seeds set to 42”.
"""
import subprocess
import sys
from pathlib import Path


def test_quickstart_runs_successfully():
    """
    Executes the three commands that compose the quick‑start instruction:
    1. ``pip install -r requirements.txt``
    2. ``python -m code.seed_init``
    3. ``python -m code.main``

    Verifies:
    - Each command exits with return code 0.
    - The seed‑initialisation log file exists.
    - The log file contains the exact line “Seeds set to 42”.
    """
    # 1. Install frozen dependencies
    install_cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    result_install = subprocess.run(
        install_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result_install.returncode == 0, (
        f"Pip install failed with code {result_install.returncode}\\n"
        f"stdout: {result_install.stdout}\\nstderr: {result_install.stderr}"
    )

    # 2. Run seed initialisation
    seed_cmd = [sys.executable, "-m", "code.seed_init"]
    result_seed = subprocess.run(
        seed_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result_seed.returncode == 0, (
        f"Seed initialisation failed with code {result_seed.returncode}\\n"
        f"stdout: {result_seed.stdout}\\nstderr: {result_seed.stderr}"
    )

    # 3. Run main placeholder script
    main_cmd = [sys.executable, "-m", "code.main"]
    result_main = subprocess.run(
        main_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result_main.returncode == 0, (
        f"Main script failed with code {result_main.returncode}\\n"
        f"stdout: {result_main.stdout}\\nstderr: {result_main.stderr}"
    )

    # 4. Verify the log file was created and contains the correct line
    log_path = Path("logs/seed_initialization.log")
    assert log_path.is_file(), f"Log file not found at {log_path}"
    log_content = log_path.read_text(encoding="utf-8")
    assert "Seeds set to 42" in log_content, (
        f"Expected line not found in log file. Content was:\\n{log_content}"
    )
import subprocess
import sys
import os

def test_quickstart_sample_run():
    """
    Executes the quickstart sample command and verifies it completes
    within the time budget and prints the expected confirmation string.
    """
    # Ensure the repository root is in the PYTHONPATH
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")

    # Run the command as a subprocess
    result = subprocess.run(
        [sys.executable, "-m", "code.main", "--run-sample"],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )

    # Verify exit code
    assert result.returncode == 0, f"Non-zero exit code: {result.returncode}\\nStderr: {result.stderr}"

    # Verify expected output
    expected_output = "Sample run completed"
    assert expected_output in result.stdout, f"Expected output not found. Got: {result.stdout}"

if __name__ == "__main__":
    # Allow the test to be run directly
    test_quickstart_sample_run()
    print("Quickstart sample run test passed.")
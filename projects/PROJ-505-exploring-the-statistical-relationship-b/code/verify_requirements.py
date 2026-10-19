"""
Verify that all pinned requirements can be installed without error.
Runs `pip install -r requirements.txt` and writes a log file.
"""
import subprocess
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    req_file = paths.root / "requirements.txt"
    result = subprocess.run(
        ["pip", "install", "-r", str(req_file)],
        capture_output=True,
        text=True,
    )
    log_path = paths.results("requirements_install.log")
    with open(log_path, "w", encoding="utf-8") as f:
        if result.returncode == 0:
            f.write("success\n")
        else:
            f.write("failure\n")
        f.write(result.stdout)
        f.write(result.stderr)
        f.write(f"returncode={result.returncode}\\n")
    if result.returncode != 0:
        raise RuntimeError(f"pip install failed with code {result.returncode}")

if __name__ == "__main__":
    main()

"""
Utility script to execute the contract test suite and capture both the
JUnit XML report and a combined stdout/stderr log. The quickstart
verification step expects the files:
  outputs/test_logs/contract.xml
  outputs/test_logs/contract.log
"""
import subprocess
import sys
from pathlib import Path

def main() -> None:
    out_dir = Path("outputs") / "test_logs"
    out_dir.mkdir(parents=True, exist_ok=True)

    xml_path = out_dir / "contract.xml"
    log_path = out_dir / "contract.log"

    cmd = [
        "pytest",
        "tests/contract/",
        "-q",
        f"--junitxml={xml_path}",
    ]

    # Run pytest, capturing stdout and stderr into the log file.
    with log_path.open("w", encoding="utf-8") as log_file:
        result = subprocess.run(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

    # Propagate the exit code so the runner can see success/failure.
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
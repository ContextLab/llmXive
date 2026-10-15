# This thin wrapper simply invokes the download script with the arguments
# required by the quickstart for the layout corpus. It exists so the CI
# runner can execute the download as a separate artifact.
import subprocess
import sys
from pathlib import Path

def main():
    cmd = [
        sys.executable,
        "-m",
        "src.data.download",
        "--dataset-name",
        "layout_corpus",
        "--output-dir",
        str(Path("data/raw")),
    ]
    result = subprocess.run(cmd, check=True)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
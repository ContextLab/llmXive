"""
Create the project directory skeleton, add empty __init__.py files,
compile the code package, and generate a structure report.
"""
import subprocess
import sys
from pathlib import Path

def main() -> None:
    # ------------------------------------------------------------------
    # 1. Define the directory tree required by the project
    # ------------------------------------------------------------------
    dirs = [
        Path("code"),
        Path("code/data"),
        Path("code/models"),
        Path("code/evaluation"),
        Path("code/utils"),
        Path("tests"),
        Path("data/raw"),
        Path("data/processed"),
        Path("data/external"),
        Path("results"),
        Path("logs"),
        Path("specs/001-predict-molecular-properties"),
    ]

    # Create each directory (including parents) if it does not exist
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 2. Add empty __init__.py files to every Python package directory
    # ------------------------------------------------------------------
    package_dirs = [
        Path("code"),
        Path("code/data"),
        Path("code/models"),
        Path("code/evaluation"),
        Path("code/utils"),
        Path("tests"),
        Path("specs/001-predict-molecular-properties"),
    ]

    for pkg in package_dirs:
        init_file = pkg / "__init__.py"
        init_file.touch(exist_ok=True)

    # ------------------------------------------------------------------
    # 3. Verify that the source tree compiles without syntax errors
    # ------------------------------------------------------------------
    compile_cmd = [sys.executable, "-m", "compileall", "code"]
    compile_res = subprocess.run(
        compile_cmd,
        capture_output=True,
        text=True,
    )
    if compile_res.returncode != 0:
        sys.stderr.write("compileall failed:\\n")
        sys.stderr.write(compile_res.stdout)
        sys.stderr.write(compile_res.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Produce a sorted list of all directories in the repository
    # ------------------------------------------------------------------
    find_cmd = ["find", ".", "-type", "d"]
    find_res = subprocess.run(
        find_cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    dir_lines = sorted(
        line.strip()
        for line in find_res.stdout.splitlines()
        if line.strip()
    )
    report_path = Path("results") / "structure_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(dir_lines) + "\n")

if __name__ == "__main__":
    main()

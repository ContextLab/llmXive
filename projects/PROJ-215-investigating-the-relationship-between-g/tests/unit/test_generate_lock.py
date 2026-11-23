import subprocess
import sys
from pathlib import Path

def test_generate_lock_creates_file(tmp_path):
    """
    Execute the generate_lock script and verify that a requirements.lock
    file is created with entries matching the packages listed in
    requirements.txt (ignoring comments and blanks).
    """
    # Resolve script location relative to the project root
    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "code" / "scripts" / "generate_lock.py"
    lock_path = project_root / "requirements.lock"
    req_path = project_root / "requirements.txt"

    # Ensure any previous lock file is removed
    if lock_path.is_file():
        lock_path.unlink()

    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"

    # Verify lock file exists
    assert lock_path.is_file(), "requirements.lock was not created"

    # Load requirement package names (ignore comments/blank lines)
    req_packages = []
    with req_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip version specifiers and extras as in the script
            line = line.split(";", 1)[0].strip()
            for sep in ["==", ">=", "<=", "~=", ">", "<"]:
                if sep in line:
                    line = line.split(sep, 1)[0]
                    break
            if "[" in line:
                line = line.split("[", 1)[0]
            req_packages.append(line.lower())

    # Load lock file entries
    lock_entries = []
    with lock_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pkg, ver = line.split("==")
            lock_entries.append(pkg.lower())

    # The lock file should contain exactly the same packages (order may differ)
    assert set(req_packages) == set(lock_entries), "Mismatch between requirements.txt and requirements.lock"
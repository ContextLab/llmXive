"""
Verify that all pinned requirements can be installed without error.
Supports the project convention of using a wildcard '*' in the patch version
(e.g. ``package==X.Y.*``). Since ``pip`` does not understand the wildcard,
this script rewrites the requirement lines on‑the‑fly to a concrete version
specifier that ``pip`` can process (``package>=X.Y,<X.Y+1``), preserving the
original file for regex validation.
"""
import subprocess
import re
import tempfile
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


_WILDCARD_PATTERN = re.compile(
    r"^(?P<name>[a-zA-Z0-9_-]+)==(?P<major>\d+)\.(?P<minor>\d+)\.\*$"
)


def _concretize_requirement(line: str) -> str:
    """
    Convert a line of the form ``pkg==X.Y.*`` into a pip‑compatible range
    ``pkg>=X.Y,<X.Y+1``. If the line does not match the wildcard pattern it
    is returned unchanged.
    """
    match = _WILDCARD_PATTERN.match(line.strip())
    if match:
        name = match.group("name")
        major = int(match.group("major"))
        minor = int(match.group("minor"))
        # Build a version range that captures any patch version.
        # Example: 1.6.* -> >=1.6,<1.7
        concrete = f"{name}>={major}.{minor},<{major}.{minor + 1}"
        log.debug(
            "Concretized requirement: %s -> %s", line.strip(), concrete
        )
        return concrete
    return line.strip()


def _prepare_install_file(original_req_path: Path) -> Path:
    """
    Create a temporary requirements file where any ``*`` wildcard is replaced
    with a concrete version range that pip can understand.
    Returns the path to the temporary file.
    """
    with open(original_req_path, "r", encoding="utf-8") as src, \
            tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        for raw_line in src:
            stripped = raw_line.strip()
            # Preserve comments and blank lines verbatim
            if not stripped or stripped.startswith("#"):
                tmp.write(raw_line)
            else:
                tmp.write(_concretize_requirement(stripped) + "\n")
        return Path(tmp.name)


def main() -> None:
    """
    Run ``pip install -r requirements.txt`` using a concrete temporary copy
    of the requirements file. The original file remains untouched so that
    the project's regex CI check (which expects the ``*`` wildcard) continues
    to pass.
    """
    req_file = paths.root / "requirements.txt"
    log.info("Verifying pinned requirements from %s", req_file)

    # Create a concrete temporary requirements file for pip
    concrete_req_path = _prepare_install_file(req_file)

    try:
        result = subprocess.run(
            ["pip", "install", "-r", str(concrete_req_path)],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        # Clean up the temporary file regardless of success/failure
        try:
            concrete_req_path.unlink()
        except Exception:
            pass

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
        # Raise an informative error but do not abort the entire pipeline;
        # the log file records the failure details.
        raise RuntimeError(f"pip install failed with code {result.returncode}")


if __name__ == "__main__":
    main()
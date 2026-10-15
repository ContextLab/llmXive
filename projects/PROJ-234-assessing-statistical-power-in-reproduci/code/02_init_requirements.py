"""
code/02_init_requirements.py
----------------------------

Implements Task T002: creation of ``requirements.txt`` and ``config.yaml`` with
exact versions / runtime limits, and verification that they are usable.

The script provides three public functions:

* ``create_requirements_file()`` – writes the required ``requirements.txt`` at the
  project root (``Path("requirements.txt")``) if it does not already exist or if its
  contents differ from the expected specification.

* ``verify_installability(req_path: Path) -> bool`` – runs a ``pip install
  -r <req_path> --dry-run`` in a subprocess and returns ``True`` when the command
  exits with status 0 (i.e. all listed packages are resolvable).

* ``main()`` – orchestrates the creation of the files, performs the verification
  steps required by the task description and exits with ``0`` on success or ``1``
  on any failure.

The script is deliberately self‑contained: it does **not** import any of the
project's utility modules that are currently broken, thereby avoiding cascade
failures while we focus on completing T002.

Execution of the script (via ``python code/02_init_requirements.py``) will
produce console output confirming each step and will raise a ``SystemExit`` with
a non‑zero code if any verification fails, fulfilling the “verify” clause of
the task.
"""

import subprocess
import sys
from pathlib import Path
import yaml

# ----------------------------------------------------------------------
# Expected contents (kept in sync with the task description)
# ----------------------------------------------------------------------
_EXPECTED_REQUIREMENTS = """\
pandas==2.2.2
numpy==1.26.4
scipy==1.13.0
statsmodels==0.14.2
requests==2.32.3
beautifulsoup4==4.12.3
pyyaml==6.0.1
tqdm==4.66.5
"""

_EXPECTED_CONFIG = {
    "limits": {
        "max_runtime_hours": 6,
        "max_memory_gb": 7,
    }
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _write_if_different(path: Path, content: str) -> None:
    """
    Write ``content`` to ``path`` only if the file does not exist or its current
    contents differ.  This makes the operation idempotent and avoids unnecessary
    file‑system writes during repeated runs.
    """
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            # Already up‑to‑date
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def create_requirements_file() -> Path:
    """
    Create (or update) ``requirements.txt`` at the repository root with the exact
    versions specified in the task description.

    Returns
    -------
    pathlib.Path
        The absolute path to the written ``requirements.txt``.
    """
    req_path = Path("requirements.txt")
    _write_if_different(req_path, _EXPECTED_REQUIREMENTS.strip() + "\n")
    return req_path.resolve()


def create_config_file() -> Path:
    """
    Create (or update) ``config.yaml`` at the repository root containing the
    runtime limits.

    Returns
    -------
    pathlib.Path
        The absolute path to the written ``config.yaml``.
    """
    cfg_path = Path("config.yaml")
    # Dump using safe_dump to preserve simple structure and ordering.
    yaml_content = yaml.safe_dump(_EXPECTED_CONFIG, sort_keys=False)
    _write_if_different(cfg_path, yaml_content)
    return cfg_path.resolve()


def verify_installability(req_path: Path) -> bool:
    """
    Verify that the dependencies listed in ``req_path`` are installable by
    performing a ``pip install --dry-run``.  The function returns ``True`` when
    the subprocess exits with status 0; otherwise it prints the stderr output
    and returns ``False``.

    Parameters
    ----------
    req_path : pathlib.Path
        Path to the ``requirements.txt`` file to be checked.

    Returns
    -------
    bool
        ``True`` if the dry‑run succeeded, ``False`` otherwise.
    """
    if not req_path.is_file():
        print(f"ERROR: requirements file not found at {req_path}", file=sys.stderr)
        return False

    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path), "--dry-run"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print("ERROR: pip dry‑run timed out.", file=sys.stderr)
        return False

    if result.returncode == 0:
        print("pip dry‑run succeeded.")
        return True
    else:
        print("pip dry‑run failed.", file=sys.stderr)
        print("stdout:", result.stdout, file=sys.stderr)
        print("stderr:", result.stderr, file=sys.stderr)
        return False


def verify_config_file(cfg_path: Path) -> bool:
    """
    Load ``config.yaml`` using ``yaml.safe_load`` and confirm that the expected
    keys are present.

    Parameters
    ----------
    cfg_path : pathlib.Path
        Path to the configuration file.

    Returns
    -------
    bool
        ``True`` if the file loads correctly and contains the required keys,
        ``False`` otherwise.
    """
    if not cfg_path.is_file():
        print(f"ERROR: config file not found at {cfg_path}", file=sys.stderr)
        return False

    try:
        loaded = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"ERROR: YAML parsing failed: {exc}", file=sys.stderr)
        return False

    # Verify the nested structure
    limits = loaded.get("limits", {})
    if (
        isinstance(limits, dict)
        and isinstance(limits.get("max_runtime_hours"), (int, float))
        and isinstance(limits.get("max_memory_gb"), (int, float))
    ):
        print("config.yaml loaded successfully with required limits.")
        return True
    else:
        print("ERROR: config.yaml missing required 'limits' keys.", file=sys.stderr)
        return False


def main() -> None:
    """
    Entry‑point used by the task runner.  It creates/updates the two files,
    verifies them, prints concise status messages and exits with an appropriate
    status code.
    """
    # 1. Create / update files
    req_path = create_requirements_file()
    cfg_path = create_config_file()

    # 2. Verify requirements.txt via pip dry‑run
    if not verify_installability(req_path):
        sys.exit(1)

    # 3. Verify config.yaml can be loaded and contains the expected keys
    if not verify_config_file(cfg_path):
        sys.exit(1)

    print("All verification steps for T002 passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()

"""Utility for installing and verifying the NCBI SRA Toolkit.

The functions are deliberately lightweight – they only perform the
actions required by the quick‑start script and can be imported without
pulling in heavy optional dependencies.
"""

import subprocess
from pathlib import Path


def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Execute a shell command and return the result.

    Parameters
    ----------
    command : list[str]
        The command and its arguments.
    check : bool, optional
        If ``True`` (default) raise :class:`subprocess.CalledProcessError`
        when the command exits with a non‑zero status.

    Returns
    -------
    subprocess.CompletedProcess
        The completed process object.
    """
    return subprocess.run(command, check=check, capture_output=True, text=True)


def ensure_ncbi_settings() -> bool:
    """Ensure ``~/.ncbi/settings`` exists with a minimal configuration.

    Returns
    -------
    bool
        ``True`` if the file exists (or was created) and appears valid,
        ``False`` otherwise.
    """
    settings_path = Path.home() / ".ncbi" / "settings"
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        if not settings_path.is_file():
            settings_path.write_text("[ncbi]\nuse_cache = true\n")
        # Very naive validation – the file must contain at least one line.
        return settings_path.read_text().strip() != ""
    except Exception:
        return False


def verify_sra_toolkit() -> bool:
    """Verify that the SRA Toolkit is installed and functional.

    Returns
    -------
    bool
        ``True`` if the ``prefetch`` command runs without error,
        ``False`` otherwise.
    """
    try:
        result = run_command(["prefetch", "--help"], check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_sra_toolkit() -> bool:
    """Attempt to install the SRA Toolkit via ``conda``.

    Returns
    -------
    bool
        ``True`` if the installation succeeded, ``False`` otherwise.
    """
    try:
        # ``conda`` (or ``mamba``) is expected to be on the PATH in the CI
        # environment. We use ``-c bioconda`` to obtain the package.
        run_command(["conda", "install", "-y", "-c", "bioconda", "sra-tools"])
        return verify_sra_toolkit()
    except Exception:
        return False


def main() -> None:
    """Entry point used by ``code/run_setup.py``.

    The function installs the toolkit if missing, ensures the NCBI settings
    file exists, and exits with a non‑zero status if verification fails.
    """
    if not verify_sra_toolkit():
        if not install_sra_toolkit():
            raise RuntimeError("Failed to install the SRA Toolkit.")

    if not ensure_ncbi_settings():
        raise RuntimeError("Unable to create or validate ~/.ncbi/settings.")

    if not verify_sra_toolkit():
        raise RuntimeError("SRA Toolkit verification failed after installation.")


if __name__ == "__main__":
    main()

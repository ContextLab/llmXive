"""
Utility module for running linting and formatting tools programmatically.
Provides functions to invoke flake8, black, and isort from Python scripts.
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional, List


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.

    Args:
        cmd: Command and arguments as a list.
        cwd: Working directory for the command.
        capture_output: Whether to capture stdout/stderr.
        check: Whether to raise CalledProcessError on non-zero exit.

    Returns:
        CompletedProcess instance with return code, stdout, and stderr.

    Raises:
        subprocess.CalledProcessError: If check=True and command fails.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Command failed with return code {e.returncode}")
            if e.stdout:
                print(f"STDOUT:\n{e.stdout}")
            if e.stderr:
                print(f"STDERR:\n{e.stderr}")
        raise


def run_lint(
    paths: Optional[List[str]] = None,
    project_root: Optional[Path] = None,
) -> Tuple[int, str, str]:
    """
    Run flake8 linting on specified paths.

    Args:
        paths: List of paths to lint. Defaults to code/, utils/, tests/.
        project_root: Project root directory. Defaults to current working directory.

    Returns:
        Tuple of (exit_code, stdout, stderr).

    Raises:
        FileNotFoundError: If flake8 is not installed.
    """
    if project_root is None:
        project_root = Path.cwd()

    if paths is None:
        paths = ["code", "utils", "tests"]

    # Check if flake8 is available
    try:
        run_command([sys.executable, "-m", "flake8", "--version"], cwd=project_root)
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise FileNotFoundError(
            "flake8 is not installed. Run: pip install flake8"
        )

    cmd = [sys.executable, "-m", "flake8"] + paths
    try:
        result = run_command(cmd, cwd=project_root, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def run_format(
    paths: Optional[List[str]] = None,
    project_root: Optional[Path] = None,
    check_only: bool = False,
) -> Tuple[int, str, str]:
    """
    Run black and isort formatting on specified paths.

    Args:
        paths: List of paths to format. Defaults to code/, utils/, tests/.
        project_root: Project root directory. Defaults to current working directory.
        check_only: If True, only check formatting without modifying files.

    Returns:
        Tuple of (exit_code, stdout, stderr).

    Raises:
        FileNotFoundError: If black or isort is not installed.
    """
    if project_root is None:
        project_root = Path.cwd()

    if paths is None:
        paths = ["code", "utils", "tests"]

    # Check if black is available
    try:
        run_command([sys.executable, "-m", "black", "--version"], cwd=project_root)
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise FileNotFoundError(
            "black is not installed. Run: pip install black"
        )

    # Check if isort is available
    try:
        run_command([sys.executable, "-m", "isort", "--version"], cwd=project_root)
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise FileNotFoundError(
            "isort is not installed. Run: pip install isort"
        )

    results = []

    # Run isort first
    isort_cmd = [sys.executable, "-m", "isort"]
    if check_only:
        isort_cmd.append("--check-only")
    isort_cmd.extend(paths)

    try:
        isort_result = run_command(isort_cmd, cwd=project_root, check=False)
        results.append(("isort", isort_result.returncode, isort_result.stdout, isort_result.stderr))
    except Exception as e:
        results.append(("isort", -1, "", str(e)))

    # Run black
    black_cmd = [sys.executable, "-m", "black"]
    if check_only:
        black_cmd.append("--check")
    black_cmd.extend(paths)

    try:
        black_result = run_command(black_cmd, cwd=project_root, check=False)
        results.append(("black", black_result.returncode, black_result.stdout, black_result.stderr))
    except Exception as e:
        results.append(("black", -1, "", str(e)))

    # Aggregate results
    total_exit = 0
    stdout_parts = []
    stderr_parts = []

    for tool, exit_code, out, err in results:
        if exit_code != 0:
            total_exit = 1
        stdout_parts.append(f"=== {tool} STDOUT ===\n{out}")
        stderr_parts.append(f"=== {tool} STDERR ===\n{err}")

    return (
        total_exit,
        "\n".join(stdout_parts),
        "\n".join(stderr_parts),
    )


def main():
    """
    Main entry point for running linting and formatting tools from the command line.
    Usage: python -m utils.linting_setup [lint|format|format-check]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run linting and formatting tools for the project."
    )
    parser.add_argument(
        "action",
        choices=["lint", "format", "format-check"],
        help="Action to perform: lint, format, or format-check",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=None,
        help="Paths to process (default: code utils tests)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (default: current directory)",
    )

    args = parser.parse_args()

    project_root = args.project_root or Path.cwd()

    print(f"Running {args.action} on paths: {args.paths or ['code', 'utils', 'tests']}")
    print(f"Project root: {project_root}")
    print("-" * 60)

    if args.action == "lint":
        exit_code, stdout, stderr = run_lint(
            paths=args.paths, project_root=project_root
        )
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

    elif args.action == "format":
        exit_code, stdout, stderr = run_format(
            paths=args.paths, project_root=project_root, check_only=False
        )
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

    elif args.action == "format-check":
        exit_code, stdout, stderr = run_format(
            paths=args.paths, project_root=project_root, check_only=True
        )
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

    if exit_code == 0:
        print("-" * 60)
        print(f"✓ {args.action.capitalize()} completed successfully!")
    else:
        print("-" * 60)
        print(f"✗ {args.action.capitalize()} failed with exit code {exit_code}")
        if args.action == "format-check":
            print("Run 'python -m utils.linting_setup format' to auto-fix formatting issues.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
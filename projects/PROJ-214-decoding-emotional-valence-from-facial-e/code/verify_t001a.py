"""T001a: Ensure `code/` and `tests/` directories exist at repository root.

Prints a directory listing as evidence that both directories exist.
"""
from pathlib import Path

from llmxive_toolkit import paths

ROOT = paths.root


def list_dir(d: Path) -> None:
    print(f"{d.relative_to(ROOT)}/")
    if not d.exists():
        raise FileNotFoundError(f"Required directory missing: {d}")
    for child in sorted(d.iterdir()):
        marker = "/" if child.is_dir() else ""
        print(f"  {child.name}{marker}")


def main() -> None:
    code_dir = ROOT / "code"
    tests_dir = ROOT / "tests"
    code_dir.mkdir(exist_ok=True)
    tests_dir.mkdir(exist_ok=True)
    # Also ensure nested test packages exist (they are part of the tests/ tree).
    (tests_dir / "unit").mkdir(exist_ok=True)
    (tests_dir / "integration").mkdir(exist_ok=True)

    print(f"Project root: {ROOT}")
    list_dir(code_dir)
    list_dir(tests_dir)
    print("T001a verified: code/ and tests/ exist at repository root.")


if __name__ == "__main__":
    main()
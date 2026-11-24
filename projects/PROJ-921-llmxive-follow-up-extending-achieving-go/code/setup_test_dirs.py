"""Create the tests/ directory structure for the llmXive follow-up project.

Creates tests/, tests/unit/, and tests/integration/ along with the
__init__.py files that make them importable packages, then prints a
filesystem listing as evidence that the structure exists.
"""
from pathlib import Path

from llmxive_toolkit import paths


def setup_test_directories() -> list[Path]:
    """Create tests/ and its required subdirectories.

    Returns the list of created/verified directory paths.
    """
    dirs = [
        paths.root / "tests",
        paths.root / "tests" / "unit",
        paths.root / "tests" / "integration",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    # Make the test directories importable packages.
    for d in dirs:
        init = d / "__init__.py"
        if not init.exists():
            init.write_text(
                '"""llmXive follow-up test package."""\n',
                encoding="utf-8",
            )
    return dirs


def main() -> None:
    created = setup_test_directories()
    print("Verified/created test directories:")
    for d in created:
        print(f"  {d} -> exists={d.is_dir()}")
    tests_root = paths.root / "tests"
    print("\nFilesystem listing of tests/:")
    for p in sorted(tests_root.rglob("*")):
        kind = "DIR " if p.is_dir() else "FILE"
        print(f"  [{kind}] {p.relative_to(paths.root)}")


if __name__ == "__main__":
    main()
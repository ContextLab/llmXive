"""
Unit test for the project‑structure creation script.

The test invokes the ``main`` function from ``setup_project_structure`` and
then asserts that all required directories and the ``checksums.json`` file
exist.
"""

from pathlib import Path

def test_create_project_structure():
    # Import and run the creation script
    from setup_project_structure import main as create_structure

    # Execute the script – it should be idempotent
    create_structure()

    # Resolve the project root (two levels up from this test file)
    project_root = Path(__file__).resolve().parents[2]

    # Expected paths
    expected_paths = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "logs",
        project_root / "data" / "artifacts",
        project_root / "data" / "checksums.json",
    ]

    for p in expected_paths:
        assert p.exists(), f"Expected path {p} to exist"
    # Additional sanity check: checksums.json should contain valid JSON
    if (project_root / "data" / "checksums.json").is_file():
        try:
            import json

            with open(project_root / "data" / "checksums.json", "r") as f:
                json.load(f)
        except Exception as exc:
            raise AssertionError(
                "checksums.json is not valid JSON"
            ) from exc
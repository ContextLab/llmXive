from pathlib import Path

def test_dir_structure_manifest():
    """
    Verifies that data/dir_structure.txt exists, contains the 
    nine expected directories, and that those directories 
    actually exist on the filesystem.
    """
    manifest_path = Path("data/dir_structure.txt")
    assert manifest_path.exists(), "Manifest file data/dir_structure.txt is missing"

    expected_dirs = [
        "code",
        "code/simulation",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/processed/plots",
    ]

    # Read manifest and clean up whitespace/empty lines
    content = manifest_path.read_text().splitlines()
    content = [line.strip() for line in content if line.strip()]

    # Verify each expected directory is in the manifest and exists on disk
    for d in expected_dirs:
        assert d in content, f"Directory '{d}' is missing from the manifest"
        assert Path(d).is_dir(), f"Directory '{d}' defined in manifest does not exist on disk"

    # Verify we have at least the nine required entries
    assert len(content) >= 9, f"Manifest contains only {len(content)} directories, expected at least 9"
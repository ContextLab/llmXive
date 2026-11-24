import pathlib

def test_quickstart_contains_demo_command():
    """
    Verify that the quickstart documentation contains the exact command
    required by the CI check:
    ``python -m code.main --demo``
    """
    quickstart_path = pathlib.Path(__file__).parents[2] / "quickstart.md"
    assert quickstart_path.is_file(), f"quickstart.md not found at {quickstart_path}"
    content = quickstart_path.read_text(encoding="utf-8")
    expected = "python -m code.main --demo"
    assert expected in content, f"quickstart.md must contain the exact string '{expected}'"